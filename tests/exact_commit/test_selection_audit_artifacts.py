"""The current manuscript must not silently accept drift in an M19 derivative."""

from pathlib import Path

import pytest
from scripts.exact_commit.build_selection_audit import (
    OUTPUT,
    expected_outputs,
    verify_outputs,
)


@pytest.fixture(scope="module")
def regenerated() -> dict[str, str]:
    return expected_outputs()


def test_current_selection_audit_derivatives_match_verified_raw_data(regenerated):
    verify_outputs(OUTPUT, regenerated)


@pytest.mark.parametrize("filename", ("summary.json", "audit-values.tex", "audit-timing.tex"))
@pytest.mark.parametrize("change", ("missing", "modified"))
def test_selection_audit_rejects_missing_or_modified_derivative(
    tmp_path: Path, regenerated, filename: str, change: str
) -> None:
    for name, content in regenerated.items():
        (tmp_path / name).write_text(content, encoding="utf-8")
    changed = tmp_path / filename
    if change == "missing":
        changed.unlink()
    else:
        changed.write_text(changed.read_text() + "unaudited change\n")
    with pytest.raises(ValueError, match=filename):
        verify_outputs(tmp_path, regenerated)
