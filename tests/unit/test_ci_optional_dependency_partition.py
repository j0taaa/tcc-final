from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_ci_guards_and_exercises_combined_exact_epic_tests() -> None:
    q2_test = (ROOT / "tests" / "exact_commit" / "test_q2_real_gap.py").read_text(
        encoding="utf-8"
    )
    q5_test = (ROOT / "tests" / "exact_commit" / "test_q5_end_to_end.py").read_text(
        encoding="utf-8"
    )
    workflow = (ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")

    assert 'pytest.importorskip("mwpc_parser_py"' in q2_test
    assert 'pytest.importorskip("rustformlang"' in q2_test
    assert 'pytest.importorskip(\n        "rustformlang.fa.bytes_dfa"' in q5_test
    assert "Run combined exact and EPIC tests" in workflow
    assert "tests/exact_commit/test_q2_real_gap.py" in workflow
    assert "tests/exact_commit/test_q5_end_to_end.py" in workflow
    assert workflow.index("Build exact Rust binding for Q2") < workflow.index(
        "Run combined exact and EPIC tests"
    )

