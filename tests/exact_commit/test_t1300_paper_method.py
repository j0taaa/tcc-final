from __future__ import annotations

import json
import re
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ARTICLE = ROOT / "paper" / "main.tex"


def _article() -> str:
    return ARTICLE.read_text(encoding="utf-8")


def _first_jsonl_row(path: Path) -> dict[str, object]:
    first_line = path.read_text(encoding="utf-8").splitlines()[0]
    value = json.loads(first_line)
    assert isinstance(value, dict)
    return value


def test_t1300_method_section_has_no_implementation_placeholders() -> None:
    article = _article()
    method = article.split(
        r"\section{Implementation and Evaluation Methodology}", maxsplit=1
    )[1].split(r"\section{Preliminary and Expected Results}", maxsplit=1)[0]

    assert r"\ph{" not in method
    for stale_placeholder in (
        r"\ph{model}",
        r"\ph{grammars/tasks}",
        r"\ph{hardware}",
        r"\ph{selected tasks}",
        r"\ph{chosen lexical strategy",
        r"\ph{diagnostic/fallback policy}",
        r"\ph{fallback rule}",
        r"\ph{models, grammars, data, and hardware used}",
    ):
        assert stale_placeholder not in article


def test_repository_and_upstream_revisions_come_from_versioned_records() -> None:
    article = _article()
    audit = (ROOT / "docs" / "evidence" / "m125-completion-audit.md").read_text(
        encoding="utf-8"
    )
    upstream = (ROOT / "UPSTREAM.md").read_text(encoding="utf-8")
    audited_commit = re.search(r"Audited implementation commit:\s*\n\s*`([0-9a-f]{40})`", audit)
    upstream_commit = re.search(r"Pinned commit: `([0-9a-f]{40})`", upstream)

    assert audited_commit is not None
    assert upstream_commit is not None
    assert audited_commit.group(1) in article
    assert upstream_commit.group(1) in article
    assert "read-only EPIC submodule" in article


def test_model_support_and_decoder_fields_match_q5_config_and_code() -> None:
    article = _article()
    config = tomllib.loads(
        (ROOT / "configs" / "experiments" / "q5_structured_publication_v4.toml").read_text(
            encoding="utf-8"
        )
    )
    parameters = config["parameters"]
    support = config["support"]
    model = config["model"]

    assert model["model_id"] in article
    assert model["model_revision"] in article
    assert support["top_k"] == 8
    assert support["k_max"] == 32
    assert r"$K=8$" in article
    assert "doubling to 16 and 32" in article
    assert r"\texttt{exact\_on\_support}" in article
    assert parameters["weight_mode"] == "confidence"
    assert parameters["termination_token_ids"] == [126081, 126348]
    assert parameters["pad_token_id"] == 126081
    assert "IDs 126081 and 126348" in article
    assert config["timeouts"]["solver_seconds"] == 30.0
    assert "30 seconds total" in article

    proposal_policy = (ROOT / "src" / "mwpc_exact" / "proposal_policy.py").read_text(
        encoding="utf-8"
    )
    ranked_support = (ROOT / "src" / "mwpc_exact" / "ranked_support.py").read_text(
        encoding="utf-8"
    )
    q5_driver = (ROOT / "scripts" / "exact_commit" / "run_q5_end_to_end.py").read_text(
        encoding="utf-8"
    )
    assert '"confidence_descending_then_absolute_position_ascending"' in proposal_policy
    assert "(-scores[token_id], token_id)" in ranked_support
    assert "failure_fallback_strategy=None" in q5_driver
    assert "no non-optimal fallback" in article


def test_grammar_tokenizer_and_backend_description_matches_implementation() -> None:
    article = _article()
    tokenizer_audit = json.loads(
        (ROOT / "docs" / "evidence" / "t600-llada-tokenizer-audit.json").read_text(
            encoding="utf-8"
        )
    )

    assert tokenizer_audit["mapping"]["base_vocabulary_size"] == 126080
    assert len(tokenizer_audit["unsupported_added_tokens"]) == 269
    assert "126,080 base IDs" in article
    assert "all 269 added IDs" in article
    assert "reversing the GPT-2 ByteLevel bijection" in article
    assert "singleton calls to" in article
    assert "does not insert a lexer" in article

    for path in (
        ROOT / "src" / "mwpc_exact" / "reference" / "normalization.py",
        ROOT / "crates" / "mwpc_parser" / "src" / "parser.rs",
        ROOT / "crates" / "mwpc_parser_py" / "src" / "lib.rs",
    ):
        assert path.is_file()
    assert "removes $\\varepsilon$ and unit productions" in article
    assert "maximum-weight acyclic closure" in article
    assert r"\texttt{mwpc\_parser}" in article
    assert r"\texttt{mwpc\_parser\_py}" in article


def test_hardware_and_software_fields_match_pinned_q4_q5_metadata() -> None:
    article = _article()
    q4 = json.loads(
        (ROOT / "docs" / "evidence" / "t1255-q4-publication-summary.json").read_text(
            encoding="utf-8"
        )
    )
    q5_row = _first_jsonl_row(
        ROOT
        / "docs"
        / "artifacts"
        / "raw"
        / "m125_publication_results_v1"
        / "q5-end-to-end-rows.jsonl"
    )
    q4_metadata = q4["run_metadata"]
    q5_metadata = q5_row["run_metadata"]

    assert q4_metadata["hardware"]["cpu"]["model"].startswith("11th Gen Intel")
    assert q5_metadata["hardware"]["gpu"]["name"] == "NVIDIA GeForce RTX 3080 Ti"
    assert q5_metadata["hardware"]["gpu"]["driver_version"] == "595.84"
    assert q5_metadata["software_versions"]["cuda_runtime"] == "12.8"
    assert q5_metadata["software_versions"]["python"] == "3.11.16"
    assert q5_metadata["software_versions"]["pytorch"] == "2.8.0+cu128"
    assert q5_metadata["software_versions"]["transformers"] == "4.52.2"
    assert q5_metadata["live_dependency_versions"]["bitsandbytes"] == "0.50.1"
    for recorded_value in (
        "i7-11700K",
        "RTX 3080 Ti",
        "595.84",
        "12.8",
        "3.11.16",
        "2.8.0",
        "4.52.2",
        "1.98.0",
        "0.50.1",
    ):
        assert recorded_value in article


def test_unresolved_parent_license_is_reported_instead_of_invented() -> None:
    article = _article()
    licenses = (ROOT / "LICENSES.md").read_text(encoding="utf-8")

    assert "[LICENSE TO BE CHOSEN]" in licenses
    assert "Parent release license is pending" in article
