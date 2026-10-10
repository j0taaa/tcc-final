"""Use immutable A23 control source, never a mutable sibling attempt."""

import hashlib
import json
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
ARCHIVE = ROOT / "attempts/23-canonical-epsilon-posterior/v2"


def materialize():
    manifest = json.loads((ARCHIVE / "manifest.json").read_text())
    source = ARCHIVE / "source.zip"
    expected = manifest["archives"]["source.zip"]
    if hashlib.sha256(source.read_bytes()).hexdigest() != expected["sha256"]:
        raise ValueError("frozen competent control archive changed")
    target = ROOT / ".cache" / ("a24-control-" + manifest["version"]["source_commit"][:12])
    prefixes = ("attempts/23-canonical-epsilon-posterior/work/", "src/", "scripts/")
    with zipfile.ZipFile(source) as archive:
        for name, item in expected["files"].items():
            if not name.startswith(prefixes):
                continue
            path = target / name
            if path.exists():
                if hashlib.sha256(path.read_bytes()).hexdigest() != item["sha256"]:
                    raise ValueError("materialized immutable control changed")
            else:
                data = archive.read(name)
                if hashlib.sha256(data).hexdigest() != item["sha256"]:
                    raise ValueError("frozen source inventory differs")
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(data)
    return target, manifest["version"]["source_commit"], expected["sha256"]
