#!/usr/bin/env python3
"""Audit the pinned LLaDA tokenizer and emit the versioned T600 evidence."""

from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import random
import subprocess
import sys
import tomllib
from pathlib import Path
from typing import Any

from mwpc_exact.tokenizer_bytes import CompositionalByteLevelAdapter

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def _relative_path(path: Path) -> str:
    try:
        return str(path.relative_to(REPOSITORY_ROOT))
    except ValueError:
        return str(path)


def _case_result(
    tokenizer: Any, adapter: CompositionalByteLevelAdapter, text: str
) -> dict[str, Any]:
    token_ids = tokenizer.encode(text, add_special_tokens=False)
    raw_bytes = adapter.detokenize_bytes(token_ids)
    decoded = tokenizer.decode(
        token_ids,
        skip_special_tokens=False,
        clean_up_tokenization_spaces=False,
    )
    singleton_decoded = "".join(
        tokenizer.decode(
            [token_id],
            skip_special_tokens=False,
            clean_up_tokenization_spaces=False,
        )
        for token_id in token_ids
    )
    _require(decoded == raw_bytes.decode("utf-8", errors="replace"), "curated decode mismatch")
    return {
        "input": text,
        "token_ids": token_ids,
        "raw_bytes_hex": raw_bytes.hex(),
        "decoded": decoded,
        "input_equals_decoded": text == decoded,
        "singleton_decode_equals_full_decode": singleton_decoded == decoded,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--config",
        type=Path,
        default=REPOSITORY_ROOT / "configs/exact_commit/t600_llada_tokenizer.toml",
    )
    parser.add_argument(
        "--local-files-only",
        action="store_true",
        help="fail instead of downloading the pinned tokenizer files",
    )
    arguments = parser.parse_args()

    try:
        from huggingface_hub import hf_hub_download
        from transformers import AutoTokenizer
    except ImportError as error:
        raise SystemExit(
            "T600 audit dependencies are missing; run `make bootstrap-epic` first"
        ) from error

    config_path = arguments.config.resolve()
    config_bytes = config_path.read_bytes()
    config = tomllib.loads(config_bytes.decode("utf-8"))
    model_id = str(config["model_id"])
    revision = str(config["tokenizer_revision"])

    tokenizer = AutoTokenizer.from_pretrained(
        model_id,
        revision=revision,
        local_files_only=arguments.local_files_only,
        trust_remote_code=False,
    )
    base_vocabulary_size = int(tokenizer.vocab_size)
    total_vocabulary_size = len(tokenizer)
    _require(
        type(tokenizer).__name__ == config["expected_tokenizer_class"],
        "unexpected tokenizer class",
    )
    _require(
        base_vocabulary_size == config["expected_base_vocabulary_size"],
        "unexpected base vocabulary size",
    )
    _require(
        total_vocabulary_size == config["expected_total_vocabulary_size"],
        "unexpected total vocabulary size",
    )

    policy = config["policy"]
    ordinary_start = int(policy["ordinary_token_id_start"])
    ordinary_end = int(policy["ordinary_token_id_end_exclusive"])
    unsupported_start = int(policy["unsupported_added_token_id_start"])
    unsupported_end = int(policy["unsupported_added_token_id_end_exclusive"])
    _require((ordinary_start, ordinary_end) == (0, base_vocabulary_size), "bad ordinary range")
    _require(
        (unsupported_start, unsupported_end)
        == (base_vocabulary_size, total_vocabulary_size),
        "bad unsupported range",
    )

    token_pieces: list[str | None] = []
    for token_id in range(base_vocabulary_size):
        piece = tokenizer.convert_ids_to_tokens(token_id)
        _require(isinstance(piece, str), f"missing base token piece at ID {token_id}")
        token_pieces.append(piece)
    token_pieces.extend(None for _ in range(base_vocabulary_size, total_vocabulary_size))
    adapter = CompositionalByteLevelAdapter.from_token_pieces(token_pieces)

    one_byte_representatives: dict[int, int] = {}
    for token_id in range(base_vocabulary_size):
        emission = adapter.token_bytes(token_id)
        if len(emission) == 1:
            one_byte_representatives.setdefault(emission[0], token_id)
    _require(set(one_byte_representatives) == set(range(256)), "not every raw byte is represented")
    byte_representative_ids = [one_byte_representatives[value] for value in range(256)]
    _require(
        adapter.detokenize_bytes(byte_representative_ids) == bytes(range(256)),
        "single-byte representative sequence mismatch",
    )

    backend = json.loads(tokenizer.backend_tokenizer.to_str())
    decoder = backend.get("decoder")
    model = backend.get("model")
    _require(isinstance(decoder, dict) and decoder.get("type") == "ByteLevel", "not ByteLevel")
    _require(isinstance(model, dict) and model.get("type") == "BPE", "not BPE")
    model_summary = {
        key: model.get(key)
        for key in (
            "type",
            "dropout",
            "unk_token",
            "continuing_subword_prefix",
            "end_of_word_suffix",
            "fuse_unk",
            "byte_fallback",
            "ignore_merges",
        )
    }

    added_decoder = tokenizer.backend_tokenizer.get_added_tokens_decoder()
    expected_added_ids = set(range(base_vocabulary_size, total_vocabulary_size))
    _require(set(added_decoder) == expected_added_ids, "added-token IDs are not contiguous")
    added_tokens = []
    for token_id in sorted(added_decoder):
        token = added_decoder[token_id]
        decoded_with_specials = tokenizer.decode(
            [token_id], skip_special_tokens=False, clean_up_tokenization_spaces=False
        )
        decoded_without_specials = tokenizer.decode(
            [token_id], skip_special_tokens=True, clean_up_tokenization_spaces=False
        )
        added_tokens.append(
            {
                "token_id": token_id,
                "content": token.content,
                "backend_special": bool(token.special),
                "configured_special_id": token_id in tokenizer.all_special_ids,
                "decode_with_specials": decoded_with_specials,
                "decode_skipping_specials": decoded_without_specials,
                "lstrip": bool(token.lstrip),
                "rstrip": bool(token.rstrip),
                "normalized": bool(token.normalized),
                "single_word": bool(token.single_word),
                "ordinary_grammar_emission": "unsupported",
            }
        )
    _require(all(item["backend_special"] for item in added_tokens), "non-special added token found")
    _require(
        all(item["decode_skipping_specials"] == "" for item in added_tokens),
        "an added token survived skip_special_tokens=True",
    )

    curated_inputs = {
        "ascii": "hello world",
        "whitespace": " \t\n\r  x",
        "unicode_nfc": "café Ω 中文",
        "unicode_nfd": "cafe\u0301 A\u030a",
        "emoji_and_joiner": "👩🏽\u200d💻🙂",
    }
    curated = {
        name: _case_result(tokenizer, adapter, text) for name, text in curated_inputs.items()
    }

    counterexample_ids = [int(value) for value in config["singleton_counterexample_ids"]]
    counterexample_raw = adapter.detokenize_bytes(counterexample_ids)
    counterexample_full = tokenizer.decode(
        counterexample_ids,
        skip_special_tokens=False,
        clean_up_tokenization_spaces=False,
    )
    counterexample_singletons = "".join(
        tokenizer.decode(
            [token_id], skip_special_tokens=False, clean_up_tokenization_spaces=False
        )
        for token_id in counterexample_ids
    )
    _require(counterexample_full != counterexample_singletons, "singleton counterexample vanished")
    _require(
        counterexample_full == counterexample_raw.decode("utf-8", errors="replace"),
        "counterexample full decode mismatch",
    )

    seed = int(config["random_seed"])
    case_count = int(config["random_case_count"])
    max_length = int(config["random_max_sequence_length"])
    random_generator = random.Random(seed)
    strict_utf8_cases = 0
    invalid_utf8_cases = 0
    singleton_decode_mismatches = 0
    random_case_digest = hashlib.sha256()
    invalid_examples: list[dict[str, Any]] = []
    singleton_examples: list[dict[str, Any]] = []
    for _ in range(case_count):
        token_ids = [
            random_generator.randrange(base_vocabulary_size)
            for _ in range(random_generator.randint(0, max_length))
        ]
        raw_bytes = adapter.detokenize_bytes(token_ids)
        full_decoded = tokenizer.decode(
            token_ids,
            skip_special_tokens=False,
            clean_up_tokenization_spaces=False,
        )
        singleton_decoded = "".join(
            tokenizer.decode(
                [token_id],
                skip_special_tokens=False,
                clean_up_tokenization_spaces=False,
            )
            for token_id in token_ids
        )
        _require(
            full_decoded == raw_bytes.decode("utf-8", errors="replace"),
            "full decoder differs from lossy rendering of raw ByteLevel bytes",
        )
        try:
            strict_decoded = raw_bytes.decode("utf-8")
        except UnicodeDecodeError:
            invalid_utf8_cases += 1
            if len(invalid_examples) < 3:
                invalid_examples.append({"token_ids": token_ids, "raw_bytes_hex": raw_bytes.hex()})
        else:
            strict_utf8_cases += 1
            _require(strict_decoded == full_decoded, "strict UTF-8 full decode mismatch")
        if singleton_decoded != full_decoded:
            singleton_decode_mismatches += 1
            if len(singleton_examples) < 3:
                singleton_examples.append(
                    {
                        "token_ids": token_ids,
                        "raw_bytes_hex": raw_bytes.hex(),
                        "full_decoded": full_decoded,
                        "singleton_decoded": singleton_decoded,
                    }
                )
        random_case_digest.update(json.dumps(token_ids, separators=(",", ":")).encode("ascii"))
        random_case_digest.update(b"\n")
    _require(strict_utf8_cases + invalid_utf8_cases == case_count, "random count mismatch")

    tokenizer_files = {}
    for filename in config["tokenizer_files"]:
        downloaded = Path(
            hf_hub_download(
                repo_id=model_id,
                filename=str(filename),
                revision=revision,
                local_files_only=arguments.local_files_only,
            )
        )
        tokenizer_files[str(filename)] = {"sha256": _sha256(downloaded)}

    output_path = REPOSITORY_ROOT / config["output"]["summary"]
    evidence = {
        "schema_version": int(config["schema_version"]),
        "audit": "t600_llada_tokenizer_byte_semantics",
        "result": "pass",
        "model_id": model_id,
        "tokenizer_revision": revision,
        "git_commit": subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=REPOSITORY_ROOT,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip(),
        "config_path": _relative_path(config_path),
        "config_sha256": hashlib.sha256(config_bytes).hexdigest(),
        "software": {
            "python": sys.version.split()[0],
            "transformers": importlib.metadata.version("transformers"),
            "tokenizers": importlib.metadata.version("tokenizers"),
            "huggingface_hub": importlib.metadata.version("huggingface-hub"),
        },
        "tokenizer_files": tokenizer_files,
        "backend": {
            "tokenizer_class": type(tokenizer).__name__,
            "model": model_summary,
            "decoder": decoder,
            "normalizer": backend.get("normalizer"),
            "pre_tokenizer": backend.get("pre_tokenizer"),
        },
        "mapping": {
            "name": policy["mapping"],
            "definition": "concatenate inverse GPT-2 ByteLevel characters for each base token",
            "base_vocabulary_size": base_vocabulary_size,
            "total_vocabulary_size": total_vocabulary_size,
            "ordinary_token_id_range": [ordinary_start, ordinary_end],
            "unsupported_added_token_id_range": [unsupported_start, unsupported_end],
            "empty_ordinary_emissions": 0,
            "byte_values_with_single_token_representative": len(one_byte_representatives),
            "single_byte_representative_token_ids": byte_representative_ids,
            "model_byte_fallback": model.get("byte_fallback"),
            "unicode_rendering": policy["unicode_rendering"],
        },
        "random_sequences": {
            "seed": seed,
            "case_count": case_count,
            "max_sequence_length": max_length,
            "token_id_sequence_sha256": random_case_digest.hexdigest(),
            "strict_utf8_cases": strict_utf8_cases,
            "invalid_utf8_cases": invalid_utf8_cases,
            "singleton_decode_mismatches": singleton_decode_mismatches,
            "invalid_utf8_examples": invalid_examples,
            "singleton_mismatch_examples": singleton_examples,
            "full_decode_matches_lossy_raw_bytes": True,
        },
        "singleton_decode_counterexample": {
            "token_ids": counterexample_ids,
            "token_pieces": [
                tokenizer.convert_ids_to_tokens(value) for value in counterexample_ids
            ],
            "raw_bytes_hex": counterexample_raw.hex(),
            "full_decode": counterexample_full,
            "concatenated_singleton_decode": counterexample_singletons,
        },
        "curated_sequences": curated,
        "special_tokens_map": tokenizer.special_tokens_map,
        "configured_special_token_ids": tokenizer.all_special_ids,
        "unsupported_added_tokens": added_tokens,
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(evidence, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"output": _relative_path(output_path), "result": "pass"}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
