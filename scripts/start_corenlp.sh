#!/usr/bin/env bash
set -euo pipefail

PORT="${CORENLP_PORT:-9000}"
TIMEOUT="${CORENLP_SERVER_TIMEOUT:-45000}"
MEMORY="${CORENLP_MEMORY:-4g}"
CORENLP_HOME="${CORENLP_HOME:-}"
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PID_FILE="$PROJECT_ROOT/corenlp-server.pid"
LOG_FILE="$PROJECT_ROOT/corenlp-server.log"

if [[ -z "$CORENLP_HOME" || ! -d "$CORENLP_HOME" ]]; then
  echo "ERROR: defina CORENLP_HOME con la carpeta descomprimida de Stanford CoreNLP."
  echo "Ejemplo: export CORENLP_HOME=\$HOME/Descargas/stanford-corenlp-4.x.x"
  exit 1
fi

if ! command -v java >/dev/null 2>&1; then
  echo "ERROR: Java no está instalado. En Ubuntu: sudo apt install openjdk-17-jre"
  exit 1
fi

if ! find "$CORENLP_HOME" -maxdepth 1 -iname '*models-spanish*.jar' -print -quit | grep -q .; then
  echo "ERROR: falta el JAR de modelos en español dentro de $CORENLP_HOME"
  echo "Descargue el modelo español de la misma versión que CoreNLP y cópielo en esa carpeta."
  exit 1
fi

if [[ -f "$PID_FILE" ]] && kill -0 "$(cat "$PID_FILE")" 2>/dev/null; then
  echo "CoreNLP ya está activo con PID $(cat "$PID_FILE")."
  exit 0
fi

cd "$CORENLP_HOME"
nohup java "-mx${MEMORY}" -cp "*" \
  edu.stanford.nlp.pipeline.StanfordCoreNLPServer \
  -serverProperties StanfordCoreNLP-spanish.properties \
  -port "$PORT" \
  -timeout "$TIMEOUT" \
  -preload tokenize,ssplit,pos,lemma,parse,depparse \
  >"$LOG_FILE" 2>&1 &

echo $! > "$PID_FILE"
echo "Iniciando CoreNLP (PID $(cat "$PID_FILE"))..."

for _ in {1..120}; do
  if curl -fsS "http://localhost:${PORT}/ready" >/dev/null 2>&1; then
    echo "CoreNLP está listo en http://localhost:${PORT}"
    exit 0
  fi
  if ! kill -0 "$(cat "$PID_FILE")" 2>/dev/null; then
    echo "CoreNLP se detuvo durante el inicio. Revise: $LOG_FILE"
    exit 1
  fi
  sleep 1
done

echo "CoreNLP continúa cargando. Revise el estado con: curl http://localhost:${PORT}/ready"
echo "Registro: $LOG_FILE"
