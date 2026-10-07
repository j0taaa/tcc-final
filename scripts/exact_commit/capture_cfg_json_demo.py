"""Opt-in fresh official CPU MDLM predictions for the nine frozen JSON contexts."""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import platform
import subprocess
from fractions import Fraction
from pathlib import Path
from time import perf_counter

from scripts.exact_commit.mdlm_cpu import load_cpu_model
from scripts.exact_commit.run_cfg_posterior_audit import CONFIG, ROOT, run_job, source_grammar

from mwpc_exact.conflict_proof import state_data
from mwpc_exact.eos_policy import EOSMode, EOSPolicy
from mwpc_exact.mass_certificate import ProbabilityInput
from mwpc_exact.reference.normalization import normalize_to_cnf
from mwpc_exact.state import SelectionInput
from mwpc_exact.support import SupportPolicy, build_per_position_support
from mwpc_exact.tokenizer_bytes import CompositionalByteLevelAdapter
from mwpc_exact.types import SupportKind


def main():
    import numpy as np
    import torch
    from transformers import AutoTokenizer

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    if subprocess.check_output(["git", "status", "--porcelain"], cwd=ROOT).strip():
        raise ValueError("commit producing code/config before fresh forwards")
    config = json.loads(CONFIG.read_text())
    profile = config["fresh_model_demonstration"]
    original = json.loads(
        (ROOT / "configs/experiments/m31_probability_scaling_cpu_v1.json").read_text()
    )
    torch.set_num_threads(profile["torch_cpu_threads"])
    torch.manual_seed(config["seed"])
    tokenizer = AutoTokenizer.from_pretrained(
        original["tokenizer_id"],
        revision=original["tokenizer_revision"],
        cache_dir=str(ROOT / ".cache/mdlm"),
        local_files_only=True,
    )
    model, hashes, adapted_hash = load_cpu_model(original, ROOT / ".cache/mdlm")
    pieces = (
        *(
            tokenizer.convert_ids_to_tokens(t) if t not in tokenizer.all_special_ids else None
            for t in range(len(tokenizer))
        ),
        None,
    )
    adapter = CompositionalByteLevelAdapter.from_token_pieces(pieces)
    grammar = normalize_to_cnf(source_grammar("json")).grammar
    args.output.mkdir(parents=True, exist_ok=False)
    metadata = {
        "git_commit": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
        ).strip(),
        "seed": config["seed"],
        "config_sha256": hashlib.sha256(CONFIG.read_bytes()).hexdigest(),
        "model_id": original["model_id"],
        "model_revision": original["model_revision"],
        "tokenizer_revision": original["tokenizer_revision"],
        "checkpoint_sha256": hashes,
        "adapted_model_sha256": adapted_hash,
        "device": "cpu",
        "torch": torch.__version__,
        "python": platform.python_version(),
        "platform": platform.platform(),
        "grammar_sha256": hashlib.sha256(
            json.dumps(grammar.to_dict(), sort_keys=True).encode()
        ).hexdigest(),
        "support_policy": f"top{profile['top_k']}; no injected answer tokens",
        "numeric_reference": original["numeric_reference"],
        "eos_semantics": "ABSENT",
        "claim_scope": "frozen mean-field syntax demo; exact_on_support; no semantic metric",
        "cpu_model": next(
            line.split(":", 1)[1].strip()
            for line in Path("/proc/cpuinfo").read_text().splitlines()
            if line.startswith("model name")
        ),
        "torch_threads": torch.get_num_threads(),
    }
    (args.output / "metadata.json").write_text(json.dumps(metadata, indent=2) + "\n")
    (args.output / "config.json").write_bytes(CONFIG.read_bytes())
    with torch.inference_mode(), (args.output / "rows.jsonl").open("x") as output:
        model(
            input_ids=torch.full((1, 32), original["mask_token_id"], dtype=torch.long),
            timesteps=torch.zeros(1),
        )
        for context, (prefix, suffix) in enumerate(profile["prefix_suffix"]):
            left = tokenizer.encode(prefix, add_special_tokens=False)
            right = tokenizer.encode(suffix, add_special_tokens=False)
            for slots in profile["slots"]:
                name = f"json-context{context}-{slots}"
                tokens = left + [original["mask_token_id"]] * slots + right
                started = perf_counter()
                logits = model(input_ids=torch.tensor([tokens]), timesteps=torch.zeros(1))[
                    0, len(left) : len(left) + slots
                ]
                forward = perf_counter() - started
                normalized = logits.to(torch.float64).clone()
                normalized[:, original["mask_token_id"]] = float("-inf")
                probabilities = normalized.softmax(-1)
                array = args.output / f"{name}.npz"
                np.savez_compressed(
                    array, logits=logits.numpy(), probabilities=probabilities.numpy()
                )
                started = perf_counter()
                canvas = tuple(None if t == original["mask_token_id"] else t for t in tokens)
                rows = {i: (t,) for i, t in enumerate(canvas) if t is not None}
                distributions = [(Fraction(1),)] * len(canvas)
                normalization = []
                for free in range(slots):
                    weights = tuple(Fraction.from_float(float(p)) for p in probabilities[free])
                    total = sum(weights, Fraction())
                    chosen = sorted(
                        normalized[free]
                        .argsort(descending=True, stable=True)[: profile["top_k"]]
                        .tolist()
                    )
                    position = len(left) + free
                    rows[position] = tuple(chosen)
                    distributions[position] = tuple(weights[t] / total for t in chosen)
                    normalization.append([total.numerator, total.denominator])
                support = build_per_position_support(
                    canvas=canvas,
                    policy=SupportPolicy(
                        kind=SupportKind.EXPLICIT,
                        vocabulary_size=adapter.vocabulary_size,
                        pruning_description=f"original top-{profile['top_k']}; unrenormalized",
                    ),
                    explicit_support=rows,
                )
                state = SelectionInput(
                    grammar, canvas, (), support, adapter, EOSPolicy(EOSMode.ABSENT)
                )
                data = ProbabilityInput(state, tuple(distributions))
                construction = perf_counter() - started
                raw = {
                    "input": state_data(state),
                    "probabilities": [
                        [[p.numerator, p.denominator] for p in row] for row in distributions
                    ],
                    "normalization": normalization,
                    "source_array_sha256": hashlib.sha256(array.read_bytes()).hexdigest(),
                }
                payload = json.dumps(raw, sort_keys=True, separators=(",", ":")).encode()
                with gzip.open(args.output / f"{name}-input.json.gz", "wb") as stream:
                    stream.write(payload)
                result = run_job(data, "json", "cfg", config["scaling"])
                row = {
                    **metadata,
                    "case": name,
                    "prefix": prefix,
                    "suffix": suffix,
                    "slots": slots,
                    "input_sha256": hashlib.sha256(payload).hexdigest(),
                    "source_array_sha256": raw["source_array_sha256"],
                    "forward_seconds": forward,
                    "input_construction_seconds": construction,
                    "omitted_mass": str(data.omitted_mass),
                    "support": support.exactness_scope.to_dict(),
                    "result": result,
                }
                if result.get("sample"):
                    sample = adapter.detokenize_bytes(result["sample"])
                    json.loads(sample)
                    row["sample_utf8"] = sample.decode("utf8")
                output.write(json.dumps(row) + "\n")
                output.flush()
                print(
                    json.dumps(
                        {"case": name, "status": result["status"], "sample": row.get("sample_utf8")}
                    ),
                    flush=True,
                )


if __name__ == "__main__":
    main()
