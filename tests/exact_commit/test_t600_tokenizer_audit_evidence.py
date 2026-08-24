from __future__ import annotations

import json
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
EVIDENCE_PATH = REPOSITORY_ROOT / "docs/evidence/t600-llada-tokenizer-audit.json"


def _evidence() -> dict[str, object]:
    value = json.loads(EVIDENCE_PATH.read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


def test_pinned_t600_audit_passes_complete_base_vocabulary_checks() -> None:
    evidence = _evidence()
    mapping = evidence["mapping"]
    random_sequences = evidence["random_sequences"]

    assert evidence["result"] == "pass"
    assert evidence["model_id"] == "GSAI-ML/LLaDA-8B-Instruct"
    assert evidence["tokenizer_revision"] == "08b83a6feb34df1a6011b80c3c00c7563e963b07"
    assert isinstance(mapping, dict)
    assert mapping["ordinary_token_id_range"] == [0, 126080]
    assert mapping["unsupported_added_token_id_range"] == [126080, 126349]
    assert mapping["empty_ordinary_emissions"] == 0
    assert mapping["byte_values_with_single_token_representative"] == 256
    assert isinstance(random_sequences, dict)
    assert random_sequences["seed"] == 600
    assert random_sequences["case_count"] == 20000
    assert random_sequences["full_decode_matches_lossy_raw_bytes"] is True
    assert (
        random_sequences["strict_utf8_cases"] + random_sequences["invalid_utf8_cases"]
        == random_sequences["case_count"]
    )


def test_pinned_t600_audit_lists_every_unsupported_added_token() -> None:
    evidence = _evidence()
    unsupported = evidence["unsupported_added_tokens"]

    assert isinstance(unsupported, list)
    assert [item["token_id"] for item in unsupported] == list(range(126080, 126349))
    assert all(item["ordinary_grammar_emission"] == "unsupported" for item in unsupported)
    assert all(item["backend_special"] is True for item in unsupported)
    assert all(item["decode_skipping_specials"] == "" for item in unsupported)


def test_pinned_t600_audit_keeps_singleton_decode_counterexample() -> None:
    evidence = _evidence()
    counterexample = evidence["singleton_decode_counterexample"]

    assert isinstance(counterexample, dict)
    assert counterexample == {
        "concatenated_singleton_decode": "\N{REPLACEMENT CHARACTER}\N{REPLACEMENT CHARACTER}",
        "full_decode": "\N{WOMAN}",
        "raw_bytes_hex": "f09f91a9",
        "token_ids": [47681, 102],
        "token_pieces": ["ðŁĳ", "©"],
    }


def test_pinned_tokenizer_artifact_hashes_are_immutable() -> None:
    evidence = _evidence()

    assert evidence["tokenizer_files"] == {
        "special_tokens_map.json": {
            "sha256": "e9f1f0f6fa133da3169ae69b1969c51cced047a900050893d7a0711c6bd063aa"
        },
        "tokenizer.json": {
            "sha256": "071eb20fe7bd601550b1b7838ff696d6c93b88f51257f753303d3df23163c381"
        },
        "tokenizer_config.json": {
            "sha256": "b9a6102c39a4f42f47f0d63fc6cee58a2381199d90f2a4f39b3f6871f32b4119"
        },
    }
