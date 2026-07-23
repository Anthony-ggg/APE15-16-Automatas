"""Integración HTTP con Stanford CoreNLP para la APE 16."""

from __future__ import annotations

import json
import re
import time
from typing import Any

import requests

from analyzers.common import (
    corenlp_java_memory_mb,
    is_clause_relation,
    is_object_relation,
    is_subject_relation,
    join_tokens,
)
from services.linguistic_rules import TRANSITIVE_VERBS, is_known_verb, normalize_term, verb_lemma


ANNOTATORS = "tokenize,ssplit,pos,lemma,parse,depparse"


def health(base_url: str, timeout_seconds: int = 3) -> dict[str, Any]:
    try:
        response = requests.get(f"{base_url}/ready", timeout=timeout_seconds)
        return {
            "available": response.ok,
            "url": base_url,
            "status_code": response.status_code,
            "error": None if response.ok else "El servidor respondió, pero todavía no está listo.",
        }
    except requests.RequestException as exc:
        return {
            "available": False,
            "url": base_url,
            "error": f"No se pudo conectar con CoreNLP: {exc}",
        }


def _parse_constituency_tree(tree: str) -> dict[str, Any] | None:
    """Convierte el árbol con paréntesis de CoreNLP en una estructura JSON.

    Ejemplo: ``(ROOT (S (sn María) (grup.verb estudia)))``. La estructura
    resultante permite dibujar nodos y líneas en el front-end sin depender de
    bibliotecas JavaScript externas.
    """
    if not tree or tree.startswith("Árbol no disponible"):
        return None

    tokens = re.findall(r"\(|\)|[^\s()]+", tree)
    position = 0

    def parse_node() -> dict[str, Any]:
        nonlocal position
        if position >= len(tokens):
            raise ValueError("Árbol incompleto")

        if tokens[position] != "(":
            value = tokens[position]
            position += 1
            return {"label": value, "children": [], "terminal": True}

        position += 1  # (
        if position >= len(tokens):
            raise ValueError("Falta la etiqueta del nodo")
        label = tokens[position]
        position += 1
        children: list[dict[str, Any]] = []

        while position < len(tokens) and tokens[position] != ")":
            children.append(parse_node())

        if position >= len(tokens):
            raise ValueError("Falta cerrar un nodo")
        position += 1  # )
        return {"label": label, "children": children, "terminal": False}

    try:
        root = parse_node()
        if position != len(tokens):
            return None
        return root
    except (ValueError, RecursionError):
        return None


def _is_verb(pos: str, word: str = "", lemma: str = "") -> bool:
    normalized = (pos or "").lower()
    return (
        normalized.startswith("v")
        or normalized in {"verb", "aux"}
        or is_known_verb(word, lemma)
    )


def _descendants(
    root_index: int,
    children_map: dict[int, list[int]],
    forbidden_heads: set[int],
) -> list[int]:
    result: list[int] = []
    stack = [root_index]
    visited: set[int] = set()
    while stack:
        current = stack.pop()
        if current in visited:
            continue
        visited.add(current)
        result.append(current)
        for child in children_map.get(current, []):
            if child in forbidden_heads and child != root_index:
                continue
            stack.append(child)
    return sorted(result)


def _phrase(
    token_index: int | None,
    token_map: dict[int, dict],
    children_map: dict[int, list[int]],
    clause_heads: set[int],
) -> str:
    if token_index is None:
        return "No detectado"
    indices = _descendants(token_index, children_map, clause_heads)
    words = [token_map[index].get("originalText", token_map[index]["word"]) for index in indices]
    return join_tokens(words)


def _nearest_clause_head(
    token_index: int,
    governor_map: dict[int, int],
    clause_heads: set[int],
    default_head: int,
) -> int:
    current = token_index
    visited: set[int] = set()
    while current not in visited and current > 0:
        visited.add(current)
        if current in clause_heads:
            return current
        current = governor_map.get(current, 0)
    return default_head


def _sentence_propositions(sentence: dict) -> list[dict]:
    tokens = sentence.get("tokens", [])
    dependencies = sentence.get("basicDependencies", [])
    token_map = {token["index"]: token for token in tokens}
    governor_map = {dep["dependent"]: dep.get("governor", 0) for dep in dependencies}
    children_map: dict[int, list[int]] = {}
    for dep in dependencies:
        children_map.setdefault(dep.get("governor", 0), []).append(dep["dependent"])

    root_dep = next((dep for dep in dependencies if dep["dep"].lower() == "root"), None)
    syntactic_root = root_dep["dependent"] if root_dep else (tokens[0]["index"] if tokens else 1)

    # Si el parser eligió un sustantivo como raíz, se busca una forma verbal
    # reconocible antes de construir las proposiciones.
    root_token = token_map.get(syntactic_root, {})
    if _is_verb(root_token.get("pos", ""), root_token.get("word", ""), root_token.get("lemma", "")):
        default_head = syntactic_root
    else:
        verb_candidates = [
            token["index"]
            for token in tokens
            if _is_verb(token.get("pos", ""), token.get("word", ""), token.get("lemma", ""))
        ]
        default_head = verb_candidates[0] if verb_candidates else syntactic_root

    clause_heads: set[int] = {default_head}
    for dep in dependencies:
        dependent = dep["dependent"]
        token = token_map.get(dependent, {})
        if is_clause_relation(dep["dep"]) and _is_verb(
            token.get("pos", ""), token.get("word", ""), token.get("lemma", "")
        ):
            clause_heads.add(dependent)

    # Respaldo: verbos que poseen sujeto propio.
    for token in tokens:
        index = token["index"]
        if not _is_verb(token.get("pos", ""), token.get("word", ""), token.get("lemma", "")):
            continue
        has_subject = any(
            dep.get("governor") == index and is_subject_relation(dep["dep"])
            for dep in dependencies
        )
        if has_subject:
            clause_heads.add(index)

    assigned: dict[int, list[int]] = {head: [] for head in clause_heads}
    for token in tokens:
        head = _nearest_clause_head(token["index"], governor_map, clause_heads, default_head)
        assigned.setdefault(head, []).append(token["index"])

    propositions: list[dict] = []
    for head in clause_heads:
        indices = sorted(assigned.get(head, [head]))
        subject_dep = next(
            (
                dep
                for dep in dependencies
                if dep.get("governor") == head and is_subject_relation(dep["dep"])
            ),
            None,
        )
        object_dep = next(
            (
                dep
                for dep in dependencies
                if dep.get("governor") == head and is_object_relation(dep["dep"])
            ),
            None,
        )
        head_dep = next((dep for dep in dependencies if dep["dependent"] == head), None)
        words = [token_map[index].get("originalText", token_map[index]["word"]) for index in indices]
        head_token = token_map.get(head, {})
        lemma = verb_lemma(head_token.get("word", ""), head_token.get("lemma", "")) or head_token.get("lemma") or head_token.get("word", "No detectado")

        if subject_dep:
            subject = _phrase(subject_dep["dependent"], token_map, children_map, clause_heads)
            subject_head = token_map.get(subject_dep["dependent"], {}).get("word", "No detectado")
            method_parts = ["dependencias"]
        else:
            before = [index for index in indices if index < head]
            before_words = [token_map[index].get("originalText", token_map[index].get("word", "")) for index in before]
            while before_words and normalize_term(before_words[0]) in {"y", "e", "o", "u", "pero", "aunque", "si", "porque", "mientras"}:
                before_words.pop(0)
                before.pop(0)
            subject = join_tokens(before_words) if before_words else "Sujeto omitido/implícito"
            content = [
                token_map[index].get("word", "")
                for index in before
                if not str(token_map[index].get("pos", "")).lower().startswith(("d", "s", "f"))
            ]
            subject_head = content[0] if content else "No detectado"
            method_parts = ["respaldo léxico para el sujeto"]

        if object_dep:
            obj = _phrase(object_dep["dependent"], token_map, children_map, clause_heads)
            object_head = token_map.get(object_dep["dependent"], {}).get("word", "No detectado")
            method_parts.append("dependencias")
        elif normalize_term(str(lemma)) in TRANSITIVE_VERBS:
            after = [index for index in indices if index > head]
            after_words = [token_map[index].get("originalText", token_map[index].get("word", "")) for index in after]
            obj = join_tokens(after_words) if after_words else "No detectado"
            content = [
                token_map[index].get("word", "")
                for index in after
                if not str(token_map[index].get("pos", "")).lower().startswith(("d", "s", "f"))
            ]
            object_head = content[0] if content else "No detectado"
            if obj != "No detectado":
                method_parts.append("respaldo léxico para el objeto")
        else:
            obj = "No detectado"
            object_head = "No detectado"

        propositions.append(
            {
                "text": join_tokens(words),
                "subject": subject,
                "subject_head": subject_head,
                "verb": head_token.get("word", "No detectado"),
                "verb_lemma": lemma,
                "object": obj,
                "object_head": object_head,
                "dependency": head_dep["dep"] if head_dep else "ROOT",
                "extraction_method": " + ".join(dict.fromkeys(method_parts)),
                "start": min(indices) if indices else head,
            }
        )

    propositions.sort(key=lambda item: item["start"])
    for number, proposition in enumerate(propositions, start=1):
        proposition["number"] = number
        proposition.pop("start", None)
    return propositions


def analizar(text: str, base_url: str, timeout_seconds: int = 45) -> dict[str, Any]:
    properties = {
        "annotators": ANNOTATORS,
        "outputFormat": "json",
        "timeout": str(timeout_seconds * 1000),
    }
    started = time.perf_counter()
    try:
        response = requests.post(
            f"{base_url}/",
            params={"properties": json.dumps(properties, ensure_ascii=False)},
            data=text.encode("utf-8"),
            headers={"Content-Type": "text/plain; charset=utf-8"},
            timeout=timeout_seconds,
        )
        response.raise_for_status()
        data = response.json()
    except requests.ConnectionError:
        return {
            "available": False,
            "error": (
                f"No se pudo conectar a Stanford CoreNLP en {base_url}. "
                "Inicie el servidor con ./scripts/start_corenlp.sh"
            ),
        }
    except requests.Timeout:
        return {
            "available": False,
            "error": "CoreNLP superó el tiempo máximo de espera.",
        }
    except (requests.RequestException, ValueError) as exc:
        return {
            "available": False,
            "error": f"CoreNLP devolvió un error: {exc}",
        }

    elapsed_ms = round((time.perf_counter() - started) * 1000, 2)
    all_tokens: list[dict] = []
    all_dependencies: list[dict] = []
    all_propositions: list[dict] = []
    sentences_result: list[dict] = []
    parse_trees: list[str] = []
    parse_tree_structures: list[dict[str, Any] | None] = []

    global_index = 0
    for sentence_number, sentence in enumerate(data.get("sentences", []), start=1):
        dependencies = sentence.get("basicDependencies", [])
        dependency_by_token = {dep["dependent"]: dep for dep in dependencies}
        sentence_tokens = sentence.get("tokens", [])
        token_map = {token["index"]: token for token in sentence_tokens}

        for token in sentence_tokens:
            dep = dependency_by_token.get(token["index"], {})
            governor_index = dep.get("governor", 0)
            global_index += 1
            all_tokens.append(
                {
                    "index": global_index,
                    "sentence_index": token["index"],
                    "sentence_number": sentence_number,
                    "token": token.get("originalText", token.get("word", "")),
                    "lemma": token.get("lemma", token.get("word", "")),
                    "pos": token.get("pos", ""),
                    "dependency": dep.get("dep", ""),
                    "governor": (
                        "ROOT"
                        if governor_index == 0
                        else token_map.get(governor_index, {}).get("word", str(governor_index))
                    ),
                }
            )

        for dep in dependencies:
            governor_index = dep.get("governor", 0)
            all_dependencies.append(
                {
                    "sentence_number": sentence_number,
                    "relation": dep.get("dep", ""),
                    "governor": (
                        "ROOT"
                        if governor_index == 0
                        else token_map.get(governor_index, {}).get("word", str(governor_index))
                    ),
                    "dependent": token_map.get(dep["dependent"], {}).get(
                        "word", str(dep["dependent"])
                    ),
                }
            )

        propositions = _sentence_propositions(sentence)
        for proposition in propositions:
            proposition["sentence_number"] = sentence_number
        all_propositions.extend(propositions)
        parse_tree = sentence.get("parse", "Árbol no disponible")
        parse_tree_structure = _parse_constituency_tree(parse_tree)
        parse_trees.append(parse_tree)
        parse_tree_structures.append(parse_tree_structure)
        sentences_result.append(
            {
                "number": sentence_number,
                "text": join_tokens(
                    token.get("originalText", token.get("word", ""))
                    for token in sentence_tokens
                ),
                "proposition_count": len(propositions),
                "propositions": propositions,
                "parse_tree": parse_tree,
                "parse_tree_structure": parse_tree_structure,
            }
        )

    first = all_propositions[0] if all_propositions else None
    return {
        "available": True,
        "tool": "Stanford CoreNLP",
        "url": base_url,
        "annotators": ANNOTATORS,
        "time_ms": elapsed_ms,
        "memory_mb": corenlp_java_memory_mb(),
        "tokens": all_tokens,
        "dependencies": all_dependencies,
        "dependencies_count": len(all_dependencies),
        "sentences": sentences_result,
        "proposition_count": len(all_propositions),
        "propositions": all_propositions,
        "svo": {
            "subject": first["subject"] if first else "No detectado",
            "verb": first["verb"] if first else "No detectado",
            "object": first["object"] if first else "No detectado",
        },
        "parse_trees": parse_trees,
        "parse_tree_structures": parse_tree_structures,
    }
