"""Load immutable A23 kernels for the SAME first-sample operation, no marginals."""

import hashlib
import importlib
import json
import sys
import types
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
ARCHIVE = ROOT / "attempts/23-canonical-epsilon-posterior/v2"


def materialize():
    manifest = json.loads((ARCHIVE / "manifest.json").read_text())
    source = ARCHIVE / "source.zip"
    inventory = manifest["archives"]["source.zip"]
    if hashlib.sha256(source.read_bytes()).hexdigest() != inventory["sha256"]:
        raise ValueError("frozen exact control source changed")
    target = ROOT / ".cache" / ("a25-control-" + manifest["version"]["source_commit"][:12])
    prefixes = ("attempts/23-canonical-epsilon-posterior/work/", "src/", "scripts/")
    with zipfile.ZipFile(source) as archive:
        for name, expected in inventory["files"].items():
            if not name.startswith(prefixes):
                continue
            path = target / name
            if path.exists():
                if hashlib.sha256(path.read_bytes()).hexdigest() != expected["sha256"]:
                    raise ValueError("materialized control changed")
            else:
                data = archive.read(name)
                if hashlib.sha256(data).hexdigest() != expected["sha256"]:
                    raise ValueError("source archive inventory differs")
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(data)
    return target, manifest["version"]["source_commit"], inventory["sha256"]


def module(name):
    package = "_a25_frozen_control"
    if package not in sys.modules:
        target, _, _ = materialize()
        root = types.ModuleType(package)
        root.__path__ = [str(target / "attempts/23-canonical-epsilon-posterior/work")]
        sys.modules[package] = root
    return importlib.import_module(package + "." + name)
