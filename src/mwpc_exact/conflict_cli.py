"""Solve a saved dLLM state or independently verify its portable certificate."""

from __future__ import annotations

import argparse
import gzip
import json
from pathlib import Path

from mwpc_exact.budget_proof import fraction_data
from mwpc_exact.conflict_proof import read_state, verify_conflict_proof
from mwpc_exact.reference.grammar import CnfGrammar
from mwpc_exact.serialization import _selection_input_from_dict


def _read(path: Path) -> object:
    raw = path.read_bytes()
    return json.loads(gzip.decompress(raw) if path.suffix == ".gz" else raw)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--input", type=Path, help="original token state JSON/JSON.gz (or archived benchmark input)"
    )
    parser.add_argument("--budget", type=int, default=2)
    parser.add_argument("--proof", type=Path, help="new portable certificate output")
    parser.add_argument("--verify", type=Path, help="certificate to verify without optimization")
    args = parser.parse_args()
    if args.verify:
        result = verify_conflict_proof(_read(args.verify))
    else:
        if args.input is None or args.proof is None:
            parser.error("solving requires --input and a new --proof path")
        from mwpc_exact.conflict_commit import ConflictCommitSolver
        from mwpc_exact.conflict_proof import conflict_proof_data

        data = _read(args.input)
        if not isinstance(data, dict):
            raise ValueError("input must be an original-token state object")
        state = (
            read_state(data)
            if "selection" in data
            else _selection_input_from_dict(
                data["selection_input"], CnfGrammar.from_dict(data["grammar"]["cnf"])
            )
        )
        result = ConflictCommitSolver().solve(state, args.budget)
        if result.certificate is None:
            raise RuntimeError(f"unresolved solve: {result.status}")
        encoded = (json.dumps(conflict_proof_data(state, result), sort_keys=True) + "\n").encode()
        args.proof.parent.mkdir(parents=True, exist_ok=True)
        with args.proof.open("xb") as output:
            output.write(gzip.compress(encoded, mtime=0) if args.proof.suffix == ".gz" else encoded)
    print(
        json.dumps(
            {
                "status": result.status.value,
                "objective_value": fraction_data(result.objective_value),
                "committed_positions": result.committed_positions,
                "committed_proposal_ids": result.committed_proposal_ids,
                "witness_token_ids": result.witness_token_ids,
                "oracle_calls": result.oracle_calls,
                "certificate_verified": True,
                "exactness_scope": result.exactness_scope.to_dict(),
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
