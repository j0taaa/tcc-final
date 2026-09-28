import pytest
from scripts.check_paper import validate_build


def test_compiled_page_count_is_required_and_bounded() -> None:
    assert validate_build("Pages: 16\n", "") == 16
    for info in ("Pages: 18\n", "Pages: 9\n", ""):
        with pytest.raises(ValueError):
            validate_build(info, "")


@pytest.mark.parametrize(
    "warning",
    [
        r"Overfull \hbox (1pt too wide)",
        r"Overfull \vbox (1pt too high)",
        "LaTeX Warning: There were undefined references.",
        "Rerun to get cross-references right",
    ],
)
def test_final_typesetting_failures_are_rejected(warning: str) -> None:
    with pytest.raises(ValueError):
        validate_build("Pages: 16\n", warning)
