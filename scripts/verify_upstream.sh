#!/usr/bin/env bash
set -euo pipefail
python3 - <<'VERIFY'
import hashlib
import json
from pathlib import Path

root = Path('vendor/EPIC-Decoding')
data = json.loads((root / '.upstream-manifest.json').read_text())
assert data['upstream_commit'] == '5b1b31098f34ed3691d2a9f4aae14fdf5839d072'
assert data['upstream_repository'] == 'https://github.com/hyundong98/EPIC-Decoding'
for name, digest in data['retained_file_sha256'].items():
    path = root / name
    if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != digest:
        raise SystemExit(f'Pinned EPIC snapshot changed: {name}')
for name in data['removed_test_files']:
    if (root / name).exists():
        raise SystemExit(f'Removed upstream test returned: {name}')
print(f"EPIC production snapshot verified: {data['upstream_commit']}; tests removed")
VERIFY
