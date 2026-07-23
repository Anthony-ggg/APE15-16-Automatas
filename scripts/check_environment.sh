#!/usr/bin/env bash
set -u

check() {
  if command -v "$1" >/dev/null 2>&1; then
    echo "[OK] $1: $($1 --version 2>&1 | head -n 1)"
  else
    echo "[FALTA] $1"
  fi
}

check python3
check java
check curl

python3 - <<'PY'
try:
    import flask
    print(f"[OK] Flask {flask.__version__ if hasattr(flask, '__version__') else 'instalado'}")
except Exception:
    print("[FALTA] Flask")
try:
    import spacy
    print(f"[OK] spaCy {spacy.__version__}")
    try:
        spacy.load("es_core_news_sm")
        print("[OK] Modelo es_core_news_sm")
    except OSError:
        print("[FALTA] Modelo es_core_news_sm")
except Exception:
    print("[FALTA] spaCy")
PY

if curl -fsS http://localhost:9000/ready >/dev/null 2>&1; then
  echo "[OK] Stanford CoreNLP listo en puerto 9000"
else
  echo "[FALTA] Stanford CoreNLP no responde en puerto 9000"
fi
