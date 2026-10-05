from __future__ import annotations

from dataclasses import replace
from fractions import Fraction
from itertools import combinations, product
from random import Random

import pytest
from tests.exact_commit.test_budget_bounds import state_for

from mwpc_exact import EOSMode, EOSPolicy, ExactBackend, Proposal, SolveStatus
from mwpc_exact.budget_bounds import validate_budget_batch
from mwpc_exact.budgeted_commit import budgeted_commit_frontier
from mwpc_exact.conflict_certificate import (
    check_conflict_commit,
    restrict_choices,
    retained_support,
)
from mwpc_exact.conflict_commit import ConflictCommitSolver
from mwpc_exact.reference.recognizer import recognizes_cnf


def brute(state, budget):
    best = None
    for tokens in product(*state.support.rows):
        positions = [i for i, t in enumerate(state.canvas) if t is None]
        for size in range(min(budget, len(positions)) + 1):
            for chosen in combinations(positions, size):
                try:
                    value = validate_budget_batch(
                        state, budget=budget, witness_token_ids=tokens, committed_positions=chosen
                    ).reward
                except ValueError:
                    continue
                best = value if best is None else max(best, value)
    return best


@pytest.mark.parametrize("seed", range(290000, 290032))
def test_random_exact_conflicts_equal_independent_tokens_subsets_and_resource_dp(seed):
    rng = Random(seed)
    words = [bytes(w) for w in product(b"ab", repeat=3)]
    proposals = tuple(
        Proposal(j, rng.randrange(3), rng.randrange(3), rng.randrange(9) / 8) for j in range(9)
    )
    state = state_for(
        rng.sample(words, rng.randrange(1, 9)),
        (b"a", b"b", b"a"),
        ((0, 1, 2),) * 3,
        proposals,
    )
    solver = ConflictCommitSolver(backend=ExactBackend.PYTHON)
    frontier = budgeted_commit_frontier(state, 3)
    for budget in range(4):
        result = solver.solve(state, budget)
        expected = brute(state, budget)
        assert result.status is SolveStatus.OPTIMAL, seed
        assert result.objective_value == expected == frontier[budget].objective_value, seed
        check_conflict_commit(state, result)
        assert result.oracle_calls <= (budget + 1) * result.learned_conflicts + 1, seed


def conflicting_state():
    return state_for(
        (b"ab", b"ba"),
        (b"a", b"b"),
        ((0, 1),) * 2,
        (Proposal(0, 0, 0, 5), Proposal(1, 1, 0, 4), Proposal(2, 1, 1, 2)),
    )


def test_conflict_proof_reuse_survives_changed_weights_and_budget():
    state = conflicting_state()
    solver = ConflictCommitSolver(backend=ExactBackend.PYTHON)
    first = solver.solve(state, 2)
    assert first.objective_value == 7 and first.learned_conflicts == 1
    changed = replace(
        state, proposals=tuple(replace(p, weight=p.weight * 2) for p in state.proposals)
    )
    second = solver.solve(changed, 2)
    assert second.objective_value == 14
    assert second.reused_conflicts == 1 and second.learned_conflicts == 0
    assert second.oracle_calls == 1 < first.oracle_calls
    check_conflict_commit(changed, second)


def test_fixed_matching_conflict_member_is_discharged_under_safe_reuse():
    state = conflicting_state()
    solver = ConflictCommitSolver(backend=ExactBackend.PYTHON)
    solver.solve(state, 2)
    fixed = restrict_choices(state, ((0, 0),))
    fixed = replace(fixed, proposals=tuple(p for p in state.proposals if p.position == 1))
    result = solver.solve(fixed, 1)
    assert result.reused_conflicts == 1 and result.learned_conflicts == 0
    assert result.oracle_calls == 1 and result.objective_value == 2
    check_conflict_commit(fixed, result)


def test_support_expansion_and_grammar_changes_invalidate_cache():
    original = state_for((b"ab", b"aa"), (b"a", b"b"), ((0,), (1,)), (Proposal(0, 1, 1, 2),))
    assert not retained_support(original, conflicting_state())
    solver = ConflictCommitSolver(backend=ExactBackend.PYTHON)
    bad = state_for((b"bb",), (b"a", b"b"), ((0,), (1,)), (Proposal(0, 0, 0, 3),))
    assert solver.solve(bad, 1).status is SolveStatus.INFEASIBLE_ON_SUPPORT
    expanded = state_for((b"bb",), (b"a", b"b"), ((0, 1), (1,)), (Proposal(0, 0, 0, 3),))
    result = solver.solve(expanded, 1)
    assert result.status is SolveStatus.OPTIMAL and result.objective_value == 0
    assert result.reused_conflicts == 0
    check_conflict_commit(expanded, result)


def test_infeasibility_cache_needs_no_new_oracle_and_is_not_zero_reward():
    state = state_for((b"bb",), (b"a", b"b"), ((0,), (1,)), ())
    solver = ConflictCommitSolver(backend=ExactBackend.PYTHON)
    first = solver.solve(state, 0)
    second = solver.solve(state, 2)
    assert first.status is second.status is SolveStatus.INFEASIBLE_ON_SUPPORT
    assert first.objective_value is second.objective_value is None
    assert second.oracle_calls == 0 and second.reused_conflicts == 1
    check_conflict_commit(state, second)


@pytest.mark.parametrize("budget", (0, 1, 2, 3))
def test_exact_special_token_costs_and_duplicate_rewards(budget):
    state = state_for(
        (b"a",),
        (b"a", None),
        ((0,), (1,), (1,)),
        (
            Proposal(0, 0, 0, 1),
            Proposal(1, 0, 0, 2**-54),
            Proposal(2, 1, 1, 3),
            Proposal(3, 2, 1, 2),
        ),
        eos=EOSPolicy(EOSMode.REQUIRED, (1,), 1),
    )
    result = ConflictCommitSolver(backend=ExactBackend.PYTHON).solve(state, budget)
    assert result.objective_value == brute(state, budget)
    assert result.matched_proposal_ids == (0, 1, 2, 3)
    check_conflict_commit(state, result)


def test_split_utf8_and_token_aliases_keep_original_token_identity():
    state = state_for(
        ("é".encode(),),
        (b"\xc3", b"\xa9", b"\xc3"),
        ((0, 2), (1,)),
        (Proposal(0, 0, 0, 1), Proposal(1, 0, 2, 2)),
    )
    result = ConflictCommitSolver(backend=ExactBackend.PYTHON).solve(state, 1)
    assert result.witness_token_ids == (2, 1) and result.objective_value == 2
    assert recognizes_cnf(state.grammar, (195, 169))
    check_conflict_commit(state, result)


@pytest.mark.parametrize("controls", ({"max_oracle_calls": 0}, {"timeout_seconds": 0}))
def test_exhausted_work_is_timeout_without_infeasibility_certificate(controls):
    result = ConflictCommitSolver(backend=ExactBackend.PYTHON).solve(
        conflicting_state(), 2, **controls
    )
    assert result.status is SolveStatus.TIMEOUT
    assert result.objective_value is result.certificate is None
    with pytest.raises(ValueError, match="unresolved"):
        check_conflict_commit(conflicting_state(), result)


def test_forged_master_bound_and_missing_branch_are_rejected():
    state = conflicting_state()
    result = ConflictCommitSolver(backend=ExactBackend.PYTHON).solve(state, 2)
    certificate = result.certificate
    assert certificate is not None
    root = certificate.master_nodes[0]
    for forged in (replace(root, upper_bound=Fraction(100)), replace(root, children=())):
        damaged = replace(certificate, master_nodes=(forged, *certificate.master_nodes[1:]))
        with pytest.raises(ValueError):
            check_conflict_commit(state, replace(result, certificate=damaged))
    with pytest.raises(ValueError, match="foreign"):
        check_conflict_commit(replace(state, proposals=()), result)


def test_checker_does_not_call_either_optimizer(monkeypatch):
    import mwpc_exact.budgeted_commit as resource_module
    import mwpc_exact.conflict_commit as conflict_module

    state = conflicting_state()
    result = ConflictCommitSolver(backend=ExactBackend.PYTHON).solve(state, 2)

    def forbidden(*args, **kwargs):
        raise AssertionError("independent verification called an optimizer")

    monkeypatch.setattr(conflict_module, "_master", forbidden)
    monkeypatch.setattr(resource_module, "budgeted_commit_frontier", forbidden)
    check_conflict_commit(state, result)


def test_portable_conflict_proof_roundtrip_and_independent_verification(monkeypatch):
    import json

    import mwpc_exact.conflict_commit as engine
    from mwpc_exact.conflict_proof import conflict_proof_data, verify_conflict_proof

    state = conflicting_state()
    result = ConflictCommitSolver(backend=ExactBackend.PYTHON).solve(state, 2)
    encoded = json.loads(json.dumps(conflict_proof_data(state, result)))

    def forbidden(*args, **kwargs):
        raise AssertionError("verification called optimization")

    monkeypatch.setattr(engine, "_master", forbidden)
    checked = verify_conflict_proof(encoded, expected_input=state)
    assert checked.objective_value == result.objective_value
    encoded["conflicts"][0]["choices"] = []
    with pytest.raises(ValueError):
        verify_conflict_proof(encoded, expected_input=state)


def test_experiment_metadata_preserves_immutable_mapping_without_deepcopy():
    import json
    from dataclasses import dataclass
    from types import MappingProxyType

    from scripts.exact_commit.run_conflict_real import system_data

    @dataclass(frozen=True)
    class Metadata:
        git_commit: str
        thread_environment: object

    source = Metadata("pinned", MappingProxyType({"OMP_NUM_THREADS": "1"}))
    assert json.loads(json.dumps(system_data(source))) == {
        "git_commit": "pinned",
        "thread_environment": {"OMP_NUM_THREADS": "1"},
    }


def test_two_sided_reuse_avoids_all_oracles_after_certified_conflicting_choice(monkeypatch):
    from mwpc_exact.proof_reuse import ProofReuseSolver

    state = conflicting_state()
    solver = ProofReuseSolver(backend=ExactBackend.PYTHON)
    initial = solver.solve(state, 2)
    assert initial.oracle_calls == 4

    def forbidden(*args, **kwargs):
        raise AssertionError("retained exact proof invoked a CFG oracle")

    monkeypatch.setattr(solver._solver, "solve", forbidden)
    for factor in range(1, 12):
        changed = replace(
            state, proposals=tuple(replace(p, weight=p.weight * factor) for p in state.proposals)
        )
        result = solver.solve(changed, 2)
        assert result.oracle_calls == 0 and result.objective_value == 7 * factor
        assert result.reused_conflicts == 1
        check_conflict_commit(changed, result)


def test_witness_only_ablation_does_not_secretly_reuse_conflicts():
    from mwpc_exact.proof_reuse import ProofReuseSolver

    solver = ProofReuseSolver(backend=ExactBackend.PYTHON, use_conflicts=False)
    assert solver.solve(conflicting_state(), 2).oracle_calls == 4
    assert solver.solve(conflicting_state(), 2).oracle_calls == 4


def test_feasible_witness_can_survive_expansion_but_negative_conflicts_cannot():
    from mwpc_exact.proof_reuse import ProofReuseSolver

    proposals = (Proposal(0, 0, 0, 2),)
    old = state_for((b"ab", b"aa"), (b"a", b"b"), ((0,), (1,)), proposals)
    expanded = state_for((b"ab", b"aa"), (b"a", b"b"), ((0, 1), (0, 1)), proposals)
    solver = ProofReuseSolver(backend=ExactBackend.PYTHON)
    first = solver.solve(old, 1)
    result = solver.solve(expanded, 1)
    assert result.witness_token_ids == first.witness_token_ids
    assert result.oracle_calls == 0 and result.reused_conflicts == 0
    check_conflict_commit(expanded, result)


def test_reused_witness_is_revalidated_after_fixed_slots_and_grammar_change():
    from mwpc_exact.proof_reuse import ProofReuseSolver

    solver = ProofReuseSolver(backend=ExactBackend.PYTHON)
    state = conflicting_state()
    solver.solve(state, 2)
    new = state_for((b"bb",), (b"a", b"b"), ((1,), (1,)), (), canvas=(1, None))
    answer = solver.solve(new, 1)
    assert answer.witness_token_ids == (1, 1) and answer.oracle_calls > 0
    check_conflict_commit(new, answer)
