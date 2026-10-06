"""Verify the unchanged scientific archive against the pre-cleanup source freeze."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    data = json.loads((ROOT / "docs/evidence/m32-preserved-artifacts.json").read_text())
    for name, digest in data["preserved_scientific_files"].items():
        path = ROOT / name
        if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != digest:
            raise ValueError(f"Frozen scientific artifact changed: {name}")
    print(f"Preserved {len(data['preserved_scientific_files'])} scientific files unchanged")


if __name__ == "__main__":
    main()
