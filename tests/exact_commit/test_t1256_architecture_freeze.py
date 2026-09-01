from __future__ import annotations

from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
DECISION_PATH = (
    REPOSITORY_ROOT
    / "docs/decisions/0021-freeze-experiment-artifact-architecture.md"
)


def test_t1256_freezes_existing_layers_and_forbids_generic_replacements() -> None:
    decision = DECISION_PATH.read_text(encoding="utf-8")
    normalized = " ".join(decision.split())

    for existing_layer in (
        "experiment TOML configuration",
        "run-metadata contract",
        "raw and processed artifact directories",
        "statistical-summary utilities",
        "final-artifact generation paths",
    ):
        assert existing_layer in normalized
    for forbidden_layer in (
        "plugin system",
        "general workflow engine",
        "another artifact schema",
        "generic charting framework",
        "database",
        "dependency-injection layer",
        "second statistical library",
        "second raw/processed convention",
    ):
        assert forbidden_layer in normalized


def test_t1256_keeps_validation_fixtures_out_of_scientific_result_inputs() -> None:
    decision = DECISION_PATH.read_text(encoding="utf-8")
    normalized = " ".join(decision.split())
    final_config = (
        REPOSITORY_ROOT / "configs/analysis/t1203_final_artifacts_v1.toml"
    ).read_text(encoding="utf-8")
    article = (REPOSITORY_ROOT / "paper/main.tex").read_text(encoding="utf-8")

    assert "T1201's two-row artifact inventory" in normalized
    assert "T1202's synthetic formula artifact" in normalized
    assert "only currently assembled scientific-result bundle" in normalized
    for fixture_id in ("t1201", "t1202"):
        assert fixture_id not in final_config.lower()
        assert fixture_id not in article.lower()
    assert "t1203_final_results_v1" in final_config
