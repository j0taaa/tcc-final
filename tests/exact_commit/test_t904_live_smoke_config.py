from __future__ import annotations

import hashlib
import json
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
EVIDENCE_PATH = REPOSITORY_ROOT / "docs/evidence/t904-llada-live-smoke.json"
T904_DRIVER_COMMIT = "40f228a83c5d30679023ba38248eb8a9c5ab7f98"


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


def test_t904_live_artifact_pins_model_quantization_and_memory_limitation() -> None:
    config_bytes = CONFIG_PATH.read_bytes()
    config = tomllib.loads(config_bytes.decode("utf-8"))
    evidence = json.loads(EVIDENCE_PATH.read_text(encoding="utf-8"))

    assert evidence["status"] == "PASS"
    assert evidence["purpose"] == "live_model_correctness_smoke_not_a_benchmark"
    assert evidence["benchmark_claim"] is False
    assert evidence["repository"] == {
        "git_clean_at_start": True,
        "git_commit": T904_DRIVER_COMMIT,
        "upstream_epic_commit": "5b1b31098f34ed3691d2a9f4aae14fdf5839d072",
    }
    assert evidence["config"]["sha256"] == hashlib.sha256(config_bytes).hexdigest()
    assert evidence["model"]["model_id"] == config["model_id"]
    assert evidence["model"]["resolved_revision"] == config["expected_resolved_revision"]
    assert evidence["model"]["checkpoint_safetensors_bytes"] == sum(
        config["checkpoint_shard_sizes_bytes"]
    )
    assert evidence["tokenizer"]["requested_revision"] == config["tokenizer_revision"]
    assert evidence["tokenizer"]["model_output_padding_rows"] == 115
    assert evidence["execution"]["quantization"] == config["quantization"]
    assert evidence["execution"]["local_files_only"] is True
    assert evidence["memory_assessment"]["unquantized_bf16_load_attempted"] is False
    assert (
        evidence["model"]["checkpoint_safetensors_bytes"]
        > evidence["memory_assessment"]["gpu_total_memory_bytes"]
    )


def test_t904_live_artifact_validates_all_modes_and_exact_certificate() -> None:
    evidence = json.loads(EVIDENCE_PATH.read_text(encoding="utf-8"))
    runs = {run["strategy"]: run for run in evidence["strategy_runs"]}

    assert set(runs) == {"serial", "epic", "exact"}
    for run in runs.values():
        assert run["complete"] is True
        assert run["validation"]["content_bytes_hex"] == "30"
        assert run["validation"]["independent_grammar_valid"] is True
    assert runs["serial"]["implementation"] == "upstream_llada_serial_constrained_loop"
    assert runs["serial"]["regular_cover_batch_enabled"] is False
    assert runs["epic"]["implementation"] == "upstream_llada_regular_cover_enabled_loop"
    assert runs["epic"]["regular_cover_batch_enabled"] is True
    assert runs["epic"]["regular_cover_selector_calls"] == 0
    assert runs["epic"]["serial_fallback_remains_available"] is True

    exact = runs["exact"]["outcome"]["decoder_step"]["solver_result"]
    certificate = exact["diagnostics"]["certificate_validation"]
    assert exact["status"] == "optimal"
    assert exact["exactness_scope"]["kind"] == "top_k"
    assert exact["exactness_scope"]["top_k"] == 1
    assert exact["diagnostics"]["exactness_name"] == "exact_on_support"
    assert exact["witness_token_ids"] == runs["exact"]["generated_token_ids"]
    assert exact["witness_terminal_labels"] == [ord("0")]
    assert exact["witness_graph_edge_ids"]
    assert exact["objective_value"] == certificate["recomputed_objective"]
    assert set(exact["selected_proposal_ids"]) == set(
        certificate["recomputed_selected_proposal_ids"]
    )
    assert certificate["is_valid"] is True
    assert certificate["issues"] == []
