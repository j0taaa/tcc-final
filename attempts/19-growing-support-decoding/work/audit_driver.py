"""Opt-in Torch toy driver audit; numerical timings are never evidence of benefit."""

import argparse
import hashlib
import json
from pathlib import Path

import torch

from mwpc_exact.tokenizer_bytes import CompositionalByteLevelAdapter

from .generation import run_case
from .test_correctness import fixture


class Fake(torch.nn.Module):
    def __init__(self):
        super().__init__()
        self.anchor = torch.nn.Parameter(torch.zeros(()))

    def forward(self, input_ids, timesteps):
        step = int((input_ids != 255).sum())
        logits = torch.full((1, 3, 256), -20.0)
        base = 3 + 17 * step
        logits[:, :, base : base + 16] = 1.0
        logits[0, 0, 0], logits[0, 1, 2], logits[0, 2, 1] = 2.0, 2.0, 2.0
        logits[0, 0, 1], logits[0, 1, base], logits[0, 2, 0] = 3.0, 3.0, 3.0
        return logits


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(args.output)
    torch.set_num_threads(1)
    torch.set_flush_denormal(False)
    work = Path(__file__).resolve().parent
    protocol = json.loads((work / "protocol.json").read_text())
    methods = protocol["methods"] + [
        "rust_lex",
        "rust_cached_prefix",
        "rust_lazy_prefix",
        "rust_count_warm",
        "root_lex",
        "root_cached_prefix",
        "root_lazy_prefix",
        "root_count_warm",
        "root_speculative",
        "rust_speculative",
        "sat_reserve_32",
        "sat_reserve_64",
        "sat_reserve_128",
    ]
    state, _ = fixture()
    from mwpc_exact.reference.json_grammar import json_source_grammar

    adapter = CompositionalByteLevelAdapter((b"[", b"]", *(b"0" for _ in range(254))))
    results, first = [], None
    for method in methods:
        row = run_case(
            Fake(),
            adapter,
            json_source_grammar(),
            state.grammar,
            dict(key="1" * 64, tokens=(0, 2, 1)),
            3,
            method,
            dict(mask_token_id=255),
            protocol,
            trim=True,
            compressed=True,
            native_grammar=state.grammar,
            rooted=True,
            growing=True,
        )
        if row["status"] != "complete":
            raise AssertionError((method, row["status"], row.get("reason")))
        record = {k: row[k] for k in ("tokens", "support_rows", "trace", "output")}
        if first is None:
            first = record
        elif record != first:
            raise AssertionError((method, "driver trajectory diverged"))
        results.append(
            dict(
                method=method,
                status=row["status"],
                engine_preparations=row.get("engine_preparations", 0),
            )
        )
    evidence = dict(
        kind="driver correctness only, fake logits, no performance/model experiment",
        checks=results,
        trajectory=first,
        source_sha256={
            p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in work.glob("*.py")
        },
    )
    args.output.write_text(json.dumps(evidence, indent=2) + "\n")
    print(f"{len(results)} complete identical adaptive toy-driver trajectories")


if __name__ == "__main__":
    main()
