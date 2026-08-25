from __future__ import annotations

import tomllib
from pathlib import Path

from scripts.exact_commit.run_t904_llada_live_smoke import (
    _literal_grammar,
    _validate_generated_tokens,
)

from mwpc_exact import CompositionalByteLevelAdapter
from mwpc_exact.epic_adapter.llada import PINNED_LLADA_PROFILE

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = REPOSITORY_ROOT / "configs/exact_commit/t904_llada_live_smoke.toml"


def test_t904_config_freezes_live_revision_strategies_and_support_scope() -> None:
    config = tomllib.loads(CONFIG_PATH.read_text(encoding="utf-8"))

    assert config["schema_version"] == 1
    assert config["purpose"] == "live_model_correctness_smoke_not_a_benchmark"
    assert config["model_id"] == PINNED_LLADA_PROFILE.model_id
    assert config["model_revision"] == PINNED_LLADA_PROFILE.tokenizer_revision
    assert config["tokenizer_revision"] == PINNED_LLADA_PROFILE.tokenizer_revision
    assert config["generation"]["strategies"] == ["serial", "epic", "exact"]
    assert config["exact"]["exactness_scope"] == "exact_on_support"
    assert config["exact"]["termination_token_ids"] == list(
        PINNED_LLADA_PROFILE.eos_policy.termination_token_ids
    )
    assert config["exact"]["pad_token_id"] == PINNED_LLADA_PROFILE.eos_policy.pad_token_id
    assert config["quantization"] == {
        "implementation": "bitsandbytes",
        "load_in_4bit": True,
        "four_bit_quant_type": "nf4",
        "four_bit_compute_dtype": "bfloat16",
        "four_bit_use_double_quant": True,
    }
    assert len(config["checkpoint_shard_names"]) == len(config["checkpoint_shard_sizes_bytes"]) == 6
    assert sum(config["checkpoint_shard_sizes_bytes"]) == 16_031_197_112
    assert (
        config["expected_model_vocabulary_size"]
        > config["expected_tokenizer_total_vocabulary_size"]
    )


def test_t904_independent_validation_passes_tuple_labels_to_cnf_recognizer() -> None:
    target = b"0"
    validation = _validate_generated_tokens(
        (0, PINNED_LLADA_PROFILE.eos_policy.termination_token_ids[0]),
        tokenizer_adapter=CompositionalByteLevelAdapter((b"0",)),
        grammar=_literal_grammar(target),
        target=target,
    )

    assert validation["content_bytes_hex"] == target.hex()
    assert validation["independent_grammar_valid"] is True
