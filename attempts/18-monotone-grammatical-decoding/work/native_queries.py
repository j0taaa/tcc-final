"""Best-derivation lex/greedy queries on identical maintained parser kernels.

Research contract: JSON, finite original-token slots, ABSENT EOS. Lossless
dyadic transport uses the existing Fraction/BigUint comparison throughout.
All native controls have the same independent linear JSON/path validation.
No change to the maintained public MWPC objective or certificate API.
"""

import json
from collections import Counter
from dataclasses import replace
from math import ldexp
from types import SimpleNamespace

from grammar_selectors import CachedPrefix, Recompute

from mwpc_exact.backend import ExactBackend
from mwpc_exact.eos_lattice import build_eos_lattice
from mwpc_exact.eos_policy import EOSMode
from mwpc_exact.reference.dag_parser import _reconstruct_dag_path, run_dag_cky
from mwpc_exact.rust_solver import solve_rust_dag
from mwpc_exact.token_lattice import build_token_lattice
from mwpc_exact.types import Proposal, SolveStatus


class NativeQuery:
    def initialize(self, state, backend):
        if state.eos_policy.mode is not EOSMode.ABSENT:
            raise NotImplementedError("native research decoder requires ABSENT EOS")
        self.backend = backend
        self.plan = SimpleNamespace(state=state)
        self.base = replace(
            state.support,
            permitted_token_ids=tuple(sorted({t for row in state.support.rows for t in row})),
        )

    def solve(self, canvas, proposals=()):
        self.calls += 1
        if len(proposals) > 1075:
            raise NotImplementedError("native dyadic priorities support at most 1075 proposals")
        state = self.plan.state
        support = replace(
            self.base,
            canvas=tuple(canvas),
            rows=tuple(
                (t,) if t is not None else row
                for t, row in zip(canvas, self.base.rows, strict=True)
            ),
        )
        priorities = tuple(
            Proposal(j, p, token, ldexp(1.0, -j)) for j, (p, token, _) in enumerate(proposals)
        )
        lattice = build_eos_lattice(
            token_lattice=build_token_lattice(support=support, proposals=priorities),
            adapter=state.tokenizer_adapter,
            policy=state.eos_policy,
        )
        if self.backend is ExactBackend.RUST:
            result = solve_rust_dag(state.grammar, lattice.normalized_graph, timeout_seconds=30)
            certificate = result.certificate
        else:
            result = run_dag_cky(state.grammar, lattice.normalized_graph)
            certificate = (
                _reconstruct_dag_path(result) if result.status is SolveStatus.OPTIMAL else None
            )
        if result.status is SolveStatus.INFEASIBLE_ON_SUPPORT:
            return None
        if result.status is SolveStatus.TIMEOUT:
            raise TimeoutError("native_parser_deadline")
        if result.status is SolveStatus.UNSUPPORTED:
            raise NotImplementedError("native_parser_unavailable")
        if result.status is not SolveStatus.OPTIMAL or certificate is None:
            raise RuntimeError(f"native_parser_status_{result.status}")
        path = lattice.reconstruct_normalized_path(certificate.witness_graph_edge_ids)
        lattice.validate_path(path)
        tokens = path.token_path.token_ids
        if len(tokens) != len(canvas) or any(
            token not in row or (fixed is not None and fixed != token)
            for token, row, fixed in zip(tokens, self.base.rows, canvas, strict=True)
        ):
            raise RuntimeError("native witness violated original slots/support/canvas")
        expected = [j for j, (p, token, _) in enumerate(proposals) if tokens[p] == token]
        if Counter(path.matched_proposal_ids) != Counter(expected):
            raise RuntimeError("native witness violated exact priority provenance")
        text = state.tokenizer_adapter.detokenize_bytes(tokens).decode()
        json.loads(text, parse_constant=self.reject_constant)
        return tokens

    @staticmethod
    def reject_constant(value):
        raise ValueError(f"non-JSON constant {value}")


class NativeLex(NativeQuery, Recompute):
    def __init__(self, state, *, backend=ExactBackend.RUST):
        self.initialize(state, backend)
        Recompute.__init__(self, self.plan, lex=True)


class NativePrefix(NativeQuery, CachedPrefix):
    def __init__(self, state, *, lazy=False, backend=ExactBackend.RUST):
        self.initialize(state, backend)
        Recompute.__init__(self, self.plan)
        self.current = None if lazy else self.solve(self.canvas)
        if not lazy and self.current is None:
            raise ValueError("infeasible_on_support")

    def try_token(self, position, token):
        if self.current is not None and self.current[position] == token:
            return True
        trial = list(self.canvas)
        trial[position] = token
        candidate = self.solve(trial)
        if candidate is None:
            return False
        self.current = candidate
        return True

    def transition(self, proposals, *, threshold=0.8, cap=None):
        try:
            return super().transition(proposals, threshold=threshold, cap=cap)
        except RuntimeError as error:
            if self.current is None and str(error) == "no progress despite feasible forest":
                raise ValueError("infeasible_on_support") from None
            raise
