from __future__ import annotations

from mwpc_exact import SolveStatus
from mwpc_exact.reference.brute_force import exhaustive_completion_oracle
from mwpc_exact.reference.random_instances import (
    RandomTokenAlignedInstance,
    generate_random_instance,
)


def completion_status(instance: RandomTokenAlignedInstance) -> SolveStatus:
    return exhaustive_completion_oracle(
        grammar=instance.grammar,
        per_position_support=instance.per_position_support,
        canvas=instance.canvas,
        proposals=instance.proposals,
        terminal_labels_by_token_id=instance.terminal_labels_by_token_id,
    ).status


def test_seed_reproduces_the_exact_same_case() -> None:
    first = generate_random_instance(1729)
    second = generate_random_instance(1729)

    assert first == second
    assert first.to_json() == second.to_json()


def test_instances_round_trip_through_versioned_json() -> None:
    instance = generate_random_instance(42)

    restored = RandomTokenAlignedInstance.from_json(instance.to_json())

    assert restored == instance
    assert restored.to_dict() == instance.to_dict()


def test_failure_fixture_can_be_written_and_replayed_offline(tmp_path) -> None:
    instance = generate_random_instance(99)
    path = tmp_path / "seed-99.json"

    instance.write_json(path)
    restored = RandomTokenAlignedInstance.read_json(path)

    assert restored == instance


def test_seed_family_contains_recursive_and_acyclic_grammars() -> None:
    assert generate_random_instance(0).grammar_kind == "recursive"
    assert generate_random_instance(1).grammar_kind == "acyclic"


def test_configured_seeds_include_feasible_and_infeasible_instances() -> None:
    statuses = {completion_status(generate_random_instance(seed)) for seed in range(8)}

    assert statuses == {SolveStatus.OPTIMAL, SolveStatus.INFEASIBLE_ON_SUPPORT}


def test_generated_cases_have_conflicts_integer_weights_and_duplicates() -> None:
    instance = generate_random_instance(2)
    position_zero = tuple(proposal for proposal in instance.proposals if proposal.position == 0)

    assert len({proposal.token_id for proposal in position_zero}) >= 2
    assert all(proposal.weight.is_integer() for proposal in instance.proposals)
    choices = [(proposal.position, proposal.token_id) for proposal in instance.proposals]
    assert len(set(choices)) < len(choices)
