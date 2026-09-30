#!/usr/bin/env python3
"""Independently check an archived query trajectory without model or network."""

import argparse
import hashlib
import json
from math import fsum, isclose, isfinite
from pathlib import Path

from mwpc_research.geocoding import geocoding_catalog, read_record

ROOT = Path(__file__).resolve().parents[2]
EOS = 126081


def verify(directory):
    record = read_record(directory)
    generation, config, support = record["generation"], record["config"], record["support"]
    calls = geocoding_catalog(
        record["request"], config.get("grounding_policy", "question_spans_v1")
    )
    assert support["catalog"] == list(calls)
    assert record["grammar_sha256"] == hashlib.sha256(json.dumps(calls).encode()).hexdigest()
    emissions = {int(t): bytes(b) for t, b in support["emissions"].items()}
    paths = support["paths"]
    assert len(paths) == len(calls)
    domains = [set(path[p] for path in paths) for p in range(config["slots"])]

    def decode(tokens):
        assert len(tokens) == config["slots"]
        end = tokens.index(EOS)
        assert all(t == EOS for t in tokens[end:])
        return b"".join(emissions[t] for t in tokens[:end]).decode("utf-8")

    assert [decode(path) for path in paths] == list(calls)
    certificates = 0
    if record["policy"]["kind"] != "epic":
        canvas = [None] * config["slots"]
        for step in generation["trace"]:
            assert step["canvas_before"] == canvas
            witness = step["witness_token_ids"]
            assert decode(witness) in calls
            assert all(t in domains[p] for p, t in enumerate(witness))
            assert all(t is None or t == witness[p] for p, t in enumerate(canvas))
            native, proposals = step["production_result"], step["proposals"]
            if native is not None:
                assert all(isfinite(w) and w >= 0 for _, _, w in proposals)
                selected = [i for i, (p, t, w) in enumerate(proposals) if w > 0 and witness[p] == t]
                assert sorted(native["selected_proposal_ids"]) == selected
                assert isclose(
                    native["score"], fsum(proposals[i][2] for i in selected), abs_tol=1e-9
                )
                assert native["witness_token_ids"] == witness
                expected = (
                    "feasible_on_support"
                    if record["policy"].get("selector") == "greedy"
                    else "optimal"
                )
                assert native["status"] == expected
                certificates += 1
            for p in step["committed_positions"]:
                assert canvas[p] is None
                canvas[p] = witness[p]
        assert generation["token_ids"] == canvas
        if generation["status"] == "complete":
            assert decode(canvas) == generation["output"]
    return {
        "record_sha256": hashlib.sha256((directory / "record.json").read_bytes()).hexdigest(),
        "method": record["policy"]["name"],
        "status": record["status"],
        "model_revision": config["revision"],
        "git_commit": record["git_commit"],
        "checked_certificates": certificates,
        "api_recorded": record["api"] is not None,
        "verification": "Checksums, schema/support, finite slots, fixed positions, witness "
        "bytes and matched objective; no model inference or network access. "
        "Optimality relies on the independently tested solver, not feasibility alone.",
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--record", type=Path, default=ROOT / "docs/artifacts/demo/geocoding_v2")
    args = parser.parse_args()
    print(json.dumps(verify(args.record), indent=2))


if __name__ == "__main__":
    main()
