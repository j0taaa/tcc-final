"""Classical lossless archive coding; reconstruct and hash ORIGINAL NPZ bytes."""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import shutil
from pathlib import Path

import numpy as np


def sha(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def npz_bytes(**arrays):
    buffer = io.BytesIO()
    np.savez_compressed(buffer, **arrays)
    return buffer.getvalue()


def unpack(path, previous=None):
    with np.load(path) as packet:
        shape = tuple(packet["shape"].tolist())
        result = np.zeros(int(np.prod(shape)), dtype=np.uint16)
        for bit in range(16):
            result |= (
                np.unpackbits(packet["planes"][bit], count=result.size, bitorder="little").astype(
                    np.uint16
                )
                << bit
            )
        result = result.reshape(shape)
        if previous is not None:
            result ^= previous
        return packet["input_ids"].copy(), result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--capture", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    manifest = {
        "codec": "classical_bf16_xor_bitshuffle_npz_block4_v1",
        "numpy": np.__version__,
        "scope": "Lossless storage only; not new experiment or scientific method",
        "files": [],
    }
    previous, final_heads = None, {}
    for original in sorted(args.capture.glob("head-*.npz")):
        ordinal = int(original.stem.split("-")[1])
        part = args.output / f"part-{ordinal // 4:02d}"
        part.mkdir(exist_ok=True)
        if ordinal % 4 == 0:
            previous = None
        with np.load(original) as packet:
            ids, current = packet["input_ids"], packet["response_logits_bf16"]
            residual = current if previous is None else current ^ previous
            planes = np.stack(
                [
                    np.packbits(((residual.ravel() >> b) & 1).astype(np.uint8), bitorder="little")
                    for b in range(16)
                ]
            )
            compact = part / (original.stem + ".compact.npz")
            np.savez_compressed(
                compact, planes=planes, shape=np.asarray(current.shape), input_ids=ids
            )
        actual_ids, actual = unpack(compact, previous)
        assert np.array_equal(actual, current) and np.array_equal(actual_ids, ids)
        reconstructed = npz_bytes(input_ids=actual_ids, response_logits_bf16=actual)
        assert hashlib.sha256(reconstructed).hexdigest() == sha(original)
        manifest["files"].append(
            {
                "original": original.name,
                "original_bytes": original.stat().st_size,
                "original_sha256": sha(original),
                "compact": str(compact.relative_to(args.output)),
                "compact_sha256": sha(compact),
                "previous_ordinal": None if ordinal % 4 == 0 else ordinal - 1,
            }
        )
        rng = original.with_name(original.stem + "-rng.pt")
        shutil.copyfile(rng, part / rng.name)
        manifest["files"].append(
            {
                "original": rng.name,
                "original_bytes": rng.stat().st_size,
                "original_sha256": sha(rng),
                "copied": str((part / rng.name).relative_to(args.output)),
            }
        )
        if ordinal and ordinal % 16 == 0:
            final_heads[ordinal // 16 - 1] = actual.copy(), part
        previous = actual
        print(
            json.dumps(
                {
                    "head": ordinal,
                    "status": "ORIGINAL_NPZ_BYTE_SHA256_MATCH",
                    "original_bytes": original.stat().st_size,
                    "compact_bytes": compact.stat().st_size,
                }
            ),
            flush=True,
        )
    assert len(final_heads) == 8
    for index, (bits, part) in final_heads.items():
        original = args.capture / f"terminal-{index:02d}.npz"
        with np.load(original) as packet:
            tokens, ids = packet["tokens"], packet["original_ids"]
            compact = part / f"terminal-{index:02d}.compact.npz"
            np.savez_compressed(compact, tokens=tokens, original_ids=ids)
            scores = (bits.astype(np.uint32) << 16).view(np.float32)[None, ...]
            reconstructed = npz_bytes(scores_float32=scores, tokens=tokens, original_ids=ids)
        assert hashlib.sha256(reconstructed).hexdigest() == sha(original)
        manifest["files"].append(
            {
                "original": original.name,
                "original_bytes": original.stat().st_size,
                "original_sha256": sha(original),
                "compact": str(compact.relative_to(args.output)),
                "compact_sha256": sha(compact),
                "response_head_ordinal": (index + 1) * 16,
            }
        )
        rng = original.with_name(original.stem + "-rng.pt")
        shutil.copyfile(rng, part / rng.name)
        manifest["files"].append(
            {
                "original": rng.name,
                "original_bytes": rng.stat().st_size,
                "original_sha256": sha(rng),
                "copied": str((part / rng.name).relative_to(args.output)),
            }
        )
    metadata = args.output / "metadata"
    metadata.mkdir()
    for original in sorted(args.capture.iterdir()):
        if original.suffix in (".npz", ".pt"):
            continue
        shutil.copyfile(original, metadata / original.name)
        manifest["files"].append(
            {
                "original": original.name,
                "original_bytes": original.stat().st_size,
                "original_sha256": sha(original),
                "copied": str((metadata / original.name).relative_to(args.output)),
            }
        )
    assert len(manifest["files"]) == len(list(args.capture.iterdir()))
    manifest.update(
        status="ALL_ORIGINAL_BYTES_ROUNDTRIP_VERIFIED",
        decoded_npz_files=137,
        original_bytes=sum(r["original_bytes"] for r in manifest["files"]),
        compact_bytes=sum(p.stat().st_size for p in args.output.rglob("*") if p.is_file()),
    )
    (args.output / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps({k: v for k, v in manifest.items() if k != "files"}))


if __name__ == "__main__":
    main()
