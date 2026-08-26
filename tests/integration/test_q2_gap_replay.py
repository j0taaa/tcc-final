from __future__ import annotations

import pytest

from mwpc_exact import ExactBackend, ProposalWeightMode, replay_benchmark_instance
from mwpc_research.q2_gap import configured_q2_instances, run_q2_gap_instances

pytest.importorskip(
    "constrained_diffusion.regular_cover",
    reason="install the pinned EPIC CPU environment",
)
pytest.importorskip(
    "rustformlang.cfg",
    reason="install the pinned EPIC rustformlang binding",
)


@pytest.mark.integration
def test_q2_cases_replay_through_real_pinned_epic(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("CONSTRAINED_DIFFUSION_REGULAR_COVER_EXACT", "1")
    monkeypatch.setenv("CONSTRAINED_DIFFUSION_REGULAR_COVER_MIN_BATCH", "2")
    instances = configured_q2_instances(
        seed_start=1102,
        weight_modes=(ProposalWeightMode.UNIT, ProposalWeightMode.CONFIDENCE),
    )

    result = run_q2_gap_instances(
        instances,
        replay=lambda instance: replay_benchmark_instance(
            instance,
            backend=ExactBackend.PYTHON,
            brute_force_max_completions=64,
        ),
        run_metadata={"test": "pinned-epic"},
    )

    assert result.failed_cases == 0, result.summary_dict()
    rows = {(row.common_instance_id, row.weight_mode.value): row for row in result.records}
    assert rows[("all-compatible", "unit")].comparisons["epic_regular_cover"] == {
        "exact_selector": "exact_mwpc",
        "heuristic_selector": "epic_regular_cover",
        "exact_score": 3.0,
        "heuristic_score": 3.0,
        "exact_cardinality": 3,
        "heuristic_cardinality": 3,
        "absolute_gap": 0.0,
        "relative_gap": 0.0,
        "score_equal": True,
    }
    adversarial = rows[("adversarial-one-vs-two", "unit")]
    assert adversarial.selector_results["exact_mwpc"]["score"] == 2.0
    assert adversarial.selector_results["greedy_exact_feasibility"]["score"] == 1.0
    assert adversarial.selector_results["epic_regular_cover"]["score"] == 0.0
