"""Análisis léxico y sintáctico con spaCy para la APE 15.

Incluye un respaldo léxico transparente para formas verbales frecuentes. El
respaldo corrige casos en los que el modelo pequeño etiqueta una palabra como
sustantivo y, por ello, selecciona un núcleo incorrecto; por ejemplo:
«El carro del vecino vuela».
"""

from __future__ import annotations

import time
from typing import Any

from spacy import displacy

from analyzers.common import (
    is_clause_relation,
    is_object_relation,
    is_subject_relation,
    rss_mb,
)
from services.linguistic_rules import (
    TRANSITIVE_VERBS,
    is_known_verb,
    normalize_term,
    verb_lemma,
)

try:
    import spacy
except ImportError:  # pragma: no cover - se informa desde health/analizar
    spacy = None

_NLP = None
_MODEL_ERROR: str | None = None


def _load_model():
    global _NLP, _MODEL_ERROR
    if _NLP is not None or _MODEL_ERROR is not None:
        return _NLP
    if spacy is None:
        _MODEL_ERROR = "La librería spaCy no está instalada."
        return None
    try:
        _NLP = spacy.load("es_core_news_sm")
    except OSError:
        _MODEL_ERROR = (
            "No está instalado el modelo es_core_news_sm. Ejecute: "
            "python -m spacy download es_core_news_sm"
        )
    return _NLP


def health() -> dict[str, Any]:
    nlp = _load_model()
    return {
        "available": nlp is not None,
        "model": "es_core_news_sm",
        "error": _MODEL_ERROR,
    }


def _phrase(token, clause_head_ids: set[int]) -> str:
    indices = [
        item.i
        for item in token.subtree
        if item.i == token.i or item.i not in clause_head_ids
    ]
    if not indices:
        return token.text
    start, end = min(indices), max(indices)
    return token.doc[start : end + 1].text


def _nearest_clause_head(token, clause_head_ids: set[int], default_head: int) -> int:
    current = token
    visited: set[int] = set()
    while current.i not in visited:
        visited.add(current.i)
        if current.i in clause_head_ids:
            return current.i
        if current.head.i == current.i:
            break
        current = current.head
    return default_head


def _has_finite_morph(token) -> bool:
    try:
        return "Fin" in token.morph.get("VerbForm") or "Inf" in token.morph.get("VerbForm")
    except (AttributeError, KeyError):
        return False


def _looks_nominal_despite_lexicon(token) -> bool:
    """Reduce falsos positivos en formas ambiguas como «la cocina»."""
    if token.pos_ not in {"NOUN", "PROPN"}:
        return False
    return any(child.dep_.lower().split(":", 1)[0] == "det" for child in token.children)


def _token_is_verb(token) -> bool:
    if token.pos_ in {"VERB", "AUX"} or _has_finite_morph(token):
        return True
    if _looks_nominal_despite_lexicon(token):
        return False
    return is_known_verb(token.text, token.lemma_)


def _verb_score(token, sentence) -> int:
    score = 0
    if token.pos_ in {"VERB", "AUX"}:
        score += 8
    if _has_finite_morph(token):
        score += 6
    if is_known_verb(token.text, token.lemma_):
        score += 5
    if token.dep_ == "ROOT":
        score += 10
    if is_clause_relation(token.dep_):
        score += 4
    if any(is_subject_relation(child.dep_) for child in token.children):
        score += 3
    # En español declarativo, un verbo después del primer grupo nominal es un
    # candidato más plausible que una forma ambigua al inicio.
    if token.i > sentence.start:
        score += 1
    return score


def _verb_tokens(sentence) -> list:
    return [token for token in sentence if _token_is_verb(token)]


def _main_verb(sentence, candidates: list):
    if not candidates:
        return sentence.root
    return max(candidates, key=lambda token: (_verb_score(token, sentence), -token.i))


def _strip_span_tokens(tokens: list, *, strip_leading_connectors: bool = True) -> list:
    result = [token for token in tokens if not token.is_punct]
    if strip_leading_connectors:
        while result and (
            result[0].pos_ in {"CCONJ", "SCONJ"}
            or normalize_term(result[0].text) in {"y", "e", "o", "u", "pero", "aunque", "si", "porque", "mientras"}
        ):
            result.pop(0)
    return result


def _fallback_subject(head, token_indices: list[int]) -> tuple[str, str]:
    before = [head.doc[index] for index in token_indices if index < head.i]
    before = _strip_span_tokens(before)
    if not before:
        return "Sujeto omitido/implícito", "No detectado"

    # Se conserva el grupo nominal completo anterior al verbo. Si existe un
    # conector interno, se usa el segmento posterior al último conector.
    boundary = -1
    for index, token in enumerate(before):
        if token.pos_ in {"CCONJ", "SCONJ"} or normalize_term(token.text) in {"y", "e", "o", "u", "pero"}:
            boundary = index
    phrase_tokens = before[boundary + 1 :]
    if not phrase_tokens:
        return "Sujeto omitido/implícito", "No detectado"

    noun_tokens = [token for token in phrase_tokens if token.pos_ in {"NOUN", "PROPN", "PRON"}]
    if not noun_tokens:
        # Cuando el etiquetador falla, la segunda palabra de «El carro...»
        # sigue siendo un mejor núcleo que declarar al sustantivo como verbo.
        content = [token for token in phrase_tokens if token.pos_ not in {"DET", "ADP"}]
        if not content:
            return "Sujeto omitido/implícito", "No detectado"
        noun_tokens = [content[0]]

    start = phrase_tokens[0].i
    end = phrase_tokens[-1].i + 1
    return head.doc[start:end].text.strip(), noun_tokens[0].text


def _fallback_object(head, token_indices: list[int], lemma: str | None) -> tuple[str, str]:
    if lemma not in TRANSITIVE_VERBS:
        return "No detectado", "No detectado"
    after = [head.doc[index] for index in token_indices if index > head.i]
    after = _strip_span_tokens(after)
    if not after:
        return "No detectado", "No detectado"

    # Se detiene ante un nuevo conector para no tomar otra proposición como
    # objeto directo.
    usable: list = []
    for token in after:
        if token.pos_ in {"CCONJ", "SCONJ"} or normalize_term(token.text) in {
            "y", "e", "o", "u", "pero", "porque", "aunque", "mientras", "si"
        }:
            break
        usable.append(token)
    if not usable:
        return "No detectado", "No detectado"

    noun_tokens = [token for token in usable if token.pos_ in {"NOUN", "PROPN", "PRON"}]
    if not noun_tokens:
        content = [token for token in usable if token.pos_ not in {"DET", "ADP", "ADV"}]
        if not content:
            return "No detectado", "No detectado"
        noun_tokens = [content[-1]]

    start = usable[0].i
    end = usable[-1].i + 1
    return head.doc[start:end].text.strip(), noun_tokens[0].text


def _sentence_propositions(sentence) -> list[dict]:
    verb_tokens = _verb_tokens(sentence)
    main_head = _main_verb(sentence, verb_tokens)

    clause_heads = [main_head]
    for token in verb_tokens:
        if token.i == main_head.i:
            continue
        has_subject = any(is_subject_relation(child.dep_) for child in token.children)
        if is_clause_relation(token.dep_) or has_subject:
            clause_heads.append(token)

    # Elimina duplicados y ordena para que la asignación sea estable.
    clause_heads = list({token.i: token for token in clause_heads}.values())
    clause_heads.sort(key=lambda token: token.i)

    clause_head_ids = {token.i for token in clause_heads}
    default_head = main_head.i
    assigned: dict[int, list[int]] = {head.i: [] for head in clause_heads}

    for token in sentence:
        head_id = _nearest_clause_head(token, clause_head_ids, default_head)
        assigned.setdefault(head_id, []).append(token.i)

    propositions: list[dict] = []
    for head in clause_heads:
        token_indices = sorted(assigned.get(head.i, [head.i]))
        subject_token = next(
            (child for child in head.children if is_subject_relation(child.dep_)), None
        )
        if subject_token is None:
            subject_token = next(
                (
                    sentence.doc[index]
                    for index in token_indices
                    if is_subject_relation(sentence.doc[index].dep_)
                    and sentence.doc[index].head.i == head.i
                ),
                None,
            )
        object_token = next(
            (child for child in head.children if is_object_relation(child.dep_)), None
        )

        method_parts: list[str] = []
        if subject_token:
            subject = _phrase(subject_token, clause_head_ids)
            subject_head = subject_token.text
            method_parts.append("dependencias")
        else:
            subject, subject_head = _fallback_subject(head, token_indices)
            method_parts.append("respaldo léxico para el sujeto")

        lemma = verb_lemma(head.text, head.lemma_) or head.lemma_ or head.text
        if object_token:
            obj = _phrase(object_token, clause_head_ids)
            object_head = object_token.text
            method_parts.append("dependencias")
        else:
            obj, object_head = _fallback_object(head, token_indices, normalize_term(lemma))
            if obj != "No detectado":
                method_parts.append("respaldo léxico para el objeto")

        proposition_text = "".join(
            sentence.doc[index].text_with_ws for index in token_indices
        ).strip()
        propositions.append(
            {
                "text": proposition_text or sentence.text,
                "subject": subject,
                "subject_head": subject_head,
                "verb": head.text,
                "verb_lemma": lemma,
                "object": obj,
                "object_head": object_head,
                "dependency": head.dep_,
                "extraction_method": " + ".join(dict.fromkeys(method_parts)),
                "start": min(token_indices),
            }
        )

    propositions.sort(key=lambda item: item["start"])
    for number, proposition in enumerate(propositions, start=1):
        proposition["number"] = number
        proposition.pop("start", None)
    return propositions


def analizar(text: str) -> dict[str, Any]:
    nlp = _load_model()
    if nlp is None:
        return {"available": False, "error": _MODEL_ERROR}

    memory_before = rss_mb()
    started = time.perf_counter()
    doc = nlp(text)
    elapsed_ms = round((time.perf_counter() - started) * 1000, 2)
    memory_after = rss_mb()

    tokens = [
        {
            "index": token.i + 1,
            "token": token.text,
            "lemma": token.lemma_,
            "pos": token.pos_,
            "tag": token.tag_,
            "morph": str(token.morph),
            "dependency": token.dep_,
            "governor": "ROOT" if token.dep_ == "ROOT" else token.head.text,
            "lexical_verb_backup": (
                token.pos_ not in {"VERB", "AUX"} and is_known_verb(token.text, token.lemma_)
            ),
        }
        for token in doc
    ]

    sentences: list[dict] = []
    all_propositions: list[dict] = []
    for sentence_number, sentence in enumerate(doc.sents, start=1):
        propositions = _sentence_propositions(sentence)
        for proposition in propositions:
            proposition["sentence_number"] = sentence_number
        all_propositions.extend(propositions)
        sentences.append(
            {
                "number": sentence_number,
                "text": sentence.text,
                "proposition_count": len(propositions),
                "propositions": propositions,
            }
        )

    # Generamos un gráfico independiente por oración para que las flechas no
    # se amontonen cuando el usuario escribe varias oraciones.
    displacy_trees: list[dict[str, Any]] = []
    try:
        for sentence_number, sentence in enumerate(doc.sents, start=1):
            sentence_doc = sentence.as_doc()
            tree_html = displacy.render(
                sentence_doc,
                style="dep",
                page=False,
                options={
                    "compact": False,
                    "distance": 135,
                    "offset_x": 65,
                    "arrow_spacing": 18,
                    "arrow_stroke": 2,
                    "arrow_width": 9,
                    "word_spacing": 42,
                    "collapse_punct": False,
                    "add_lemma": True,
                    "color": "#243b6b",
                    "bg": "#ffffff",
                    "font": "Inter, Segoe UI, sans-serif",
                },
            )
            displacy_trees.append(
                {
                    "number": sentence_number,
                    "text": sentence.text,
                    "html": tree_html,
                }
            )
    except Exception as exc:  # pragma: no cover - protección para modelos incompatibles
        displacy_trees = [
            {
                "number": 1,
                "text": text,
                "html": f"<p>No se pudo generar displaCy: {type(exc).__name__}</p>",
            }
        ]

    displacy_html = "".join(item["html"] for item in displacy_trees)
    first = all_propositions[0] if all_propositions else None
    return {
        "available": True,
        "tool": "spaCy",
        "model": "es_core_news_sm",
        "time_ms": elapsed_ms,
        "memory_mb": memory_after,
        "memory_delta_mb": round(memory_after - memory_before, 2),
        "tokens": tokens,
        "dependencies_count": len(tokens),
        "sentences": sentences,
        "proposition_count": len(all_propositions),
        "propositions": all_propositions,
        "svo": {
            "subject": first["subject"] if first else "No detectado",
            "verb": first["verb"] if first else "No detectado",
            "object": first["object"] if first else "No detectado",
        },
        "displacy_html": displacy_html,
        "displacy_trees": displacy_trees,
    }
