"""Offline multi-step LLaDA exact-loop regression over versioned saved logits."""

from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

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
    LLaDAExactStepResult,
    run_llada_exact_step,
)
from mwpc_exact.reference.grammar import CnfGrammar
from mwpc_exact.reference.recognizer import recognizes_cnf

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "llada_saved_logit_loop.json"


class _TokenRow:
    """Minimal CPU sequence with the tensor-like surface used by the adapter."""

    def __init__(self, values: list[int]) -> None:
        self.values = values

    def detach(self) -> _TokenRow:
        return self

    def cpu(self) -> _TokenRow:
        return self

    def tolist(self) -> list[int]:
        return list(self.values)

    def __setitem__(self, position: int, token_id: int) -> None:
        self.values[position] = token_id


@dataclass(frozen=True, slots=True)
class _LoggedStepEvent:
    step_index: int
    step_id: str
    input_token_ids: tuple[int, ...]
    outcome: LLaDAExactStepResult

    def to_dict(self) -> dict[str, object]:
        return {
            "event_type": "llada_offline_exact_step",
            "step_index": self.step_index,
            "step_id": self.step_id,
            "input_token_ids": list(self.input_token_ids),
            "outcome": self.outcome.to_dict(),
        }

    def stable_summary(self) -> dict[str, object]:
        result = self.outcome.solver_result
        validation = result.diagnostics.get("certificate_validation")
        if not isinstance(validation, Mapping):
            raise AssertionError("OPTIMAL saved-logit step omitted certificate validation")
        return {
            "step_index": self.step_index,
            "step_id": self.step_id,
            "input_token_ids": list(self.input_token_ids),
            "input_canvas": list(self.outcome.request.canvas),
            "candidate_positions": list(
                self.outcome.request.proposal_batch.candidate_positions
            ),
            "solver_status": result.status.value,
            "objective_value": result.objective_value,
            "selected_proposal_ids": list(result.selected_proposal_ids),
            "witness_token_ids": list(result.witness_token_ids),
            "witness_terminal_labels": list(result.witness_terminal_labels),
            "exactness_scope": self.outcome.request.diagnostics["exactness_scope"],
            "support_kind": result.exactness_scope.kind.value,
            "validation_is_valid": validation["is_valid"],
            "updated_canvas": list(self.outcome.updated_canvas),
            "updates": [update.to_dict() for update in self.outcome.model_updates],
            "complete": self.outcome.complete,
        }


@dataclass(frozen=True, slots=True)
class _OfflineLoopRun:
    final_token_ids: tuple[int, ...]
    final_tracking: tuple[object, ...]
    final_terminal_labels: tuple[int, ...]
    final_grammar_valid: bool
    events: tuple[_LoggedStepEvent, ...]

    def stable_summary(self) -> dict[str, object]:
        return {
            "final_token_ids": list(self.final_token_ids),
            "final_tracking": list(self.final_tracking),
            "final_terminal_labels": list(self.final_terminal_labels),
            "final_grammar_valid": self.final_grammar_valid,
            "events": [event.stable_summary() for event in self.events],
        }


def _load_fixture() -> dict[str, Any]:
    return json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))


def _run_saved_logit_loop(fixture: dict[str, Any]) -> _OfflineLoopRun:
    profile_data = fixture["profile"]
    policy_data = profile_data["eos_policy"]
    eos_policy = EOSPolicy(
        EOSMode(policy_data["mode"]),
        termination_token_ids=tuple(policy_data["termination_token_ids"]),
        pad_token_id=policy_data["pad_token_id"],
    )
    profile = LLaDAAdapterProfile(
        model_id=profile_data["model_id"],
        tokenizer_revision=profile_data["tokenizer_revision"],
        mask_token_id=profile_data["mask_token_id"],
        eos_policy=eos_policy,
    )
    emissions = tuple(
        None if emission is None else bytes.fromhex(emission)
        for emission in fixture["tokenizer"]["emissions_hex"]
    )
    tokenizer_adapter = CompositionalByteLevelAdapter(emissions)
    decoded_tokens = fixture["tokenizer"]["decoded_tokens"]
    exact_data = fixture["exact_config"]
    config = ExactStrategyConfig(
        adaptive_support=AdaptiveSupportConfig(
            initial_k=exact_data["support_top_k"],
            k_max=exact_data["support_k_max"],
        ),
        weight_mode=ProposalWeightMode(exact_data["weight_mode"]),
        eos_policy=eos_policy,
        backend=ExactBackend(exact_data["backend"]),
        failure_fallback_strategy=None,
    )
    grammar = CnfGrammar.from_dict(fixture["grammar"])
    token_row = _TokenRow(list(fixture["initial_token_ids"]))
    tracking = list(fixture["initial_decoded_tracking"])
    events: list[_LoggedStepEvent] = []

    for step_index, step in enumerate(fixture["steps"]):
        input_token_ids = tuple(token_row.values)
        outcome = run_llada_exact_step(
            grammar,
            token_ids=token_row,
            logits=step["logits"],
            predicted_token_ids=step["predicted_token_ids"],
            confidence_values=step["confidence_values"],
            decoded_tracking=tracking,
            decode_token=lambda token_id: decoded_tokens[str(token_id)],
            eos_marker=profile_data["eos_marker"],
            prompt_length=profile_data["prompt_length"],
            generation_length=profile_data["generation_length"],
            active_block_end=step["active_block_end"],
            k_s=step["k_s"],
            tokenizer_adapter=tokenizer_adapter,
            config=config,
            profile=profile,
        )
        event = _LoggedStepEvent(
            step_index=step_index,
            step_id=step["step_id"],
            input_token_ids=input_token_ids,
            outcome=outcome,
        )
        events.append(event)

        assert outcome.solver_result.status is SolveStatus.OPTIMAL
        assert outcome.model_updates
        assert sum(token_id == profile.mask_token_id for token_id in token_row.values) < sum(
            token_id == profile.mask_token_id for token_id in input_token_ids
        )
        for before, after in zip(input_token_ids, token_row.values, strict=True):
            if before != profile.mask_token_id:
                assert after == before
        if outcome.complete:
            assert step_index == len(fixture["steps"]) - 1

    assert events and events[-1].outcome.complete
    final_canvas = events[-1].outcome.updated_canvas
    termination_ids = frozenset(eos_policy.termination_token_ids)
    termination_position = next(
        position for position, token_id in enumerate(final_canvas) if token_id in termination_ids
    )
    content_token_ids = final_canvas[:termination_position]
    assert all(token_id is not None for token_id in content_token_ids)
    terminal_labels = tuple(
        tokenizer_adapter.detokenize_bytes(
            token_id for token_id in content_token_ids if token_id is not None
        )
    )
    return _OfflineLoopRun(
        final_token_ids=tuple(token_row.values),
        final_tracking=tuple(tracking),
        final_terminal_labels=terminal_labels,
        final_grammar_valid=recognizes_cnf(grammar, terminal_labels),
        events=tuple(events),
    )


def test_saved_logits_drive_complete_offline_exact_decoder_loop() -> None:
    fixture = _load_fixture()

    assert fixture["schema_version"] == 1
    assert fixture["execution"] == {
        "device": "cpu",
        "model_weights_required": False,
        "network_required": False,
    }
    first = _run_saved_logit_loop(fixture)
    second = _run_saved_logit_loop(fixture)

    assert first.stable_summary() == fixture["expected"]
    assert second.stable_summary() == first.stable_summary()
    assert tuple(event.step_id for event in first.events) == tuple(
        step["step_id"] for step in fixture["steps"]
    )
    assert len(first.events) == len(fixture["steps"])
    assert first.final_grammar_valid
    json.dumps([event.to_dict() for event in first.events])
