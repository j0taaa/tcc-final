"""Opt-in exact softmax/original-byte replay; does not run the neural model."""

import argparse
import hashlib
import json
import subprocess
from pathlib import Path


def run(source, output):
    import numpy as np
    import torch

    from mwpc_exact.tokenizer_bytes import CompositionalByteLevelAdapter

    metadata = json.loads((source / "metadata.json").read_text())
    config = metadata["config"]
    torch.set_num_threads(config["torch_cpu_threads"])
    torch.set_flush_denormal(False)
    adapter = CompositionalByteLevelAdapter.from_token_pieces(
        json.loads((source / "vocabulary.json").read_text())
    )
    for example in metadata["selected"]:
        raw = b"".join(adapter.emissions[t] for t in example["tokens"])
        assert raw == example["text"].encode("utf8")
        assert hashlib.sha256(raw).hexdigest() == example["source_sha256"]
    frames = []
    for path in sorted(source.glob("*.json")):
        if path.stem in ["metadata", "vocabulary"]:
            continue
        frame = json.loads(path.read_text())
        for key, extension in [
            ("probabilities_sha256", ".npy"),
            ("raw_logits_sha256", ".logits.npy"),
        ]:
            assert (
                hashlib.sha256((source / (path.stem + extension)).read_bytes()).hexdigest()
                == frame[key]
            )
        probabilities = np.load(source / (path.stem + ".npy"), allow_pickle=False)
        logits = np.load(source / (path.stem + ".logits.npy"), allow_pickle=False)
        assert np.array_equal(logits.astype("float32").astype("float64"), logits)
        scores = torch.from_numpy(logits).clone()
        scores[:, config["mask_token_id"]] = float("-inf")
        assert np.array_equal(scores.softmax(-1).numpy(), probabilities)
        assert np.all(probabilities[:, config["mask_token_id"]] == 0)
        frames.append(dict(case=path.stem, torch_softmax_bit_equal=True, logits_are_f32_lift=True))
    assert len(frames) == 15
    report = dict(
        status="PASS",
        verifier_producer=subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
        capture_producer=metadata["producer"],
        new_forwards=0,
        complete_original_byte_documents=5,
        frames=frames,
        torch_version=torch.__version__,
        input_scope="Raw arrays local; replay requires those optional inputs, not only hashes",
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2) + "\n")
    print(
        json.dumps(
            {
                k: report[k]
                for k in [
                    "status",
                    "capture_producer",
                    "new_forwards",
                    "complete_original_byte_documents",
                ]
            }
        ),
        flush=True,
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    run(args.source, args.output)
