"""Configuración central del proyecto APE 15 y APE 16."""

from __future__ import annotations

import os


class Config:
    CORENLP_URL = os.getenv("CORENLP_URL", "http://localhost:9000").rstrip("/")
    CORENLP_TIMEOUT_SECONDS = int(os.getenv("CORENLP_TIMEOUT_SECONDS", "45"))
    MAX_TEXT_LENGTH = int(os.getenv("MAX_TEXT_LENGTH", "1500"))
    JSON_SORT_KEYS = False
    JSON_AS_ASCII = False
