"""Verified immutable A24 V11 compiler, isolated namespace, unchanged source."""

import hashlib
import importlib
import json
import sys
import types
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
ARCHIVE = ROOT / "attempts/24-certified-depth-approximation/v11"


def load():
    manifest = json.loads((ARCHIVE / "manifest.json").read_text())
    item = manifest["archives"]["source.zip"]
    source = ARCHIVE / "source.zip"
    if manifest["version"]["source_commit"] != "0c75b91ca578488011b8572b1271ac0d16c2e879":
        raise ValueError("compiler producer changed")
    if hashlib.sha256(source.read_bytes()).hexdigest() != item["sha256"]:
        raise ValueError("compiler immutable archive changed")
    target = ROOT / ".cache" / ("a51-a24-compiler-" + item["sha256"][:16])
    prefix = "attempts/24-certified-depth-approximation/work/"
    with zipfile.ZipFile(source) as archive:
        for name, record in item["files"].items():
            if name.startswith("src/") and name.endswith(".py"):
                # Absolute core imports are permitted only with exact frozen bytes.
                if hashlib.sha256((ROOT / name).read_bytes()).hexdigest() != record["sha256"]:
                    raise ValueError("absolute core differs from frozen source")
            if not name.startswith(prefix) or not name.endswith(".py"):
                continue
            path = target / name
            if path.exists():
                data = path.read_bytes()
            else:
                data = archive.read(name)
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(data)
            if hashlib.sha256(data).hexdigest() != record["sha256"]:
                raise ValueError("materialized compiler differs from frozen inventory")
    namespace = "_a51_a24_compiler_" + item["sha256"][:12]
    if namespace not in sys.modules:
        package = types.ModuleType(namespace)
        package.__path__ = [str(target / prefix)]
        sys.modules[namespace] = package
    return dict(
        termination=importlib.import_module(namespace + ".consumer_v3.termination"),
        query=importlib.import_module(namespace + ".consumer_v2.query"),
        blocks=importlib.import_module(namespace + ".consumer_v2.block_stats"),
        producer=manifest["version"]["source_commit"],
        archive_sha256=item["sha256"],
    )
