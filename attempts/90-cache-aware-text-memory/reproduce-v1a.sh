#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/../.."
A90_DIR=attempts/90-cache-aware-text-memory
A90_PYTHON=${A90_PYTHON:-/home/jota/projects/tcc-final/.venv-live/bin/python}
# Reuse frozen editor/CPU memories. Never overwrite the failed V1 reader evidence.
flock -w 1 /tmp/tcc-final-gpu-pilot.lock env A90_GPU_LOCKED=1 "$A90_PYTHON" -u "$A90_DIR/pilot.py" --phase reader --output "$A90_DIR/evidence/reader-v1a.jsonl"
