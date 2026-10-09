"""Optional offline full-head softmax and exact-posterior reproduction; no model."""

import argparse
import hashlib
import json
import tempfile
from pathlib import Path
from types import SimpleNamespace

from .measure import worker


def main():
    import numpy as np
    import torch

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--capture", type=Path, required=True)
    parser.add_argument("--case", required=True)
    args = parser.parse_args()
    metadata = json.loads((args.capture / "metadata.json").read_text())
    case = json.loads((args.capture / (args.case + ".json")).read_text())
    files = (
        (args.case + ".npy", "probabilities_sha256"),
        (args.case + ".logits.npy", "raw_logits_sha256"),
    )
    for name, key in files:
        if hashlib.sha256((args.capture / name).read_bytes()).hexdigest() != case[key]:
            raise ValueError("complete captured head/probabilities changed")
    torch.set_num_threads(metadata["config"]["torch_cpu_threads"])
    logits = torch.from_numpy(np.load(args.capture / (args.case + ".logits.npy")))
    logits[:, metadata["config"]["mask_token_id"]] = float("-inf")
    probabilities = np.load(args.capture / (args.case + ".npy"), allow_pickle=False)
    if not np.array_equal(logits.softmax(-1).numpy(), probabilities):
        raise ValueError("archived probabilities differ from full-head CPU F64 softmax")
    protocol = json.loads((Path(__file__).parent / "protocol.json").read_text())
    with tempfile.TemporaryDirectory() as scratch:
        result = worker(
            SimpleNamespace(
                capture=args.capture,
                case=args.case,
                method="local",
                repeat=0,
                matrices=Path(scratch),
            ),
            protocol,
        )
    if result["status"] != "complete":
        raise ValueError("offline posterior did not complete")
    expected_file = args.capture / (args.case + ".expected.json")
    if expected_file.exists():
        expected = json.loads(expected_file.read_text())
        for key in ("valid_mass", "exact_total", "matrix_sha256"):
            if result[key] != expected[key]:
                raise ValueError(f"recomputed exact posterior differs: {key}")
    print(
        json.dumps(
            dict(
                status="exact_agreement",
                full_head_softmax="byte_equal",
                valid_mass=result["valid_mass"],
                matrix_sha256=result["matrix_sha256"],
                scope="Frozen input/kernel replay; checkpoint forward needs optional model",
            )
        )
    )


if __name__ == "__main__":
    main()
