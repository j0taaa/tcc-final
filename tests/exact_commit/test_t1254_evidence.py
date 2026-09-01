from __future__ import annotations

import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path

from mwpc_exact import BenchmarkInstance

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
SNAPSHOT_PATH = (
    REPOSITORY_ROOT
    / "docs/artifacts/raw/m125_publication_results_v1/q2-real-snapshots.jsonl"
)
ROW_PATH = (
    REPOSITORY_ROOT
    / "docs/artifacts/raw/m125_publication_results_v1/q2-real-gap-rows.jsonl"
)
CAPTURE_PATH = REPOSITORY_ROOT / "docs/evidence/t1254-q2-snapshot-capture.json"
SUMMARY_PATH = REPOSITORY_ROOT / "docs/evidence/t1254-q2-real-gap-summary.json"
SYNTHETIC_TABLE_PATH = (
    REPOSITORY_ROOT
    / "paper/generated/t1203_final_results_v1/heuristic-gap-table.tex"
)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _jsonl(path: Path) -> list[dict[str, object]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def test_t1254_capture_pins_24_real_common_snapshots() -> None:
    capture = json.loads(CAPTURE_PATH.read_text(encoding="utf-8"))
    snapshots = _jsonl(SNAPSHOT_PATH)

    assert _sha256(SNAPSHOT_PATH) == (
        "443eda3bf4a7eb9d82c474fa9f0f3a9a11227779a07dc623e92c7f97c6f185b2"
    )
    assert _sha256(CAPTURE_PATH) == (
        "e55750d3e7f4af672dfeee20c1d1351219b07ddaedc40f100358e5ba0702a4f7"
    )
    assert capture["snapshot_count"] == len(snapshots) == 24
    assert set(capture["pair_counts"].values()) == {4}
    assert len(capture["pair_counts"]) == 6
    metadata = capture["run_metadata"]
    assert metadata["git_commit"] == "fc2ba5507589d41ffd482f532061323b9c756100"
    assert metadata["git_dirty"] is False
    assert metadata["metadata_integrity"]["publication_blockers"] == []

    instances = [BenchmarkInstance.from_dict(snapshot) for snapshot in snapshots]
    assert [instance.fingerprint for instance in instances] == capture["snapshot_sha256"]
    assert len({instance.fingerprint for instance in instances}) == 24
    assert Counter(instance.metadata["task_id"] for instance in instances) == {
        "json_x_zero": 12,
        "fenced_add_dsl": 12,
    }
    ranks: defaultdict[tuple[str, int], set[int]] = defaultdict(set)
    for instance in instances:
        ranks[(str(instance.metadata["task_id"]), int(instance.metadata["seed"]))].add(
            int(instance.metadata["selected_state_rank"])
        )
        assert instance.metadata["contains_model_weights"] is False
        assert instance.metadata["support_interpretation"] == (
            "explicit_primary_proposal_plus_target_witness"
        )
        assert instance.expected_metadata["exactness_scope"] == "exact_on_support"
    assert len(ranks) == 6
    assert all(values == {0, 1, 2, 3} for values in ranks.values())


def test_t1254_replay_keeps_all_statuses_certificates_and_limitations_explicit() -> None:
    rows = _jsonl(ROW_PATH)
    summary = json.loads(SUMMARY_PATH.read_text(encoding="utf-8"))

    assert _sha256(ROW_PATH) == (
        "917aa8640ffea67305439d0526432f118801afee97932e0c120e26b7419386f7"
    )
    assert _sha256(SUMMARY_PATH) == (
        "dfa49cb7e9c7747475bebf89b28aedd64086f7368f1cda365a446e0c37745ec4"
    )
    assert len(rows) == 24
    assert len({row["snapshot_sha256"] for row in rows}) == 24
    assert all(row["success"] is True for row in rows)
    assert all(row["support_specification"]["kind"] == "explicit" for row in rows)
    assert all(row["run_metadata"]["exactness"]["scope"] == "exact_on_support" for row in rows)
    assert all(row["support_combination_count"] == 1 for row in rows)

    for row in rows:
        selectors = row["selector_results"]
        assert selectors["greedy_exact_feasibility"]["status"] == "feasible_on_support"
        assert selectors["epic_regular_cover"]["status"] == "heuristic"
        assert selectors["epic_regular_cover"]["diagnostics"][
            "regular_cover_selector_calls"
        ] == 1
        assert selectors["exact_mwpc"]["status"] == "optimal"
        validation = row["independent_exact_validation"]
        assert validation["certificate_valid"] is True
        assert validation["grammar_witness_valid"] is True
        assert validation["objective_value"] == validation["recomputed_objective_value"]
        assert sorted(validation["selected_proposal_ids"]) == sorted(
            validation["recomputed_selected_proposal_ids"]
        )

    assert summary["raw_sha256"] == _sha256(ROW_PATH)
    assert summary["run_metadata"]["git_commit"] == (
        "5b6d9349adec9ac910c7bb0601d92d7e5de6f956"
    )
    assert summary["run_metadata"]["synthetic_rows_included"] is False
    assert summary["failure_count"] == 0
    assert summary["timeout_count"] == 0
    assert summary["zero_optimum_count"] == 0
    assert summary["all_exact_certificates_independently_valid"] is True
    assert summary["non_singleton_support_count"] == 0
    assert summary["empirical_interpretation"] == (
        "execution_alignment_check_all_supports_singleton_after_deduplication"
    )
    assert summary["sampling_inference"] == "none_non_iid_task_seed_state_corpus"
    equality = summary["comparisons"]["epic_regular_cover"]["equality"]
    assert equality["inference_policy"] == "no_interval_non_iid_task_seed_state_corpus"
    assert "confidence_interval_lower" not in equality


def test_t1254_old_q2_rows_remain_explicitly_synthetic_and_illustrative() -> None:
    table = SYNTHETIC_TABLE_PATH.read_text(encoding="utf-8")
    decision = (
        REPOSITORY_ROOT / "docs/decisions/0016-publication-evidence-tier.md"
    ).read_text(encoding="utf-8")

    assert "configured synthetic states" in table
    assert "Illustrative canonical/adversarial behavior" in decision
    assert "representative mean EPIC/serial gap" in decision
