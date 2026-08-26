from __future__ import annotations

import json
from dataclasses import dataclass
from typing import cast

import pytest

import mwpc_exact.evaluation.epic_regular_cover as epic_module
from mwpc_exact import (
    CompositionalByteLevelAdapter,
    EOSMode,
    EOSPolicy,
    EpicSelectionContext,
    ExactBackend,
    Proposal,
    SelectionInput,
    SelectionStatus,
    SelectorKind,
    SupportKind,
    SupportPolicy,
    build_per_position_support,
    select_epic_regular_cover,
    select_exact_mwpc,
)
from mwpc_exact.reference.grammar import (
    BinaryProduction,
    CnfGrammar,
    Nonterminal,
    Terminal,
    TerminalProduction,
)


@dataclass(frozen=True)
class FakeCandidate:
    index: int
    token_id: int
    word: object
    score: float = 0.0


def ab_grammar() -> CnfGrammar:
    return CnfGrammar(
        nonterminals=(
            Nonterminal(0, "S"),
            Nonterminal(1, "A"),
            Nonterminal(2, "B"),
        ),
        terminals=(Terminal(0, ord("a")), Terminal(1, ord("b"))),
        start_nonterminal_id=0,
        terminal_productions=(
            TerminalProduction(0, 1, 0),
            TerminalProduction(1, 2, 1),
        ),
        binary_productions=(BinaryProduction(2, 0, 1, 2),),
    )


def common_input(
    proposals: tuple[Proposal, ...],
    *,
    rows: tuple[tuple[int, ...], ...] = ((0, 1), (0, 1)),
) -> SelectionInput:
    adapter = CompositionalByteLevelAdapter((b"a", b"b"))
    canvas = (None, None)
    support = build_per_position_support(
        canvas=canvas,
        policy=SupportPolicy(
            kind=SupportKind.EXPLICIT,
            vocabulary_size=adapter.vocabulary_size,
            pruning_description="T1001 deterministic EPIC adapter fixture",
        ),
        explicit_support=dict(enumerate(rows)),
        proposals=proposals,
    )
    return SelectionInput(
        grammar=ab_grammar(),
        canvas=canvas,
        proposals=proposals,
        support=support,
        tokenizer_adapter=adapter,
        eos_policy=EOSPolicy(EOSMode.ABSENT),
    )


def context() -> EpicSelectionContext:
    return EpicSelectionContext(
        words_full=("prompt", None, None),
        prompt_length=1,
        cfg=object(),
        decode_token=lambda token_id: ("a", "b")[token_id],
    )


def fake_runtime(
    selector: object,
    *,
    minimum_batch_size: int = 2,
    exact_shrink_enabled: bool = True,
    profiler_enabled: bool = False,
    snapshots: tuple[dict[str, object], ...] = (),
) -> epic_module._EpicRuntime:
    snapshot_iterator = iter(snapshots)
    return epic_module._EpicRuntime(
        candidate_factory=cast(epic_module._CandidateFactory, FakeCandidate),
        select_batch=cast(epic_module._BatchSelector, selector),
        minimum_batch_size=lambda: minimum_batch_size,
        exact_shrink_enabled=lambda: exact_shrink_enabled,
        profiler_enabled=lambda: profiler_enabled,
        profiler_snapshot=lambda: next(snapshot_iterator),
    )


def install_runtime(
    monkeypatch: pytest.MonkeyPatch,
    runtime: epic_module._EpicRuntime,
) -> None:
    monkeypatch.setattr(epic_module, "_load_pinned_epic_runtime", lambda: runtime)


def test_epic_and_exact_consume_identical_proposals_but_keep_distinct_guarantees(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    selection_input = common_input(
        (
            Proposal(7, 0, 0, weight=2.0, model_confidence=0.9),
            Proposal(8, 1, 1, weight=5.0, model_confidence=0.8),
        )
    )
    captured: dict[str, object] = {}

    def select_all(**kwargs: object) -> object:
        captured.update(kwargs)
        return kwargs["candidates"]

    install_runtime(monkeypatch, fake_runtime(select_all))

    epic = select_epic_regular_cover(selection_input, context())
    exact = select_exact_mwpc(selection_input, backend=ExactBackend.PYTHON)

    candidates = captured["candidates"]
    assert isinstance(candidates, list)
    assert [(candidate.index, candidate.token_id, candidate.score) for candidate in candidates] == [
        (1, 0, 0.9),
        (2, 1, 0.8),
    ]
    assert epic.selector is SelectorKind.EPIC
    assert epic.status is SelectionStatus.HEURISTIC
    assert epic.selected_proposal_ids == (7, 8)
    assert epic.score == 7.0
    assert not epic.witness_available
    assert epic.diagnostics["input_proposal_weights"] == (2.0, 5.0)
    assert epic.diagnostics["candidate_ranking_score"] == "model_confidence"

    assert exact.status is SelectionStatus.OPTIMAL
    assert exact.selected_proposal_ids == (7, 8)
    assert exact.score == 7.0
    assert exact.witness_available
    assert selection_input.proposals == (
        Proposal(7, 0, 0, weight=2.0, model_confidence=0.9),
        Proposal(8, 1, 1, weight=5.0, model_confidence=0.8),
    )
    json.dumps(epic.to_dict())


def test_epic_records_regular_cover_and_exact_shrink_profiler_deltas(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    selection_input = common_input(
        (
            Proposal(0, 0, 0, weight=3.0, model_confidence=0.7),
            Proposal(1, 1, 1, weight=4.0, model_confidence=0.6),
        )
    )
    before = {
        "timers": {
            "regular_cover.generated_language": {"count": 10},
            "regular_cover.intersection": {"count": 10},
        },
        "counts": {"regular_cover.exact.calls": 5},
    }
    after = {
        "timers": {
            "regular_cover.generated_language": {"count": 14},
            "regular_cover.intersection": {"count": 14},
        },
        "counts": {"regular_cover.exact.calls": 8},
    }

    def select_all(**kwargs: object) -> object:
        return kwargs["candidates"]

    install_runtime(
        monkeypatch,
        fake_runtime(
            select_all,
            profiler_enabled=True,
            snapshots=(before, after),
        ),
    )

    result = select_epic_regular_cover(selection_input, context())

    assert result.diagnostics["regular_cover_profiler_enabled"] is True
    assert result.diagnostics["regular_cover_selector_calls"] == 1
    assert result.diagnostics["regular_cover_check_calls"] == 4
    assert result.diagnostics["regular_cover_intersection_calls"] == 4
    assert result.diagnostics["exact_shrink_check_calls"] == 3
    assert result.diagnostics["exact_shrink_enabled"] is True


def test_epic_applies_upstream_minimum_batch_before_and_after_selection(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    one_candidate = common_input((Proposal(0, 0, 0, weight=3.0, model_confidence=0.7),))

    def must_not_run(**_kwargs: object) -> object:
        pytest.fail("EPIC selector ran below its minimum candidate batch")

    install_runtime(monkeypatch, fake_runtime(must_not_run))
    before = select_epic_regular_cover(one_candidate, context())

    assert before.status is SelectionStatus.HEURISTIC
    assert before.selected_proposal_ids == ()
    assert before.score == 0.0
    assert before.diagnostics["regular_cover_selector_calls"] == 0
    assert before.diagnostics["minimum_batch_filter_applied"] is True
    assert before.diagnostics["serial_fallback_required"] is True

    two_candidates = common_input(
        (
            Proposal(0, 0, 0, weight=3.0, model_confidence=0.7),
            Proposal(1, 1, 1, weight=4.0, model_confidence=0.6),
        )
    )

    def shrink_to_one(**kwargs: object) -> object:
        candidates = kwargs["candidates"]
        assert isinstance(candidates, list)
        return candidates[:1]

    install_runtime(monkeypatch, fake_runtime(shrink_to_one))
    after = select_epic_regular_cover(two_candidates, context())

    assert after.status is SelectionStatus.HEURISTIC
    assert after.selected_proposal_ids == ()
    assert after.score == 0.0
    assert after.diagnostics["upstream_selected_proposal_ids"] == (0,)
    assert after.diagnostics["minimum_batch_filter_applied"] is True
    assert after.diagnostics["serial_fallback_required"] is True


@pytest.mark.parametrize(
    ("proposals", "reason"),
    [
        (
            (
                Proposal(0, 0, 0, weight=1.0, model_confidence=0.9),
                Proposal(1, 0, 0, weight=2.0, model_confidence=0.8),
            ),
            "unique positions",
        ),
        (
            (
                Proposal(0, 0, 0, weight=1.0),
                Proposal(1, 1, 1, weight=2.0, model_confidence=0.8),
            ),
            "model_confidence",
        ),
    ],
)
def test_epic_reports_schedule_inputs_it_cannot_represent_as_unsupported(
    monkeypatch: pytest.MonkeyPatch,
    proposals: tuple[Proposal, ...],
    reason: str,
) -> None:
    selection_input = common_input(proposals)

    def must_not_run(**_kwargs: object) -> object:
        pytest.fail("unsupported EPIC input reached the upstream selector")

    install_runtime(monkeypatch, fake_runtime(must_not_run))

    result = select_epic_regular_cover(selection_input, context())

    assert result.status is SelectionStatus.UNSUPPORTED
    assert reason in result.diagnostics["unsupported_reason"]
    assert result.score is None
    assert not result.witness_available


def test_epic_rejects_unknown_upstream_candidate_without_partial_score(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    selection_input = common_input(
        (
            Proposal(0, 0, 0, weight=3.0, model_confidence=0.7),
            Proposal(1, 1, 1, weight=4.0, model_confidence=0.6),
        )
    )

    def return_copy(**kwargs: object) -> object:
        candidates = kwargs["candidates"]
        assert isinstance(candidates, list)
        first = candidates[0]
        return [FakeCandidate(first.index, first.token_id, first.word, first.score)]

    install_runtime(monkeypatch, fake_runtime(return_copy))

    result = select_epic_regular_cover(selection_input, context())

    assert result.status is SelectionStatus.ERROR
    assert result.diagnostics["error_stage"] == "upstream_result_validation"
    assert result.score is None
    assert result.selected_proposal_ids == ()


def test_epic_current_words_must_match_common_canvas_mask_state(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    selection_input = common_input(
        (
            Proposal(0, 0, 0, weight=3.0, model_confidence=0.7),
            Proposal(1, 1, 1, weight=4.0, model_confidence=0.6),
        )
    )
    install_runtime(monkeypatch, fake_runtime(lambda **_kwargs: []))
    mismatched = EpicSelectionContext(
        words_full=("prompt", "already-fixed", None),
        prompt_length=1,
        cfg=object(),
        decode_token=lambda token_id: ("a", "b")[token_id],
    )

    with pytest.raises(ValueError, match="masked/fixed state at position 0"):
        select_epic_regular_cover(selection_input, mismatched)
