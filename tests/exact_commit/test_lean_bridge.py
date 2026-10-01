from __future__ import annotations

import copy
from fractions import Fraction

import pytest
from tests.exact_commit.test_compact_budget_graph import make_state

from mwpc_exact import EOSMode, EOSPolicy, Proposal
from mwpc_exact.budget_proof import budget_proof_data
from mwpc_exact.budgeted_commit import budgeted_commit_frontier
from mwpc_exact.lean_bridge import audit_lean_axioms, export_lean_budget_proof, verify_with_lean


@pytest.mark.parametrize("weight", (0, 0.5, 0.1, 1 + 2**-52))
def test_export_scales_binary_float_scores_exactly_and_uses_no_admissions(weight):
    state = make_state((b"a",), (b"a",), ((0,),), (Proposal(0, 0, 0, weight),))
    value = budget_proof_data(state, budgeted_commit_frontier(state, 1))
    export = export_lean_budget_proof(value)
    assert export.denominator == Fraction(weight).denominator
    assert export.theorem_names == ("MWPC.Generated.optimal_0", "MWPC.Generated.optimal_1")
    assert "sorry" not in export.source and "native_decide" not in export.source
    assert "axiom " not in export.source
    assert "Epsilon.identity" in export.source and "Derivation.terminal" in export.source


def test_infeasible_export_proves_absence_without_fabricating_a_witness():
    state = make_state((b"b",), (b"a",), ((0,),))
    export = export_lean_budget_proof(budget_proof_data(state, budgeted_commit_frontier(state, 1)))
    assert "certified_infeasible" in export.source
    assert "witness_" not in export.source


def test_silent_eos_pad_and_empty_grammar_export_real_epsilon_paths():
    state = make_state(
        (b"",),
        (None,),
        ((0,), (0,)),
        (Proposal(0, 0, 0, 0.5),),
        eos=EOSPolicy(EOSMode.REQUIRED, (0,), 0),
    )
    export = export_lean_budget_proof(budget_proof_data(state, budgeted_commit_frontier(state, 1)))
    assert "Or.inr" in export.source and "Epsilon.step" in export.source


def test_export_rejects_forged_input_before_generating_a_theorem():
    state = make_state((b"a",), (b"a",), ((0,),), (Proposal(0, 0, 0, 1),))
    data = copy.deepcopy(budget_proof_data(state, budgeted_commit_frontier(state, 1)))
    data["input_fingerprint"] = "0" * 64
    with pytest.raises(ValueError, match="Budget"):
        export_lean_budget_proof(data)


def test_missing_lean_is_an_explicit_failure(tmp_path):
    state = make_state((b"a",), (b"a",), ((0,),))
    data = budget_proof_data(state, budgeted_commit_frontier(state, 1))
    with pytest.raises(FileNotFoundError, match="Lean/Lake"):
        verify_with_lean(data, formal_directory=tmp_path, lake="mwpc-nonexistent-lake")


@pytest.mark.parametrize("dependency", ("sorryAx", "Lean.ofReduceBool", "MWPC.assumeCorrect"))
def test_axiom_audit_rejects_admissions_native_shortcuts_and_project_axioms(dependency):
    with pytest.raises(ValueError, match="Unapproved"):
        audit_lean_axioms(f"'MWPC.proof' depends on axioms: [{dependency}]", ("MWPC.proof",))


def test_axiom_audit_requires_all_named_theorems_and_accepts_only_standard_logic():
    output = (
        "'MWPC.a' depends on axioms: [propext, Quot.sound]\n'MWPC.b' does not depend on any axioms"
    )
    assert audit_lean_axioms(output, ("MWPC.a", "MWPC.b")) == {
        "MWPC.a": ("propext", "Quot.sound"),
        "MWPC.b": (),
    }
    with pytest.raises(ValueError, match="exactly"):
        audit_lean_axioms(output, ("MWPC.a", "MWPC.b", "MWPC.c"))
