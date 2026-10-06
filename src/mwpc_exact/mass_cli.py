"""Verify a portable predictive-mass proof and sample only at a certified tolerance."""

from __future__ import annotations

import argparse
import gzip
import json
from fractions import Fraction
from pathlib import Path
from random import Random

from mwpc_exact.budget_proof import fraction_data
from mwpc_exact.conflict_proof import read_state
from mwpc_exact.mass_certificate import PosteriorScope, verify_mass_proof
from mwpc_exact.serde import _mapping


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verify", type=Path, required=True)
    parser.add_argument("--sample", action="store_true")
    parser.add_argument(
        "--scope", choices=[s.value for s in PosteriorScope], default=PosteriorScope.FULL.value
    )
    parser.add_argument("--max-tv", type=Fraction, default=Fraction(1, 20))
    parser.add_argument("--seed", type=int, default=300000)
    args = parser.parse_args()
    raw = args.verify.read_bytes()
    value = json.loads(gzip.decompress(raw) if args.verify.suffix == ".gz" else raw)
    checked = verify_mass_proof(value)
    scope = PosteriorScope(args.scope)
    output: dict[str, object] = {
        "verification": "PASS",
        "reference": "frozen_mean_field_conditioned_on_declared_grammar",
        "reference_scope": scope.value,
        "valid_mass_lower": fraction_data(checked.lower),
        "valid_mass_upper": fraction_data(checked.upper(scope)),
        "original_omitted_mass": fraction_data(checked.omitted),
        "outside_valid_upper": fraction_data(checked.outside_valid_upper),
        "conditional_tv_bound": fraction_data(checked.tv_bound(scope)),
    }
    if args.sample:
        try:
            witness = checked.sample(Random(args.seed), scope=scope, max_tv=args.max_tv)
        except ValueError as error:
            output["sampling_status"] = "refused"
            output["reason"] = str(error)
        else:
            state = read_state(_mapping(value, "proof")["input"])
            output.update(
                sampling_status="accepted",
                witness_token_ids=witness,
                decoded=state.tokenizer_adapter.detokenize_bytes(witness).decode("utf-8"),
            )
    print(json.dumps(output, sort_keys=True, allow_nan=False))


if __name__ == "__main__":
    main()
