from __future__ import annotations

import json
from pathlib import Path

import pytest

from mwpc_exact import (
    CompositionalByteLevelAdapter,
    EOSMode,
    EOSPolicy,
    EpicSelectionContext,
    ExactBackend,
    Proposal,
    SelectionInput,
    SelectionStatus,
    SupportKind,
    SupportPolicy,
    build_per_position_support,
    select_epic,
    select_exact,
)
from mwpc_exact.reference.grammar import (
    BinaryProduction,
    CnfGrammar,
    Nonterminal,
    Terminal,
    TerminalProduction,
)

regular_cover = pytest.importorskip(
    "constrained_diffusion.regular_cover",
    reason="install the pinned EPIC CPU environment",
)
epic_profiler = pytest.importorskip(
    "constrained_diffusion.fast_enfa_profiler",
    reason="install the pinned EPIC CPU environment",
)

REPOSITORY_ROOT = Path(__file__).parents[2]
ARTIFACT_PATH = REPOSITORY_ROOT / "docs" / "evidence" / "t902-baseline-preservation.json"


def axby_grammar() -> CnfGrammar:
    return CnfGrammar(
        nonterminals=(
            Nonterminal(0, "S"),
            Nonterminal(1, "TAIL1"),
            Nonterminal(2, "TAIL2"),
            Nonterminal(3, "A"),
            Nonterminal(4, "X"),
            Nonterminal(5, "B"),
            Nonterminal(6, "Y"),
        ),
        terminals=(
            Terminal(0, ord("a")),
            Terminal(1, ord("x")),
            Terminal(2, ord("b")),
            Terminal(3, ord("y")),
        ),
        start_nonterminal_id=0,
        terminal_productions=(
            TerminalProduction(0, 3, 0),
            TerminalProduction(1, 4, 1),
            TerminalProduction(2, 5, 2),
            TerminalProduction(3, 6, 3),
        ),
        binary_productions=(
            BinaryProduction(4, 0, 3, 1),
            BinaryProduction(5, 1, 4, 2),
            BinaryProduction(6, 2, 5, 6),
        ),
    )


@pytest.mark.integration
def test_common_adapter_matches_pinned_upstream_selection_and_keeps_exact_input_identical(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    artifact = json.loads(ARTIFACT_PATH.read_text(encoding="utf-8"))
    fixture = artifact["epic_saved_candidates"]
    allowed_words = frozenset(fixture["allowed_words"])

    def deterministic_cover(**kwargs: object) -> bool:
        words = kwargs["words_full"]
        assert isinstance(words, list)
        concrete_words = [word for word in words if word is not None]
        with epic_profiler.timer("regular_cover.generated_language"):
            allowed = bool(concrete_words) and all(
                word in allowed_words for word in concrete_words
            )
        with epic_profiler.timer("regular_cover.intersection"):
            return allowed

    monkeypatch.setattr(regular_cover, "cover_allows_words", deterministic_cover)
    monkeypatch.setenv("CONSTRAINED_DIFFUSION_REGULAR_COVER_EXACT", "0")
    monkeypatch.setenv("CONSTRAINED_DIFFUSION_REGULAR_COVER_MIN_BATCH", "2")
    original_selector = regular_cover.select_batch_with_regular_cover

    direct_candidates = [
        regular_cover.BatchCandidate(**candidate) for candidate in fixture["candidates"]
    ]
    direct = regular_cover.select_batch_with_regular_cover(
        words_full=fixture["words_full"],
        candidates=direct_candidates,
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

    token_text = {candidate["token_id"]: candidate["word"] for candidate in fixture["candidates"]}
    emissions: list[bytes | None] = [None] * 14
    for token_id, word in token_text.items():
        emissions[token_id] = word.encode("ascii")
    adapter = CompositionalByteLevelAdapter(tuple(emissions))
    proposals = tuple(
        Proposal(
            proposal_id=proposal_id,
            position=candidate["index"],
            token_id=candidate["token_id"],
            weight=(4.0, 30.0, 2.0, 20.0)[proposal_id],
            model_confidence=candidate["score"],
        )
        for proposal_id, candidate in enumerate(fixture["candidates"])
    )
    canvas = (None, None, None, None)
    support = build_per_position_support(
        canvas=canvas,
        policy=SupportPolicy(
            kind=SupportKind.EXPLICIT,
            vocabulary_size=adapter.vocabulary_size,
            permitted_token_ids=tuple(token_text),
            pruning_description="T1001 pinned EPIC saved-candidate fixture",
        ),
        explicit_support={
            proposal.position: (proposal.token_id,) for proposal in proposals
        },
        proposals=proposals,
    )
    selection_input = SelectionInput(
        grammar=axby_grammar(),
        canvas=canvas,
        proposals=proposals,
        support=support,
        tokenizer_adapter=adapter,
        eos_policy=EOSPolicy(EOSMode.ABSENT),
    )
    epic = select_epic(
        selection_input,
        EpicSelectionContext(
            words_full=tuple(fixture["words_full"]),
            prompt_length=0,
            cfg=object(),
            decode_token=lambda token_id: token_text[token_id],
        ),
    )
    exact = select_exact(selection_input, backend=ExactBackend.PYTHON)

    assert [(candidate.index, candidate.token_id) for candidate in direct] == [(0, 10), (2, 12)]
    assert epic.status is SelectionStatus.HEURISTIC
    assert epic.selected_proposal_ids == (0, 2)
    assert epic.score == 6.0
    assert epic.diagnostics["upstream_selected_proposal_ids"] == (0, 2)
    assert epic.diagnostics["exact_shrink_enabled"] is False
    assert not epic.witness_available

    assert exact.status is SelectionStatus.OPTIMAL
    assert exact.selected_proposal_ids == (0, 1, 2, 3)
    assert exact.score == 56.0
    assert exact.witness_token_ids == (10, 11, 12, 13)
    assert selection_input.proposals is proposals
    assert regular_cover.select_batch_with_regular_cover is original_selector

    def deterministic_exact(**kwargs: object) -> bool:
        epic_profiler.count("regular_cover.exact.calls")
        words = kwargs["words_full"]
        assert isinstance(words, list)
        concrete_words = [word for word in words if word is not None]
        return bool(concrete_words) and all(word in allowed_words for word in concrete_words)

    monkeypatch.setattr(epic_profiler, "_ENABLED", True)
    epic_profiler.reset()
    monkeypatch.setattr(regular_cover, "exact_allows_words", deterministic_exact)
    monkeypatch.setenv("CONSTRAINED_DIFFUSION_REGULAR_COVER_EXACT", "1")

    with_exact_shrink = select_epic(
        selection_input,
        EpicSelectionContext(
            words_full=tuple(fixture["words_full"]),
            prompt_length=0,
            cfg=object(),
            decode_token=lambda token_id: token_text[token_id],
        ),
    )

    assert with_exact_shrink.selected_proposal_ids == epic.selected_proposal_ids
    assert with_exact_shrink.diagnostics["exact_shrink_enabled"] is True
    assert with_exact_shrink.diagnostics["regular_cover_check_calls"] > 0
    # The pinned recursion checks the initial pair, then re-enters selection for
    # the right half after the pair fails the exact check.
    assert with_exact_shrink.diagnostics["exact_shrink_check_calls"] == 2
    assert regular_cover.select_batch_with_regular_cover is original_selector
