#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/../.."
A90_DIR=attempts/90-cache-aware-text-memory
A90_PYTHON=${A90_PYTHON:-/home/jota/projects/tcc-final/.venv-live/bin/python}
case "${1:-}" in
 prepare) "$A90_PYTHON" "$A90_DIR/prepare.py" ;;
 audit|cpu) "$A90_PYTHON" -u "$A90_DIR/pilot.py" --phase "$1" --output "$A90_DIR/evidence/$1-v1.jsonl" ;;
 ar|dllm|reader)
   # Bound wait; lock includes Python imports, loading, warmup, forwards and teardown.
   flock -w 1 /tmp/tcc-final-gpu-pilot.lock env A90_GPU_LOCKED=1 "$A90_PYTHON" -u "$A90_DIR/pilot.py" --phase "$1" --output "$A90_DIR/evidence/$1-v1.jsonl"
   ;;
 *) echo 'Usage: reproduce.sh prepare|audit|cpu|ar|dllm|reader' >&2;exit 2 ;;
esac
