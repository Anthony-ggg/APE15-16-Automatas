"""Clasificación semántica basada en los conectores exigidos por la guía."""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class ConnectorRule:
    connector: str
    sentence_class: str
    relation: str


# Se ordenan de mayor a menor longitud para detectar primero conectores compuestos.
CONNECTOR_RULES: tuple[ConnectorRule, ...] = tuple(
    sorted(
        (
            ConnectorRule("sin embargo", "Coordinada", "Adversativa"),
            ConnectorRule("por lo tanto", "Subordinada", "Consecutiva"),
            ConnectorRule("puesto que", "Subordinada", "Causal"),
            ConnectorRule("para que", "Subordinada", "Final"),
            ConnectorRule("ya que", "Subordinada", "Causal"),
            ConnectorRule("mientras", "Subordinada", "Temporal"),
            ConnectorRule("cuando", "Subordinada", "Temporal"),
            ConnectorRule("porque", "Subordinada", "Causal"),
            ConnectorRule("aunque", "Subordinada", "Concesiva"),
            ConnectorRule("pero", "Coordinada", "Adversativa"),
            ConnectorRule("si", "Subordinada", "Condicional"),
            ConnectorRule("ni", "Coordinada", "Copulativa"),
            ConnectorRule("y", "Coordinada", "Copulativa"),
            ConnectorRule("e", "Coordinada", "Copulativa"),
            ConnectorRule("o", "Coordinada", "Disyuntiva"),
            ConnectorRule("u", "Coordinada", "Disyuntiva"),
        ),
        key=lambda rule: len(rule.connector),
        reverse=True,
    )
)


def _connector_pattern(connector: str) -> re.Pattern[str]:
    """Crea un patrón que evita encontrar letras dentro de otras palabras."""
    escaped = re.escape(connector).replace(r"\ ", r"\s+")
    return re.compile(rf"(?<!\w){escaped}(?!\w)", re.IGNORECASE | re.UNICODE)


def detect_connectors(text: str) -> list[dict]:
    """Devuelve todos los conectores válidos, sin coincidencias solapadas."""
    candidates: list[dict] = []
    for rule in CONNECTOR_RULES:
        for match in _connector_pattern(rule.connector).finditer(text):
            candidates.append(
                {
                    **asdict(rule),
                    "found_text": match.group(0),
                    "start": match.start(),
                    "end": match.end(),
                }
            )

    candidates.sort(key=lambda item: (item["start"], -(item["end"] - item["start"])))
    selected: list[dict] = []
    for candidate in candidates:
        overlaps = any(
            candidate["start"] < existing["end"]
            and candidate["end"] > existing["start"]
            for existing in selected
        )
        if not overlaps:
            selected.append(candidate)
    return selected


def classify_sentence(text: str) -> dict:
    """Clasifica una oración según el primer conector reconocido por la guía."""
    connectors = detect_connectors(text)
    if not connectors:
        return {
            "type": "Oración simple",
            "sentence_class": "Simple",
            "relation": "Sin relación compuesta",
            "connector": "Ninguno",
            "connectors": [],
        }

    primary = connectors[0]
    return {
        "type": f"Compuesta {primary['sentence_class']}",
        "sentence_class": primary["sentence_class"],
        "relation": primary["relation"],
        "connector": primary["found_text"],
        "connectors": connectors,
    }


def fallback_proposition_count(text: str) -> int:
    """Estimación usada únicamente cuando ambos analizadores no están disponibles."""
    return 2 if detect_connectors(text) else 1
