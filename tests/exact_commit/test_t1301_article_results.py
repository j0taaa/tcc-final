from __future__ import annotations

import json
import re
from pathlib import Path

from mwpc_research.article_results import build_article_results

ROOT = Path(__file__).resolve().parents[2]
CONFIG = ROOT / "configs/analysis/m1301_article_results_v1.toml"
ARTICLE = ROOT / "paper/main.tex"
PROCESSED = ROOT / "docs/artifacts/processed/m1301_article_results_v1/article-results.json"


def test_m1301_outputs_recompute_byte_for_byte_from_pinned_evidence() -> None:
    result = build_article_results(CONFIG, repository_root=ROOT, verify_existing=True)

    assert result["artifact_id"] == "m1301_article_results_v1"
    assert result["verified_existing"] is True
    assert len(result["outputs"]) == 5


def test_article_imports_exactly_the_three_budgeted_result_elements() -> None:
    article = ARTICLE.read_text(encoding="utf-8")
    result_section = article.split(r"\section{Results and Analysis}", maxsplit=1)[1].split(
        r"\section{Limitations and Threats to Validity}", maxsplit=1
    )[0]
    table_inputs = re.findall(
        r"\\input\{generated/m1301_article_results_v1/(r\d-[^}]+\.tex)\}",
        result_section,
    )

    assert table_inputs == [
        "r1-correctness-finite-slots.tex",
        "r2-heuristic-gap.tex",
        "r3-scaling-integration.tex",
    ]
    assert r"\label{tab:resultados}" not in article
    assert r"\label{tab:cronograma}" not in article
    assert "Preliminary and Expected Results" not in article
    assert "T1203 tables and figures remain" not in article
    assert "fuller T1203 artifacts remain in the repository" in article


def test_generated_summary_preserves_scientific_interpretation() -> None:
    summary = json.loads(PROCESSED.read_text(encoding="utf-8"))
    r1 = summary["r1"]
    r2 = summary["r2"]
    q4 = summary["r3"]["q4"]
    q5 = summary["r3"]["q5"]

    assert r1["failed_case_count"] == 0
    assert r1["independent_certificate_validation_count"] == 334
    families = {row["family"]: row for row in r1["families"]}
    assert "confidence_interval_method" not in families["canonical"]["agreement"]
    assert "confidence_interval_method" not in families["exhaustive"]["agreement"]
    assert "confidence_interval_method" not in families["overall"]["agreement"]
    assert families["randomized"]["agreement"]["confidence_interval_method"] == "wilson_score"

    assert r2["real_snapshot_count"] == 24
    assert r2["real_non_singleton_support_count"] == 0
    assert r2["real_timeout_count"] == 0
    assert r2["real_failure_count"] == 0

    assert q4["measurement_count"] == 540
    assert q4["backend_mismatch_count"] == 0
    assert q4["timeout_count"] == 0
    assert q4["censored_count"] == 0
    assert q4["graph_size_scale_interpretation"] == ("compound_support_width_and_token_byte_length")
    assert q4["backends"]["python"]["dominant_named_component"] == ("byte_lattice_expansion")
    assert q4["backends"]["rust"]["dominant_recorded_component"] == (
        "unattributed_measurement_overhead"
    )

    assert q5["contract_failure_count"] == 0
    assert q5["exact_optimizer_step_count"] == 60
    for task in q5["tasks"].values():
        assert task["constrained_valid_count"] == task["constrained_generation_count"]
        assert task["epic_maximum_batch_size"] > 1
        assert task["epic_regular_cover_selector_calls"] > 0
        assert task["exact_certificate_count"] == 30
        assert task["strategies"]["exact"]["fallback_event_count"] == 0


def test_result_analysis_does_not_promote_smokes_or_null_results() -> None:
    article = ARTICLE.read_text(encoding="utf-8")
    result_section = article.split(r"\section{Results and Analysis}", maxsplit=1)[1].split(
        r"\section{Limitations and Threats to Validity}", maxsplit=1
    )[0]

    for required_caution in (
        "illustrative, not typical-model estimates",
        "cannot estimate a representative gap",
        "compound graph axis does not isolate a cause or represent code workloads",
        "not broad quality or workload superiority",
        r"configured \texttt{exact\_on\_support}, not full-vocabulary exactness",
    ):
        assert required_caution in result_section
    assert "runtime-scaling.svg" not in result_section
    assert "heuristic-gap-distribution.svg" not in result_section
