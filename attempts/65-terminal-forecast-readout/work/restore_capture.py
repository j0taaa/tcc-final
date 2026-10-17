"""Restore original V8 files and verify every captured byte SHA256, no model."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from pathlib import Path

import numpy as np
from pack_capture import unpack


def sha(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def restore(packet_root, output):
    output.mkdir(parents=True, exist_ok=False)
    manifest = json.loads((packet_root / "manifest.json").read_text())
    assert manifest["status"] == "ALL_ORIGINAL_BYTES_ROUNDTRIP_VERIFIED"
    previous, final = None, {}
    heads = [
        f
        for f in manifest["files"]
        if f["original"].startswith("head-") and f["original"].endswith(".npz")
    ]
    for entry in sorted(heads, key=lambda f: f["original"]):
        source = packet_root / entry["compact"]
        assert sha(source) == entry["compact_sha256"]
        if entry["previous_ordinal"] is None:
            previous = None
        ids, bits = unpack(source, previous)
        target = output / entry["original"]
        np.savez_compressed(target, input_ids=ids, response_logits_bf16=bits)
        assert sha(target) == entry["original_sha256"]
        ordinal = int(target.stem.split("-")[1])
        if ordinal and ordinal % 16 == 0:
            final[ordinal] = bits.copy()
        previous = bits
        print(json.dumps({"restored": target.name, "original_byte_sha256": "MATCH"}), flush=True)
    for entry in manifest["files"]:
        target = output / entry["original"]
        if "copied" in entry:
            shutil.copyfile(packet_root / entry["copied"], target)
        elif entry["original"].startswith("terminal-"):
            source = packet_root / entry["compact"]
            assert sha(source) == entry["compact_sha256"]
            with np.load(source) as packet:
                scores = (final[entry["response_head_ordinal"]].astype(np.uint32) << 16).view(
                    np.float32
                )[None, ...]
                np.savez_compressed(
                    target,
                    scores_float32=scores,
                    tokens=packet["tokens"],
                    original_ids=packet["original_ids"],
                )
        assert target.stat().st_size == entry["original_bytes"]
        assert sha(target) == entry["original_sha256"]
    assert len(list(output.iterdir())) == len(manifest["files"])
    print(
        json.dumps(
            {
                "status": "ALL_ORIGINAL_CAPTURE_BYTES_RESTORED",
                "files": len(manifest["files"]),
                "original_bytes": sum(f["original_bytes"] for f in manifest["files"]),
                "new_neural_forwards": 0,
            }
        )
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--packets", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    restore(args.packets, args.output)
