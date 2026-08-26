from __future__ import annotations

import pytest

from mwpc_exact import (
    CompositionalByteLevelAdapter,
    EOSMode,
    EOSPolicy,
    Proposal,
    SelectionInput,
    SupportKind,
    SupportPolicy,
    build_per_position_support,
    validate_ordinary_primary_proposal_comparison,
)
from mwpc_exact.reference.grammar import CnfGrammar, Nonterminal, Terminal, TerminalProduction


def _input(proposals: tuple[Proposal, ...]) -> SelectionInput:
    adapter = CompositionalByteLevelAdapter((b"a", b"b", None))
    canvas = (None, None)
    support = build_per_position_support(
        canvas=canvas,
        policy=SupportPolicy(
            kind=SupportKind.EXPLICIT,
            vocabulary_size=3,
            required_special_token_ids=(2,),
        ),
        explicit_support={0: (0, 1, 2), 1: (0, 1, 2)},
        proposals=proposals,
    )
    grammar = CnfGrammar(
        nonterminals=(Nonterminal(0, "S"),),
        terminals=(Terminal(0, ord("a")),),
        start_nonterminal_id=0,
        terminal_productions=(TerminalProduction(0, 0, 0),),
    )
    return SelectionInput(
        grammar=grammar,
        canvas=canvas,
        proposals=proposals,
        support=support,
        tokenizer_adapter=adapter,
        eos_policy=EOSPolicy(EOSMode.REQUIRED, termination_token_ids=(2,), pad_token_id=2),
    )


def test_comparison_profile_accepts_one_represented_ordinary_proposal_per_position() -> None:
    validate_ordinary_primary_proposal_comparison(
        _input(
            (
                Proposal(0, 0, 0, 1.0, model_confidence=0.9),
                Proposal(1, 1, 1, 1.0, model_confidence=0.8),
            )
        )
    )


@pytest.mark.parametrize(
    "proposals, message",
    [
        (
            (
                Proposal(0, 0, 0, 1.0, model_confidence=0.9),
                Proposal(1, 0, 1, 1.0, model_confidence=0.8),
            ),
            "at most one",
        ),
        ((Proposal(0, 0, 2, 1.0, model_confidence=0.9),), "excludes EOS/PAD"),
        ((Proposal(0, 0, 0, 1.0),), "model_confidence"),
    ],
)
def test_comparison_profile_rejects_noncomparable_candidate_universes(
    proposals: tuple[Proposal, ...],
    message: str,
) -> None:
    with pytest.raises(ValueError, match=message):
        validate_ordinary_primary_proposal_comparison(_input(proposals))
