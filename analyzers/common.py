"""Funciones comunes para construir proposiciones y métricas."""

from __future__ import annotations

import os
from collections.abc import Iterable

import psutil


CLAUSE_RELATIONS = {
    "root",
    "conj",
    "advcl",
    "ccomp",
    "xcomp",
    "acl",
    "acl:relcl",
    "relcl",
    "parataxis",
}
SUBJECT_RELATIONS = {"nsubj", "nsubj:pass", "csubj", "csubj:pass"}
OBJECT_RELATIONS = {"obj", "dobj"}


def rss_mb(pid: int | None = None) -> float:
    """Memoria residente del proceso indicado, en MB."""
    try:
        process = psutil.Process(pid or os.getpid())
        return round(process.memory_info().rss / (1024 * 1024), 2)
    except (psutil.Error, OSError):
        return 0.0


def corenlp_java_memory_mb() -> float | None:
    """Busca el servidor Java CoreNLP y suma su memoria residente."""
    total = 0
    found = False
    for process in psutil.process_iter(["name", "cmdline", "memory_info"]):
        try:
            cmdline = " ".join(process.info.get("cmdline") or [])
            if "StanfordCoreNLPServer" in cmdline:
                memory_info = process.info.get("memory_info")
                if memory_info:
                    total += memory_info.rss
                    found = True
        except (psutil.NoSuchProcess, psutil.AccessDenied, TypeError):
            continue
    return round(total / (1024 * 1024), 2) if found else None


def normalize_dep(dep: str) -> str:
    return dep.lower().strip()


def is_clause_relation(dep: str) -> bool:
    normalized = normalize_dep(dep)
    return normalized in CLAUSE_RELATIONS or normalized.split(":", 1)[0] in CLAUSE_RELATIONS


def is_subject_relation(dep: str) -> bool:
    normalized = normalize_dep(dep)
    return normalized in SUBJECT_RELATIONS or normalized.split(":", 1)[0] in SUBJECT_RELATIONS


def is_object_relation(dep: str) -> bool:
    normalized = normalize_dep(dep)
    return normalized in OBJECT_RELATIONS or normalized.split(":", 1)[0] in OBJECT_RELATIONS


def join_tokens(tokens: Iterable[str]) -> str:
    """Une tokens respetando signos de puntuación frecuentes."""
    result = ""
    no_space_before = {".", ",", ";", ":", "!", "?", ")", "]", "}"}
    no_space_after = {"(", "[", "{"}
    for token in tokens:
        if not result:
            result = token
        elif token in no_space_before:
            result += token
        elif result[-1:] in no_space_after:
            result += token
        else:
            result += " " + token
    return result.strip()
