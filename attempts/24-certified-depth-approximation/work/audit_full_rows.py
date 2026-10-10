"""Exhaustive full original-V depth/certificate oracle after disclosed clamps."""

import argparse
import hashlib
import json
from fractions import Fraction
from math import prod
from pathlib import Path

from mwpc_exact.tokenizer_bytes import CompositionalByteLevelAdapter

from .certificate import CounterTable
from .handoff import OverflowFrontier
from .posterior import Weights
from .stack_control import StackPosterior
from .table import LexerTable
from .test_correctness import json_depth, prepare


def main():
    import numpy as np

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--capture", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(args.output)
    metadata = json.loads((args.capture / "metadata.json").read_text())
    adapter = CompositionalByteLevelAdapter.from_token_pieces(
        json.loads((args.capture / "vocabulary.json").read_text())
    )
    table, rows, candidates = LexerTable(adapter), [], 0
    counter = CounterTable(table)
    for doc in metadata["selected"]:
        name = doc["key"] + "-4"
        case = json.loads((args.capture / (name + ".json")).read_text())
        if (
            hashlib.sha256((args.capture / (name + ".npy")).read_bytes()).hexdigest()
            != case["probabilities_sha256"]
        ):
            raise ValueError("captured prediction changed")
        probabilities = np.load(args.capture / (name + ".npy"), allow_pickle=False)
        for index, position in enumerate(case["positions"]):
            canvas = list(doc["tokens"])
            canvas[position] = None
            raw = [None] * len(canvas)
            raw[position] = probabilities[index]
            weights = Weights(raw, canvas, adapter.vocabulary_size)
            prefix = adapter.detokenize_bytes(doc["tokens"][:position])
            suffix = adapter.detokenize_bytes(doc["tokens"][position + 1 :])
            depths = []
            for word in adapter.emissions:
                candidates += 1
                try:
                    if word is None:
                        raise ValueError("nontext token")
                    value = json.loads(
                        (prefix + word + suffix).decode("utf8"),
                        parse_constant=lambda x: (_ for _ in ()).throw(ValueError(x)),
                    )
                    depths.append(json_depth(value))
                except (ValueError, UnicodeDecodeError):
                    depths.append(None)
            full = sum(weights.at(position, t) for t, d in enumerate(depths) if d is not None)
            for depth in (0, 1, 2, 3, 4, 6, 8):
                expected = tuple(
                    weights.at(position, t) if d is not None and d <= depth else 0
                    for t, d in enumerate(depths)
                )
                total = sum(expected)
                prepared = prepare(table, canvas, depth, track_overflow=True)
                posterior = StackPosterior(prepared, weights)
                if posterior.total != total:
                    raise RuntimeError("independent full-V bounded mass differs")
                if total and posterior.marginals()[0][position] != expected:
                    raise RuntimeError("independent full-V bounded marginal differs")
                frontier = OverflowFrontier(prepared, weights)
                bound, _ = frontier.handoff(counter)
                actual_tail = Fraction(full - total, prod(weights.denominators))
                if not actual_tail <= bound <= frontier.mass:
                    raise RuntimeError("independent full-V certificate undercounts tail")
                rows.append(
                    dict(
                        case=doc["key"],
                        position=position,
                        depth=depth,
                        bounded_total=str(total),
                        tail=str(actual_tail),
                        upper_handoff=str(bound),
                        upper_grammar_hit=str(frontier.mass),
                        status="exact_bounded_agreement_and_sound_upper",
                    )
                )
    args.output.write_text(
        json.dumps(
            dict(
                scope="Correctness only; one-hole clamps; no new forward/usefulness claim",
                capture_commit=metadata["commit"],
                rows=rows,
                original_candidates=candidates,
                oracle="Strict UTF8/json.loads, independent recursive depth; every original token",
            ),
            indent=2,
        )
        + "\n"
    )
    print(
        json.dumps(dict(comparisons=len(rows), original_candidates=candidates, status="agreement"))
    )


if __name__ == "__main__":
    main()
