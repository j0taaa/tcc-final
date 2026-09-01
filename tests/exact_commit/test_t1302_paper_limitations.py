from __future__ import annotations

import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ARTICLE = ROOT / "paper" / "main.tex"
Q5_CONFIG = ROOT / "configs" / "experiments" / "q5_structured_publication_v4.toml"


def _article() -> str:
    return ARTICLE.read_text(encoding="utf-8")


def _limitations() -> str:
    return _article().split(
        r"\section{Limitations and Threats to Validity}", maxsplit=1
    )[1].split(r"\section{Conclusion and Future Work}", maxsplit=1)[0]


def test_t1302_states_every_required_limit_without_conflating_statuses() -> None:
    limitations = _limitations()

    for required_boundary in (
        r"\texttt{exact\_on\_support}",
        "not full-vocabulary exact",
        "does not optimize the future trajectory",
        "raw ByteLevel byte stream",
        "no programming-language lexer",
        "constrains syntax only",
        "not types, references, execution, or tests",
        r"\texttt{TIMEOUT} leaves feasibility and optimality unknown",
        r"\texttt{INFEASIBLE\_ON\_SUPPORT}",
        "exhaust time or memory",
    ):
        assert required_boundary in limitations


def test_correspondence_table_maps_all_theorems_and_decoder_propositions() -> None:
    limitations = _limitations()

    assert r"\label{tab:theorem-code}" in limitations
    for claim in ("Thm.~1", "Thm.~2", "Thm.~3(i)", "Thm.~3(ii)", "Thm.~3(iii)", "Thm.~4"):
        assert claim in limitations
    assert "Props.~1--2" in limitations

    for enforcement_point in (
        r"\texttt{types.py}",
        r"\texttt{reference/normalization.py}",
        r"\texttt{ranked\_support.py}",
        r"\texttt{tokenizer\_bytes.py}",
        r"\texttt{validator.py}",
        r"\texttt{eos\_lattice.py}",
        r"\texttt{decoder.py}",
    ):
        assert enforcement_point in limitations


def test_q5_theorem_premises_match_config_and_the_exact_execution_path() -> None:
    article = _article()
    limitations = _limitations()
    config = tomllib.loads(Q5_CONFIG.read_text(encoding="utf-8"))
    parameters = config["parameters"]

    assert config["exactness"] == {
        "scope": "exact_on_support",
        "guarantee": "per_step",
        "require_independent_certificate": True,
    }
    assert config["support"]["top_k"] == 8
    assert config["support"]["k_max"] == 32
    assert config["timeouts"]["solver_seconds"] == 30.0
    assert parameters["weight_mode"] == "confidence"
    assert parameters["eos_mode"] == "required"
    assert parameters["remasking"] == "low_confidence"
    assert parameters["termination_token_ids"] == [126081, 126348]
    assert parameters["pad_token_id"] == 126081

    q5_driver = (
        ROOT / "scripts" / "exact_commit" / "run_q5_end_to_end.py"
    ).read_text(encoding="utf-8")
    exact_path = q5_driver.split("def _prepare_exact_call(", maxsplit=1)[1].split(
        "def _monitor_process_resources(", maxsplit=1
    )[0]
    assert "failure_fallback_strategy=None" in exact_path
    assert '"exact generation made no progress"' in q5_driver
    assert "remasking=parameters.remasking" not in exact_path

    assert "low-confidence ranking" in article
    assert "still-masked positions" in article
    assert "exact commits never remask" in article
    assert (
        "does not remask exact commitments" in limitations
    ), "the upstream remasking label must not silently weaken the exact termination premise"


def test_correspondence_names_real_enforcement_files() -> None:
    for relative in (
        "src/mwpc_exact/types.py",
        "src/mwpc_exact/reference/normalization.py",
        "src/mwpc_exact/ranked_support.py",
        "src/mwpc_exact/tokenizer_bytes.py",
        "src/mwpc_exact/validator.py",
        "src/mwpc_exact/eos_lattice.py",
        "src/mwpc_exact/decoder.py",
    ):
        assert (ROOT / relative).is_file()


def test_optional_objectives_are_not_presented_as_implemented_behavior() -> None:
    article = _article()

    assert "no lexicographic secondary objective is implemented or claimed" in article
    assert "a cardinality dimension inside the parser remains an unimplemented extension" in article
