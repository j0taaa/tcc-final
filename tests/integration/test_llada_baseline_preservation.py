from __future__ import annotations

import hashlib
import json
from pathlib import Path
from types import SimpleNamespace
from typing import Any, ClassVar

import pytest

from mwpc_exact import CommitStrategy, DecoderStrategyConfig, dispatch_commit_strategy

torch = pytest.importorskip("torch", reason="install the pinned EPIC CPU environment")
llada_baseline = pytest.importorskip(
    "constrained_diffusion.eval.dllm.models.llada.generate_constrained",
    reason="install the pinned EPIC CPU environment",
)
regular_cover_baseline = pytest.importorskip(
    "constrained_diffusion.regular_cover",
    reason="install the pinned EPIC CPU environment",
)

REPOSITORY_ROOT = Path(__file__).parents[2]
ARTIFACT_PATH = REPOSITORY_ROOT / "docs" / "evidence" / "t902-baseline-preservation.json"
UPSTREAM_ROOT = REPOSITORY_ROOT / "vendor" / "EPIC-Decoding"


def _artifact() -> dict[str, Any]:
    return json.loads(ARTIFACT_PATH.read_text(encoding="utf-8"))


def _git_blob_sha1(path: Path) -> str:
    payload = path.read_bytes()
    header = f"blob {len(payload)}\0".encode()
    return hashlib.sha1(header + payload, usedforsecurity=False).hexdigest()


class _SavedLogitsModel:
    device = torch.device("cpu")

    def __init__(self, logits: list[list[float]]) -> None:
        self._logits = torch.tensor([logits], dtype=torch.float64)

    def __call__(self, _token_ids: object) -> SimpleNamespace:
        return SimpleNamespace(logits=self._logits.clone())


class _FixtureTokenizer:
    special_tokens_map: ClassVar[dict[str, str]] = {"eos_token": "<eos>"}

    def __init__(self, token_text: dict[str, str]) -> None:
        self._token_text = token_text

    def decode(self, token_id: object) -> str:
        if hasattr(token_id, "item"):
            token_id = token_id.item()
        return self._token_text[str(int(token_id))]

    def batch_decode(self, token_ids: object) -> list[str]:
        return [self.decode(token_id) for token_id in token_ids]


def _run_upstream_serial(fixture: dict[str, Any]) -> list[dict[str, object]]:
    generation = fixture["generation"]
    output: list[dict[str, object]] = []
    iterator = llada_baseline.generate(
        _SavedLogitsModel(fixture["logits"]),
        torch.tensor([fixture["prompt_token_ids"]], dtype=torch.long),
        _FixtureTokenizer(fixture["token_text"]),
        None,
        None,
        len(fixture["prompt_token_ids"]),
        steps=generation["steps"],
        gen_length=generation["generation_length"],
        block_length=generation["block_length"],
        temperature=generation["temperature"],
        mask_id=fixture["mask_token_id"],
        constrain=generation["constrain"],
    )
    for token_ids, resamples, complete in iterator:
        output.append(
            {
                "token_ids": token_ids.clone().tolist(),
                "resample_count": len(resamples),
                "complete": complete,
            }
        )
    return output


def _run_upstream_epic(fixture: dict[str, Any]) -> list[dict[str, object]]:
    candidates = [regular_cover_baseline.BatchCandidate(**item) for item in fixture["candidates"]]
    selected = regular_cover_baseline.select_batch_with_regular_cover(
        words_full=fixture["words_full"],
        candidates=candidates,
        prompt_len=0,
        cfg=object(),
        lex_map=None,
        terminals=[],
        prelex=None,
        single_token_lexing=None,
        inject_gap_size=0,
        max_total_injections=0,
        subtokens={},
        supertokens={},
        strip_chars=None,
    )
    return [
        {
            "index": candidate.index,
            "token_id": candidate.token_id,
            "word": candidate.word,
            "score": candidate.score,
        }
        for candidate in selected
    ]


@pytest.mark.integration
def test_pinned_baseline_sources_match_the_comparison_artifact() -> None:
    source_blobs = _artifact()["upstream"]["source_blobs"]

    assert {
        relative_path: _git_blob_sha1(UPSTREAM_ROOT / relative_path)
        for relative_path in source_blobs
    } == source_blobs


@pytest.mark.integration
def test_serial_dispatch_calls_original_generator_and_preserves_saved_logits_output() -> None:
    fixture = _artifact()["serial_saved_logits"]
    original_serial = llada_baseline.generate
    direct_output = _run_upstream_serial(fixture)

    dispatched_output = dispatch_commit_strategy(
        DecoderStrategyConfig(strategy=CommitStrategy.SERIAL),
        serial=lambda: _run_upstream_serial(fixture),
        epic=lambda: pytest.fail("serial dispatch called the EPIC baseline"),
        exact=lambda _config: pytest.fail("serial dispatch called the exact strategy"),
    )

    assert llada_baseline.generate is original_serial
    assert direct_output == fixture["expected_direct_and_dispatched_yields"]
    assert dispatched_output == direct_output


@pytest.mark.integration
def test_epic_dispatch_calls_existing_regular_cover_and_preserves_selection(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fixture = _artifact()["epic_saved_candidates"]
    allowed_words = frozenset(fixture["allowed_words"])

    def deterministic_cover(**kwargs: object) -> bool:
        words = kwargs["words_full"]
        assert isinstance(words, list)
        concrete_words = [word for word in words if word is not None]
        return bool(concrete_words) and all(word in allowed_words for word in concrete_words)

    monkeypatch.setattr(regular_cover_baseline, "cover_allows_words", deterministic_cover)
    monkeypatch.setenv("CONSTRAINED_DIFFUSION_REGULAR_COVER_EXACT", "0")
    original_selector = regular_cover_baseline.select_batch_with_regular_cover
    direct_output = _run_upstream_epic(fixture)

    dispatched_output = dispatch_commit_strategy(
        DecoderStrategyConfig(strategy=CommitStrategy.EPIC),
        serial=lambda: pytest.fail("EPIC dispatch called the serial baseline"),
        epic=lambda: _run_upstream_epic(fixture),
        exact=lambda _config: pytest.fail("EPIC dispatch called the exact strategy"),
    )

    assert regular_cover_baseline.select_batch_with_regular_cover is original_selector
    assert direct_output == fixture["expected_direct_and_dispatched_selection"]
    assert dispatched_output == direct_output
