"""One strictly validated finite-token state; no optimizer or model imports."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from mwpc_exact.eos_policy import EOSMode, EOSPolicy
from mwpc_exact.reference.grammar import CnfGrammar
from mwpc_exact.support import PerPositionSupport
from mwpc_exact.token_lattice import build_token_lattice
from mwpc_exact.tokenizer_bytes import CompositionalByteLevelAdapter
from mwpc_exact.types import Proposal, aggregate_proposals


def _non_negative_integer(value: object, field_name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{field_name} must be an integer")
    if value < 0:
        raise ValueError(f"{field_name} must be non-negative")
    return value


def _normalize_canvas(value: object) -> tuple[int | None, ...]:
    if isinstance(value, (str, bytes)) or not isinstance(value, Sequence):
        raise TypeError("canvas must be a finite sequence of token IDs or None")
    canvas: list[int | None] = []
    for position, token_id in enumerate(value):
        if token_id is None:
            canvas.append(None)
        else:
            canvas.append(_non_negative_integer(token_id, f"canvas token at {position}"))
    if not canvas:
        raise ValueError("canvas must contain at least one physical slot")
    return tuple(canvas)


@dataclass(frozen=True, slots=True)
class SelectionInput:
    """One frozen canvas/proposal/support instance shared by all selectors."""

    grammar: CnfGrammar
    canvas: tuple[int | None, ...]
    proposals: tuple[Proposal, ...]
    support: PerPositionSupport
    tokenizer_adapter: CompositionalByteLevelAdapter
    eos_policy: EOSPolicy

    def __post_init__(self) -> None:
        if not isinstance(self.grammar, CnfGrammar):
            raise TypeError("grammar must be a CnfGrammar")
        canvas = _normalize_canvas(self.canvas)
        proposals = tuple(self.proposals)
        aggregate_proposals(proposals)
        if not isinstance(self.support, PerPositionSupport):
            raise TypeError("support must be a PerPositionSupport")
        if not isinstance(self.tokenizer_adapter, CompositionalByteLevelAdapter):
            raise TypeError("tokenizer_adapter must be a CompositionalByteLevelAdapter")
        if not isinstance(self.eos_policy, EOSPolicy):
            raise TypeError("eos_policy must be an EOSPolicy")
        if canvas != self.support.canvas:
            raise ValueError("canvas must exactly match the saved support canvas")
        if self.tokenizer_adapter.vocabulary_size != self.support.exactness_scope.vocabulary_size:
            raise ValueError("tokenizer adapter and support must have equal vocabularies")

        configured_specials = set(self.eos_policy.termination_token_ids)
        if self.eos_policy.pad_token_id is not None:
            configured_specials.add(self.eos_policy.pad_token_id)
        missing_specials = sorted(
            configured_specials - set(self.support.exactness_scope.included_special_tokens)
        )
        if missing_specials:
            raise ValueError(
                "EOS/PAD token IDs must be listed in the support exactness scope: "
                f"{missing_specials}"
            )
        if self.eos_policy.mode is EOSMode.ABSENT and configured_specials:
            raise AssertionError("validated ABSENT EOS policy unexpectedly has special IDs")

        # Reuse the public finite-support boundary to validate proposal IDs,
        # positions, token IDs, fixed positions, and represented/unrepresented
        # proposal accounting without executing either selector.
        build_token_lattice(support=self.support, proposals=proposals)
        object.__setattr__(self, "canvas", canvas)
        object.__setattr__(self, "proposals", proposals)
