"""ONLY tokenizer/config metadata; no numerical head array or model weights."""

import hashlib
import inspect
import json
import subprocess
import urllib.request
from pathlib import Path
from zipfile import ZipFile

from mwpc_exact.tokenizer_bytes import CompositionalByteLevelAdapter

from .frozen_metadata.table import LexerTable


def main():
    base = Path(__file__).parent
    output = base / "evidence" / "metadata-v6"
    output.mkdir(parents=True, exist_ok=False)
    packet = Path(
        "attempts/24-certified-depth-approximation/work/evidence/first-full-head-v2/packet.zip"
    )
    with ZipFile(packet) as archive:
        vocab = archive.read("vocabulary.json")
    adapter = CompositionalByteLevelAdapter.from_token_pieces(json.loads(vocab))
    table = LexerTable(adapter)
    config_url = "https://huggingface.co/kuleshov-group/mdlm-owt/resolve/d0958fa851335ece6c15260ce0025f030673c0fb/config.json"
    with urllib.request.urlopen(config_url, timeout=30) as response:
        config = response.read()
    cfg = json.loads(config)
    assert cfg["vocab_size"] == len(table.class_of) == 50258 and cfg["hidden_dim"] == 768
    (output / "model-config.json").write_bytes(config)
    mapping = {
        "class_of": list(table.class_of),
        "class_sizes": [len(c) for c in table.classes],
        "vocabulary": len(table.class_of),
        "classes": len(table.classes),
    }
    (output / "mapping.json").write_text(json.dumps(mapping, separators=(",", ":")) + "\n")
    source = Path(inspect.getfile(CompositionalByteLevelAdapter))
    record = {
        "producer": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
        "packet": str(packet),
        "packet_sha256": hashlib.sha256(packet.read_bytes()).hexdigest(),
        "opened_archive_members": ["vocabulary.json"],
        "vocabulary_sha256": hashlib.sha256(vocab).hexdigest(),
        "model_config_URL": config_url,
        "model_config_sha256": hashlib.sha256(config).hexdigest(),
        "adapter_source": str(source),
        "adapter_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
        "mapping_sha256": hashlib.sha256((output / "mapping.json").read_bytes()).hexdigest(),
        "vocabulary": mapping["vocabulary"],
        "classes": mapping["classes"],
        "class_sizes": mapping["class_sizes"],
        "model_parameter_reads": 0,
        "model_forwards": 0,
        "numeric_head_archive_members_opened": [],
        "competitive_timing": False,
    }
    (output / "provenance.json").write_text(json.dumps(record, indent=2) + "\n")
    print(json.dumps({k: v for k, v in record.items() if k != "class_sizes"}, indent=2))


if __name__ == "__main__":
    main()
