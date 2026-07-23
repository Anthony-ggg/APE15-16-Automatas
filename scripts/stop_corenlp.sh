#!/usr/bin/env bash
set -euo pipefail
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PID_FILE="$PROJECT_ROOT/corenlp-server.pid"

if [[ ! -f "$PID_FILE" ]]; then
  echo "No existe un PID guardado para CoreNLP."
  exit 0
fi

PID="$(cat "$PID_FILE")"
if kill -0 "$PID" 2>/dev/null; then
  kill "$PID"
  echo "CoreNLP detenido (PID $PID)."
else
  echo "El proceso $PID ya no estaba activo."
fi
rm -f "$PID_FILE"
