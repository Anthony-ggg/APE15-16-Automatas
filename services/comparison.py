"""Construcción de la tabla comparativa solicitada en la actividad 6."""

from __future__ import annotations

from typing import Any


def _normalize_corenlp_pos(tag: str) -> str:
    tag = (tag or "").lower()
    if tag.startswith("np"):
        return "PROPN"
    if tag.startswith("n"):
        return "NOUN"
    if tag.startswith("v"):
        return "VERB"
    if tag.startswith("a"):
        return "ADJ"
    if tag.startswith("d"):
        return "DET"
    if tag.startswith("p"):
        return "PRON"
    if tag.startswith("r"):
        return "ADV"
    if tag.startswith("s"):
        return "ADP"
    if tag.startswith("cc"):
        return "CCONJ"
    if tag.startswith("cs"):
        return "SCONJ"
    if tag.startswith("c"):
        return "CCONJ"
    if tag.startswith("z"):
        return "NUM"
    if tag.startswith("f"):
        return "PUNCT"
    if tag.startswith("i"):
        return "INTJ"
    return tag.upper() or "X"


def _normalize_spacy_pos(tag: str) -> str:
    return "VERB" if tag == "AUX" else tag


def pos_agreement(spacy_result: dict, corenlp_result: dict) -> dict | None:
    if not spacy_result.get("available") or not corenlp_result.get("available"):
        return None

    spacy_tokens = spacy_result.get("tokens", [])
    corenlp_tokens = corenlp_result.get("tokens", [])
    compared = 0
    matches = 0
    for spacy_token, corenlp_token in zip(spacy_tokens, corenlp_tokens):
        if spacy_token["token"].casefold() != corenlp_token["token"].casefold():
            continue
        compared += 1
        spa_pos = _normalize_spacy_pos(spacy_token.get("pos", ""))
        core_pos = _normalize_corenlp_pos(corenlp_token.get("pos", ""))
        if spa_pos == core_pos:
            matches += 1

    if compared == 0:
        return None
    return {
        "percentage": round(matches * 100 / compared, 2),
        "matches": matches,
        "compared": compared,
    }


def _value(result: dict, field: str, suffix: str = "") -> str:
    if not result.get("available"):
        return "No disponible"
    value = result.get(field)
    if value is None:
        return "No medido"
    return f"{value}{suffix}"


def build_comparison(spacy_result: dict, corenlp_result: dict) -> dict[str, Any]:
    agreement = pos_agreement(spacy_result, corenlp_result)
    agreement_text = (
        f"{agreement['percentage']}% ({agreement['matches']}/{agreement['compared']} tokens)"
        if agreement
        else "No calculable"
    )

    rows = [
        {
            "aspect": "Tiempo de ejecución",
            "spacy": _value(spacy_result, "time_ms", " ms"),
            "corenlp": _value(corenlp_result, "time_ms", " ms"),
        },
        {
            "aspect": "Precisión POS (acuerdo referencial)",
            "spacy": agreement_text,
            "corenlp": agreement_text,
        },
        {
            "aspect": "Árbol sintáctico",
            "spacy": "Árbol de dependencias visual con displaCy" if spacy_result.get("available") else "No disponible",
            "corenlp": "Árbol de constituyentes (parse tree)" if corenlp_result.get("available") else "No disponible",
        },
        {
            "aspect": "Dependencias detectadas",
            "spacy": _value(spacy_result, "dependencies_count"),
            "corenlp": _value(corenlp_result, "dependencies_count"),
        },
        {
            "aspect": "Facilidad de uso",
            "spacy": "Alta: librería y modelo dentro de Python",
            "corenlp": "Media: requiere Java, modelos españoles y servidor",
        },
        {
            "aspect": "Consumo de memoria observado",
            "spacy": _value(spacy_result, "memory_mb", " MB"),
            "corenlp": _value(corenlp_result, "memory_mb", " MB"),
        },
    ]
    return {
        "rows": rows,
        "pos_agreement": agreement,
        "note": (
            "La coincidencia POS compara las etiquetas producidas por ambas herramientas; "
            "no sustituye una evaluación contra un corpus etiquetado manualmente."
        ),
    }
