from __future__ import annotations

import json

import pytest

from mwpc_exact import (
    AdaptiveSupportConfig,
    CompositionalByteLevelAdapter,
    EOSMode,
    EOSPolicy,
    ExactBackend,
    ExactStrategyConfig,
    ProposalWeightMode,
    SolveStatus,
)
from mwpc_exact.epic_adapter.llada import (
    LLaDAAdapterProfile,
    LLaDAUpdateReason,
    build_llada_byte_adapter,
    run_llada_exact_step,
)
from mwpc_exact.reference.grammar import (
    BinaryProduction,
    CnfGrammar,
    Nonterminal,
    Terminal,
    TerminalProduction,
)

EOS = 3
EOT = 4
MASK = 5
ADAPTER = CompositionalByteLevelAdapter((b"a", b"b", b"c", None, None, None))
PROFILE = LLaDAAdapterProfile(
    model_id="offline/llada-style-fixture",
    tokenizer_revision="fixed",
    mask_token_id=MASK,
    eos_policy=EOSPolicy(
        EOSMode.REQUIRED,
        termination_token_ids=(EOS, EOT),
        pad_token_id=EOS,
    ),
)


class _TensorRow:
    """Small torch-row stand-in exercising the adapter's tensor surface."""

    def __init__(self, values: list[int]) -> None:
        self.values = values

    def detach(self) -> _TensorRow:
        return self

    def cpu(self) -> _TensorRow:
        return self

    def tolist(self) -> list[int]:
        return list(self.values)

    def __setitem__(self, position: int, token_id: int) -> None:
        self.values[position] = token_id


def _grammar_ab() -> CnfGrammar:
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


def _config(*, top_k: int) -> ExactStrategyConfig:
    return ExactStrategyConfig(
        adaptive_support=AdaptiveSupportConfig(initial_k=top_k, k_max=top_k),
        weight_mode=ProposalWeightMode.CONFIDENCE,
        eos_policy=PROFILE.eos_policy,
        backend=ExactBackend.PYTHON,
        failure_fallback_strategy=None,
    )


def _row(*scores: float) -> tuple[float, ...]:
    assert len(scores) == ADAPTER.vocabulary_size
    return scores


def test_live_byte_adapter_marks_added_and_model_only_rows_unsupported() -> None:
    adapter = build_llada_byte_adapter(
        ("a", "b", "c"),
        model_vocabulary_size=ADAPTER.vocabulary_size,
        profile=PROFILE,
    )

    assert adapter.vocabulary_size == ADAPTER.vocabulary_size
    assert adapter.emissions == (b"a", b"b", b"c", None, None, None)
    assert set(PROFILE.eos_policy.termination_token_ids) <= set(adapter.unsupported_token_ids)


def test_live_byte_adapter_rejects_model_vocabulary_before_profile_specials() -> None:
    with pytest.raises(ValueError, match="special token outside"):
        build_llada_byte_adapter(
            ("a", "b", "c"),
            model_vocabulary_size=5,
            profile=PROFILE,
        )


def test_fixed_logits_reach_exact_hook_with_generated_canvas_and_baseline_candidates() -> None:
    token_row = _TensorRow([2, 2, MASK, MASK, MASK, MASK])
    logits = (
        _row(0, 0, 10, -1, -2, -3),
        _row(0, 0, 10, -1, -2, -3),
        _row(10, 0, 9, -1, -2, -3),
        _row(0, 10, 9, -1, -2, -3),
        _row(0, 0, -1, 10, 9, -2),
        _row(0, 0, -1, 10, 9, -2),
    )
    predictions = (2, 2, 0, 1, 0, 0)
    confidence = (-float("inf"), -float("inf"), 0.6, 0.9, 99.0, 100.0)
    tracking: list[object] = ["prompt-a", "prompt-b", None, None, None, None]

    outcome = run_llada_exact_step(
        _grammar_ab(),
        token_ids=token_row,
        logits=logits,
        predicted_token_ids=predictions,
        confidence_values=confidence,
        decoded_tracking=tracking,
        decode_token=lambda token_id: f"token-{token_id}",
        eos_marker="<EOS>",
        prompt_length=2,
        generation_length=4,
        active_block_end=4,
        k_s=1,
        tokenizer_adapter=ADAPTER,
        config=_config(top_k=2),
        profile=PROFILE,
    )

    assert outcome.solver_result.status is SolveStatus.OPTIMAL
    assert outcome.request.prompt_token_ids == (2, 2)
    assert outcome.request.canvas == (None, None, None, None)
    assert outcome.request.logits == logits[2:]
    assert outcome.request.schedule_mask == (True, True, False, False)
    assert outcome.request.proposal_batch.schedule_budget == 1
    assert outcome.request.proposal_batch.candidate_positions == (1,)
    proposal = outcome.request.proposal_batch.proposals[0]
    assert (proposal.position, proposal.token_id, proposal.weight) == (1, 1, 0.9)
    assert outcome.updated_canvas == (None, 1, None, None)
    assert token_row.values == [2, 2, MASK, 1, MASK, MASK]
    assert tracking == ["prompt-a", "prompt-b", None, "token-1", None, None]
    assert tuple(update.model_position for update in outcome.model_updates) == (3,)
    assert outcome.complete is False
    assert outcome.request.diagnostics["exactness_scope"] == "exact_on_support"
    json.dumps(outcome.to_dict())


def test_eot_commit_canonicalizes_suffix_to_pad_outside_active_block() -> None:
    token_row = _TensorRow([2, MASK, MASK, MASK, MASK])
    logits = (
        _row(0, 0, 10, -1, -2, -3),
        _row(10, 0, 9, -1, -2, -3),
        _row(0, 10, 9, -1, -2, -3),
        _row(0, 0, -1, 9, 10, -2),
        _row(0, 0, 10, 9, 8, -2),
    )
    tracking: list[object] = ["prompt", None, None, None, None]

    outcome = run_llada_exact_step(
        _grammar_ab(),
        token_ids=token_row,
        logits=logits,
        predicted_token_ids=(2, 0, 1, EOT, 2),
        confidence_values=(-float("inf"), 0.9, 0.8, 0.7, 1.0),
        decoded_tracking=tracking,
        decode_token=lambda token_id: f"token-{token_id}",
        eos_marker="<EOS>",
        prompt_length=1,
        generation_length=4,
        active_block_end=4,
        k_s=3,
        tokenizer_adapter=ADAPTER,
        config=_config(top_k=1),
        profile=PROFILE,
    )

    assert outcome.solver_result.witness_token_ids == (0, 1, EOT, EOS)
    assert outcome.updated_canvas == (0, 1, EOT, EOS)
    assert token_row.values == [2, 0, 1, EOT, EOS]
    assert tracking == ["prompt", "token-0", "token-1", "<EOS>", "<EOS>"]
    assert tuple(update.reason for update in outcome.model_updates) == (
        LLaDAUpdateReason.DECODER_COMMIT,
        LLaDAUpdateReason.DECODER_COMMIT,
        LLaDAUpdateReason.DECODER_COMMIT,
        LLaDAUpdateReason.EOS_PAD_CANONICALIZATION,
    )
    assert outcome.model_updates[-1].model_position == 4
    assert outcome.complete is True


def test_zero_match_witness_progress_cannot_escape_active_block() -> None:
    token_row = _TensorRow([2, MASK, MASK, MASK, MASK])
    logits = (
        _row(0, 0, 10, -1, -2, -3),
        _row(0, -1, 10, -2, -3, -4),
        _row(-1, 9, 10, -2, -3, -4),
        _row(0, 0, -1, 10, 9, -2),
        _row(0, 0, -1, 10, 9, -2),
    )
    tracking: list[object] = ["prompt", None, None, None, None]

    outcome = run_llada_exact_step(
        _grammar_ab(),
        token_ids=token_row,
        logits=logits,
        predicted_token_ids=(2, 2, 2, EOS, EOS),
        confidence_values=(-float("inf"), 0.9, 0.8, 99.0, 100.0),
        decoded_tracking=tracking,
        decode_token=lambda token_id: f"token-{token_id}",
        eos_marker="<EOS>",
        prompt_length=1,
        generation_length=4,
        active_block_end=3,
        k_s=1,
        tokenizer_adapter=ADAPTER,
        config=_config(top_k=2),
        profile=PROFILE,
    )

    assert outcome.solver_result.selected_proposal_ids == ()
    assert tuple(commit.position for commit in outcome.decoder_step.commits) == (1,)
    assert outcome.updated_canvas == (None, 1, None, None)
    assert token_row.values == [2, MASK, 1, MASK, MASK]
    assert all(update.model_position < 3 for update in outcome.model_updates)


def test_profile_mismatch_is_rejected_before_tensor_mutation() -> None:
    token_row = _TensorRow([2, MASK, MASK, MASK, MASK])
    tracking: list[object] = ["prompt", None, None, None, None]
    wrong_config = ExactStrategyConfig(
        adaptive_support=AdaptiveSupportConfig(initial_k=1, k_max=1),
        weight_mode=ProposalWeightMode.CONFIDENCE,
        eos_policy=EOSPolicy(EOSMode.ABSENT),
        backend=ExactBackend.PYTHON,
        failure_fallback_strategy=None,
    )

    with pytest.raises(ValueError, match="must match"):
        run_llada_exact_step(
            _grammar_ab(),
            token_ids=token_row,
            logits=tuple(_row(0, 0, 10, -1, -2, -3) for _ in range(5)),
            predicted_token_ids=(2, 0, 1, EOS, EOS),
            confidence_values=(-float("inf"), 0.9, 0.8, 0.7, 0.6),
            decoded_tracking=tracking,
            decode_token=str,
            eos_marker="<EOS>",
            prompt_length=1,
            generation_length=4,
            active_block_end=3,
            k_s=1,
            tokenizer_adapter=ADAPTER,
            config=wrong_config,
            profile=PROFILE,
        )

    assert token_row.values == [2, MASK, MASK, MASK, MASK]
    assert tracking == ["prompt", None, None, None, None]
