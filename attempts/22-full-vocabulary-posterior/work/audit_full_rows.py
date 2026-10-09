"""Independent exhaustive full-V oracle after clamps, NOT a utility benchmark."""

import argparse
import hashlib
import json
from pathlib import Path

from mwpc_exact.tokenizer_bytes import CompositionalByteLevelAdapter

from .posterior import Weights
from .table import LexerTable
from .test_correctness import KINDS, evaluate, prepare


def main():
    import numpy as np

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--capture", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    metadata = json.loads((args.capture / "metadata.json").read_text())
    adapter = CompositionalByteLevelAdapter.from_token_pieces(
        json.loads((args.capture / "vocabulary.json").read_text())
    )
    table = LexerTable(adapter)
    rows = []
    for doc in metadata["selected"]:
        name = doc["key"] + "-4"
        case = json.loads((args.capture / (name + ".json")).read_text())
        probabilities = np.load(args.capture / (name + ".npy"), allow_pickle=False)
        if (
            hashlib.sha256((args.capture / (name + ".npy")).read_bytes()).hexdigest()
            != case["probabilities_sha256"]
        ):
            raise ValueError("captured prediction changed")
        for index, position in enumerate(case["positions"]):
            # Clamp other original holes to external document solely to enable
            # exhaustive correctness enumeration, never a benchmark/quality win.
            canvas = list(doc["tokens"])
            canvas[position] = None
            raw = [None] * len(canvas)
            raw[position] = probabilities[index]
            weights = Weights(raw, canvas, adapter.vocabulary_size)
            prefix = adapter.detokenize_bytes(doc["tokens"][:position])
            suffix = adapter.detokenize_bytes(doc["tokens"][position + 1 :])
            accepted = []
            for word in adapter.emissions:
                if word is None:
                    accepted.append(False)
                    continue
                try:
                    json.loads(
                        (prefix + word + suffix).decode("utf8"),
                        parse_constant=lambda v: (_ for _ in ()).throw(ValueError(v)),
                    )
                except (ValueError, UnicodeDecodeError):
                    accepted.append(False)
                else:
                    accepted.append(True)
            expected = tuple(weights.at(position, t) if ok else 0 for t, ok in enumerate(accepted))
            total = sum(expected)
            if not total:
                raise ValueError("no positive oracle completion")
            for kind in KINDS:
                prepared = prepare(table, canvas, kind)
                posterior = evaluate(prepared, weights)
                numerators, actual = posterior.marginals()
                if actual != total or numerators[position] != expected:
                    raise RuntimeError(
                        f"independent full-V oracle mismatch: {name}/{position}/{kind}"
                    )
                if any(
                    row != {fixed: total}
                    for p, (row, fixed) in enumerate(zip(numerators, canvas, strict=True))
                    if p != position
                ):
                    raise RuntimeError("fixed marginal changed")
                rows.append(
                    dict(
                        case=doc["key"],
                        position=position,
                        kind=kind,
                        original_candidates=len(accepted),
                        valid=sum(accepted),
                        total=str(total),
                        status="exact_agreement",
                    )
                )
                del posterior, prepared, numerators
    args.output.write_text(
        json.dumps(
            dict(
                scope=(
                    "Correctness after disclosed clamps; no new NN forward or timing/quality claim"
                ),
                capture_commit=metadata["commit"],
                rows=rows,
                oracle="Every original token recognized independently by strict UTF8/json.loads",
            ),
            indent=2,
        )
        + "\n"
    )
    print(json.dumps(dict(rows=len(rows), status="exact_agreement")))


if __name__ == "__main__":
    main()
