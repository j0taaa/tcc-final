from __future__ import annotations

from scripts.exact_commit.run_q1_correctness import _grammar_hashes as q1_grammar_hashes
from scripts.exact_commit.run_q2_heuristic_gap import _grammar_hashes as q2_grammar_hashes

from mwpc_exact import ProposalWeightMode
from mwpc_research.q1_correctness import configured_q1_cases
from mwpc_research.q2_gap import configured_q2_instances


def test_q1_driver_hashes_the_grammar_nested_in_each_case_instance() -> None:
    cases = configured_q1_cases(seed_start=1101, random_case_count=1)

    hashes = q1_grammar_hashes(cases)

    assert len(hashes) == len(cases)
    assert all(len(value) == 64 for value in hashes)


def test_q2_driver_hashes_each_benchmark_grammar() -> None:
    instances = configured_q2_instances(
        seed_start=1102,
        weight_modes=(ProposalWeightMode.UNIT,),
    )

    hashes = q2_grammar_hashes(instances)

    assert len(hashes) == len(instances)
    assert all(len(value) == 64 for value in hashes)
