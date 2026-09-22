"""Regressions from the repository-wide review; no models or network needed."""

from collections.abc import Iterable
from dataclasses import replace

import pytest

from mwpc_exact import (
    AdaptiveSupportConfig,
    CompositionalByteLevelAdapter,
    EOSMode,
    EOSPolicy,
    ExactBackend,
    Proposal,
    SupportKind,
    SupportPolicy,
    ValidatedExactCommit,
    apply_exact_commit_result,
    build_per_position_support,
    solve_exact_commit_adaptive_validated,
    solve_validated_exact_commit,
)
from mwpc_exact.reference.grammar import CnfGrammar, Nonterminal, Terminal, TerminalProduction

GRAMMAR = CnfGrammar(
    nonterminals=(Nonterminal(0, "S"),),
    terminals=(Terminal(0, 97), Terminal(1, 98)),
    start_nonterminal_id=0,
    terminal_productions=(TerminalProduction(0, 0, 0), TerminalProduction(1, 0, 1)),
)
ORIGINAL = (Proposal(0, 0, 0, 1), Proposal(1, 0, 1, 0))


def solve(
    adaptive: bool, canvas: tuple[int | None, ...], proposals: Iterable[Proposal]
) -> ValidatedExactCommit:
    adapter = CompositionalByteLevelAdapter((b"a", b"b"))
    if adaptive:
        result = solve_exact_commit_adaptive_validated(
            GRAMMAR,
            canvas=canvas,
            proposals=proposals,
            logits=((1.0, 0.0),),
            config=AdaptiveSupportConfig(initial_k=2, k_max=2),
            tokenizer_adapter=adapter,
            eos_policy=EOSPolicy(EOSMode.ABSENT),
            backend=ExactBackend.PYTHON,
        )
    else:
        support = build_per_position_support(
            canvas=canvas,
            policy=SupportPolicy(kind=SupportKind.FULL, vocabulary_size=2),
            logits=((1.0, 0.0),),
        )
        result = solve_validated_exact_commit(
            GRAMMAR,
            canvas=canvas,
            proposals=proposals,
            support=support,
            tokenizer_adapter=adapter,
            eos_policy=EOSPolicy(EOSMode.ABSENT),
            backend=ExactBackend.PYTHON,
        )
    assert isinstance(result, ValidatedExactCommit)
    return result


@pytest.mark.parametrize("adaptive", [False, True])
@pytest.mark.parametrize(
    "changed",
    [
        (ORIGINAL[0], replace(ORIGINAL[1], weight=100)),
        (ORIGINAL[0],),
        (*ORIGINAL, Proposal(2, 0, 1, 100)),
    ],
)
def test_unmatched_proposal_changes_cannot_reuse_validated_authority(
    adaptive: bool, changed: tuple[Proposal, ...]
) -> None:
    result = solve(adaptive, (None,), iter(ORIGINAL))
    assert result.input_proposals == ORIGINAL  # A generator is frozen before solving.
    assert apply_exact_commit_result(result, canvas=(None,), proposals=ORIGINAL).updated_canvas == (
        0,
    )
    with pytest.raises(ValueError, match="proposals differ"):
        apply_exact_commit_result(result, canvas=(None,), proposals=changed)
    if any(proposal.weight == 100 for proposal in changed):
        assert solve(adaptive, (None,), changed).witness_token_ids == (1,)


@pytest.mark.parametrize("adaptive", [False, True])
def test_remasking_fixed_canvas_cannot_reuse_validated_authority(adaptive: bool) -> None:
    result = solve(adaptive, (0,), ())
    with pytest.raises(ValueError, match="canvas differs"):
        apply_exact_commit_result(
            result, canvas=(None,), proposals=(), witness_token_probabilities=(1.0,)
        )


def test_public_solver_recognizes_the_final_witness_once(monkeypatch: pytest.MonkeyPatch) -> None:
    import mwpc_exact.reference.dag_parser as parser
    import mwpc_exact.solver as solver

    calls = []
    original = solver.recognizes_cnf

    def recognize(grammar: CnfGrammar, labels: tuple[int | str, ...]) -> bool:
        calls.append(labels)
        return original(grammar, labels)

    monkeypatch.setattr(parser, "recognizes_cnf", recognize)
    monkeypatch.setattr(solver, "recognizes_cnf", recognize)
    assert solve(False, (None,), ORIGINAL).witness_token_ids == (0,)
    assert calls == [(97,)]
