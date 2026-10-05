from __future__ import annotations

from copy import deepcopy
from dataclasses import replace
from fractions import Fraction
from itertools import product
from random import Random

import pytest
from tests.exact_commit.test_budget_bounds import state_for

from mwpc_exact import EOSMode, EOSPolicy, ExactBackend
from mwpc_exact.budget_bounds import validate_budget_batch
from mwpc_exact.mass_certificate import PosteriorScope, ProbabilityInput, verify_mass_proof
from mwpc_exact.mass_solver import probability_partition


def exact_distribution(predictive):
    masses = {}
    for tokens in product(*predictive.state.support.rows):
        try:
            validate_budget_batch(
                predictive.state, budget=0, witness_token_ids=tokens, committed_positions=()
            )
        except ValueError:
            continue
        mass = predictive.box_mass(tuple((t,) for t in tokens))
        if mass:
            masses[tokens] = mass
    return masses


def tv(known, true):
    return (
        sum((abs(known.get(t, 0) - true.get(t, 0)) for t in set(known) | set(true)), Fraction()) / 2
    )


@pytest.mark.parametrize("seed", range(300000, 300024))
def test_anytime_bounds_and_exact_tv_against_independent_original_token_enumeration(seed):
    rng = Random(seed)
    words = [bytes(w) for w in product(b"ab", repeat=3)]
    state = state_for(
        rng.sample(words, rng.randrange(1, 9)), (b"a", b"b", b"a"), ((0, 1, 2),) * 3, ()
    )
    rows = tuple(tuple(Fraction(rng.randrange(4), 12) for _ in range(3)) for _ in range(3))
    predictive = ProbabilityInput(state, rows)
    exact = exact_distribution(predictive)
    z = sum(exact.values(), Fraction())
    for limit in (0, 1, 3, 64):
        proof = probability_partition(
            predictive, max_oracle_calls=limit, requested_tv=Fraction(), backend=ExactBackend.PYTHON
        )
        checked = verify_mass_proof(proof, expected_input=predictive)
        assert checked.lower <= z <= checked.upper(PosteriorScope.REPRESENTED), seed
        assert checked.upper(PosteriorScope.FULL) <= 1, seed
        if checked.lower:
            q = {t: m / checked.lower for t, m in checked.accepted}
            p = {t: m / z for t, m in exact.items()}
            assert tv(q, p) == 1 - checked.lower / z, seed
            assert tv(q, p) <= checked.tv_bound(PosteriorScope.REPRESENTED), seed
            for position in range(3):

                def event(t, pos=position):
                    return t[pos] == 0

                lo, hi = checked.event_interval(event, PosteriorScope.REPRESENTED)
                exact_event = sum((m / z for t, m in exact.items() if event(t)), Fraction())
                assert lo <= exact_event <= hi, seed
        if limit == 64:
            assert checked.lower == z and checked.unresolved == 0, seed


def basic():
    state = state_for((b"ab", b"ba"), (b"a", b"b"), ((0, 1),) * 2, ())
    return ProbabilityInput(state, ((Fraction(3, 4), Fraction(1, 4)),) * 2)


def test_conditional_bound_can_be_sharp_without_grammar_benchmark():
    predictive = basic()
    proof = probability_partition(predictive, max_oracle_calls=1, backend=ExactBackend.PYTHON)
    result = verify_mass_proof(proof)
    exact = exact_distribution(predictive)
    z = sum(exact.values(), Fraction())
    assert result.lower == Fraction(3, 16)
    assert 1 - result.lower / z == Fraction(1, 2)
    assert result.tv_bound(PosteriorScope.REPRESENTED) >= Fraction(1, 2)
    complete = verify_mass_proof(
        probability_partition(
            predictive, max_oracle_calls=64, requested_tv=Fraction(), backend=ExactBackend.PYTHON
        )
    )
    assert complete.lower == Fraction(3, 8) and complete.tv_bound(PosteriorScope.FULL) == 0


def test_exact_on_tiny_support_does_not_authorize_full_predictive_sampling():
    state = state_for((b"a",), (b"a", b"b"), ((0,),), ())
    predictive = ProbabilityInput(state, ((Fraction(1, 1000),),))
    result = verify_mass_proof(probability_partition(predictive, backend=ExactBackend.PYTHON))
    assert result.tv_bound(PosteriorScope.REPRESENTED) == 0
    assert result.tv_bound(PosteriorScope.FULL) == Fraction(999, 1000)
    assert result.sample(Random(1), scope=PosteriorScope.REPRESENTED, max_tv=Fraction()) == (0,)
    with pytest.raises(ValueError, match="refused"):
        result.sample(Random(1), scope=PosteriorScope.FULL, max_tv=Fraction(1, 20))


def test_alias_tokens_are_distinct_outcomes_and_ambiguity_does_not_duplicate_mass():
    from mwpc_exact.reference.grammar import BinaryProduction, Nonterminal

    predictive = basic()
    g = predictive.state.grammar
    # Duplicate start derivations via a new renamed copy, preserving language.
    new = Nonterminal(max(n.symbol_id for n in g.nonterminals) + 1, "aliasStart")
    extra = []
    for rule in g.binary_productions:
        if rule.head_id == g.start_nonterminal_id:
            extra.append(
                BinaryProduction(
                    max(r.production_id for r in (*g.terminal_productions, *g.binary_productions))
                    + 1
                    + len(extra),
                    g.start_nonterminal_id,
                    rule.left_id,
                    rule.right_id,
                )
            )
    # Production identities differ even when their RHS is the same.
    ambiguous = replace(
        g, nonterminals=(*g.nonterminals, new), binary_productions=(*g.binary_productions, *extra)
    )
    input2 = replace(predictive, state=replace(predictive.state, grammar=ambiguous))
    result = verify_mass_proof(
        probability_partition(
            input2, max_oracle_calls=64, requested_tv=Fraction(), backend=ExactBackend.PYTHON
        )
    )
    assert result.lower == Fraction(3, 8)
    aliases = ProbabilityInput(
        state_for((b"a",), (b"a", b"a"), ((0, 1),), ()), ((Fraction(1, 4), Fraction(3, 4)),)
    )
    out = verify_mass_proof(
        probability_partition(aliases, requested_tv=Fraction(), backend=ExactBackend.PYTHON)
    )
    assert out.lower == 1 and len(out.accepted) == 2


def test_special_tokens_fixed_positions_and_zero_valid_mass_remain_distinct():
    state = state_for(
        (b"a",),
        (b"a", None),
        ((0,), (1,), (1,)),
        (),
        canvas=(0, None, None),
        eos=EOSPolicy(EOSMode.REQUIRED, (1,), 1),
    )
    result = verify_mass_proof(
        probability_partition(
            ProbabilityInput(state, ((Fraction(1),),) * 3), backend=ExactBackend.PYTHON
        )
    )
    assert result.lower == 1 and result.sample(
        Random(1), scope=PosteriorScope.FULL, max_tv=Fraction()
    ) == (0, 1, 1)
    no = ProbabilityInput(
        state_for((b"b",), (b"a", b"b"), ((0, 1),), ()), ((Fraction(1), Fraction()),)
    )
    proof = probability_partition(no, requested_tv=Fraction(), backend=ExactBackend.PYTHON)
    assert proof["status"] == "zero_valid_probability_on_support"
    assert verify_mass_proof(proof).lower == 0


def test_zero_probability_leaves_become_unknown_after_reweighting():
    state = state_for((b"a", b"b"), (b"a", b"b"), ((0, 1),), ())
    original = ProbabilityInput(state, ((Fraction(1), Fraction()),))
    proof = probability_partition(original, requested_tv=Fraction(), backend=ExactBackend.PYTHON)
    changed = ProbabilityInput(state, ((Fraction(1, 2), Fraction(1, 2)),))
    result = verify_mass_proof(proof, reweight=changed)
    assert result.lower == Fraction(1, 2) and result.unresolved == Fraction(1, 2)
    with pytest.raises(ValueError, match="refused"):
        result.sample(Random(1), scope=PosteriorScope.REPRESENTED, max_tv=Fraction())


@pytest.mark.parametrize(
    "mutation", ("bound", "probability", "children", "witness", "status", "unreachable")
)
def test_forged_portable_mass_certificates_are_rejected(mutation):
    proof = deepcopy(
        probability_partition(basic(), max_oracle_calls=1, backend=ExactBackend.PYTHON)
    )
    if mutation == "bound":
        proof["envelope"]["lower"] = [1, 1]
    if mutation == "probability":
        proof["probabilities"][0][0] = [1, 2]
    if mutation == "children":
        proof["nodes"][0]["children"] = [1, 1]
    if mutation == "witness":
        node = next(n for n in proof["nodes"] if n["kind"] == "accepted")
        node["box"] = [[0], [0]]
    if mutation == "status":
        proof["status"] = "certified_tolerance"
        proof["requested_tv"] = [0, 1]
    if mutation == "unreachable":
        proof["nodes"].append(deepcopy(proof["nodes"][-1]))
    with pytest.raises(ValueError):
        verify_mass_proof(proof)


def test_verification_and_reweighting_do_not_import_or_call_optimizers(monkeypatch):
    predictive = basic()
    proof = probability_partition(
        predictive, max_oracle_calls=64, requested_tv=Fraction(), backend=ExactBackend.PYTHON
    )

    def forbidden(*args, **kwargs):
        raise AssertionError("optimizer called during verification")

    monkeypatch.setattr("mwpc_exact.mass_solver.select_exact_mwpc", forbidden)
    monkeypatch.setattr("mwpc_exact.mass_solver.budgeted_commit_frontier", forbidden)
    changed = ProbabilityInput(predictive.state, ((Fraction(1, 2), Fraction(1, 2)),) * 2)
    result = verify_mass_proof(proof, reweight=changed)
    assert result.lower == Fraction(1, 2) and result.unresolved == 0


def test_timeouts_and_call_limits_keep_sound_unresolved_bounds():
    proof = probability_partition(basic(), timeout_seconds=0, backend=ExactBackend.PYTHON)
    assert proof["status"] == "timeout"
    out = verify_mass_proof(proof)
    assert out.lower == 0 and out.unresolved == 1
    with pytest.raises(ValueError):
        out.sample(Random(0), scope=PosteriorScope.REPRESENTED, max_tv=Fraction(1))


@pytest.mark.parametrize("rows", (((1.0,),), ((True,),), ((Fraction(-1),),), ((Fraction(2),),)))
def test_invalid_probability_inputs_are_rejected(rows):
    state = state_for((b"a",), (b"a",), ((0,),), ())
    with pytest.raises((ValueError, TypeError)):
        ProbabilityInput(state, rows)


def test_sharp_mass_error_bound_is_attained_when_all_unknown_sequences_are_valid():
    predictive = ProbabilityInput(
        state_for((b"a", b"b"), (b"a", b"b"), ((0, 1),), ()), ((Fraction(1, 2), Fraction(1, 2)),)
    )
    result = verify_mass_proof(
        probability_partition(predictive, max_oracle_calls=1, backend=ExactBackend.PYTHON)
    )
    assert result.lower == result.unresolved == Fraction(1, 2)
    assert result.tv_bound(PosteriorScope.REPRESENTED) == Fraction(1, 2)
    assert tv(
        {t: m / result.lower for t, m in result.accepted},
        {(0,): Fraction(1, 2), (1,): Fraction(1, 2)},
    ) == Fraction(1, 2)


def test_proof_checked_parallel_commitment_preserves_fixed_slots_and_declared_tolerance():
    from mwpc_exact.probabilistic_update import certified_parallel_update

    predictive = basic()
    proof = probability_partition(
        predictive, max_oracle_calls=64, requested_tv=Fraction(), backend=ExactBackend.PYTHON
    )
    out = certified_parallel_update(
        predictive,
        proof,
        committed_positions=(1,),
        rng=Random(300000),
        scope=PosteriorScope.REPRESENTED,
        max_tv=Fraction(),
    )
    assert out.canvas[0] is None and out.canvas[1] == out.witness_token_ids[1]
    assert out.certified_tv_bound == 0
    for positions in ((0, 0), (-1,), (True,), (2,)):
        with pytest.raises((TypeError, ValueError)):
            certified_parallel_update(
                predictive,
                proof,
                committed_positions=positions,
                rng=Random(1),
                scope=PosteriorScope.REPRESENTED,
                max_tv=Fraction(),
            )


def test_trajectory_bound_against_exact_path_distributions_for_history_dependent_transitions():
    from mwpc_exact.probabilistic_update import trajectory_tv_bound

    errors = (Fraction(1, 10), Fraction(1, 20), Fraction(1, 40))

    def paths(perturb):
        masses = {(): Fraction(1)}
        for error in errors:
            new = {}
            for history, mass in masses.items():
                p = Fraction(1, 4) if sum(history) % 2 else Fraction(3, 4)
                p += error if perturb else 0
                new[(*history, 0)] = mass * (1 - p)
                new[(*history, 1)] = mass * p
            masses = new
        return masses

    assert tv(paths(False), paths(True)) <= trajectory_tv_bound(errors) == Fraction(7, 40)
    assert trajectory_tv_bound((Fraction(3, 4),) * 2) == 1


def test_finite_language_coverage_certifies_full_predictive_despite_large_discarded_mass():
    from mwpc_exact.language_coverage import finite_yield_bounds

    state = state_for((b"a",), (b"a", b"b"), ((0,),), ())
    predictive = ProbabilityInput(state, ((Fraction(1, 1000),),))
    coverage = finite_yield_bounds(state.grammar)
    proof = probability_partition(
        predictive,
        language_coverage=coverage,
        scope=PosteriorScope.FULL,
        requested_tv=Fraction(),
        backend=ExactBackend.PYTHON,
    )
    result = verify_mass_proof(proof)
    assert result.omitted == Fraction(999, 1000)  # never renormalized/concealed
    assert result.outside_valid_upper == 0 and result.tv_bound(PosteriorScope.FULL) == 0
    assert result.sample(Random(1), scope=PosteriorScope.FULL, max_tv=Fraction()) == (0,)


def test_coverage_requires_all_alias_tokenizations_and_closed_grammar_yields():
    from mwpc_exact.language_coverage import check_language_coverage, finite_yield_bounds

    state = state_for((b"a",), (b"a", b"a"), ((0,),), ())
    coverage = finite_yield_bounds(state.grammar)
    with pytest.raises(ValueError, match="outside"):
        check_language_coverage(state, coverage)
    coverage["yield_bounds"][0][1] = []
    with pytest.raises(ValueError, match="terminal"):
        check_language_coverage(state, coverage)


def test_recursive_productive_language_refuses_finite_coverage_and_retains_generic_bounds():
    from mwpc_exact.language_coverage import finite_yield_bounds
    from mwpc_exact.reference.grammar import BinaryProduction

    state = state_for((b"a",), (b"a",), ((0,),), ())
    g = state.grammar
    recursive = replace(
        g,
        binary_productions=(
            BinaryProduction(
                99, g.start_nonterminal_id, g.start_nonterminal_id, g.start_nonterminal_id
            ),
        ),
    )
    with pytest.raises(ValueError, match="size limit"):
        finite_yield_bounds(recursive, max_words=4, max_rounds=8)
    predictive = ProbabilityInput(replace(state, grammar=recursive), ((Fraction(1),),))
    assert (
        verify_mass_proof(probability_partition(predictive, backend=ExactBackend.PYTHON)).lower == 1
    )


def test_independent_catalog_control_matches_full_cartesian_bytes_with_aliases_and_split_utf8():
    from scripts.exact_commit.run_probability_probes import independent_catalog_paths

    from mwpc_exact.language_coverage import tokenizations

    emissions = (b"a", b"b", b"ab", b"a", b"\xc3", b"\xa9", b"\xc3\xa9")
    words = (b"ab", b"\xc3\xa9")
    for slots in (1, 2):
        state = state_for(words, emissions, (tuple(range(len(emissions))),) * slots, ())
        exact = {
            path
            for path in product(range(len(emissions)), repeat=slots)
            if b"".join(emissions[t] for t in path) in words
        }
        assert set(independent_catalog_paths(words, emissions, slots)) == exact
        assert set(tokenizations(state, words)) == exact


def test_verification_subprocess_forbids_every_optimization_import(tmp_path):
    import json
    import subprocess
    import sys

    proof = probability_partition(
        basic(), max_oracle_calls=64, requested_tv=Fraction(), backend=ExactBackend.PYTHON
    )
    path = tmp_path / "proof.json"
    path.write_text(json.dumps(proof))
    code = """
import sys,importlib.abc,json
class Block(importlib.abc.MetaPathFinder):
 def find_spec(self,name,path=None,target=None):
  if name in {'mwpc_exact.mass_solver','mwpc_exact.budgeted_commit',
              'mwpc_exact.reference.budgeted_parser','mwpc_exact.conflict_commit'}:
   raise AssertionError('optimizer imported: '+name)
sys.meta_path.insert(0,Block())
from mwpc_exact.mass_certificate import verify_mass_proof
result=verify_mass_proof(json.load(open(sys.argv[1])))
assert result.lower>0
"""
    run = subprocess.run([sys.executable, "-c", code, str(path)], capture_output=True, text=True)
    assert run.returncode == 0, run.stderr


def recursive_probability(rows=((0, 1, 2, 3, 4, 5),) * 2, eos=None):
    from mwpc_exact.reference.byte_grammars import _SourceGrammarBuilder
    from mwpc_exact.reference.normalization import normalize_to_cnf

    builder = _SourceGrammarBuilder(("S",), start="S")
    builder.rule("S", b"[]")
    builder.rule("S", b"[", "S", b"]")
    state = state_for(
        (b"[]",), (b"[", b"]", b"[]", b"[[", b"]]", b"[]", b"a", None), rows, (), eos=eos
    )
    state = replace(state, grammar=normalize_to_cnf(builder.build()).grammar)
    return ProbabilityInput(state, tuple(tuple(Fraction(1, 100) for _ in row) for row in rows))


def test_recursive_alphabet_coverage_certifies_all_vocabulary_aliases_without_finite_yields():
    from mwpc_exact.language_coverage import terminal_alphabet_coverage

    predictive = recursive_probability()
    proof = probability_partition(
        predictive,
        language_coverage=terminal_alphabet_coverage(predictive.state.grammar),
        scope=PosteriorScope.FULL,
        requested_tv=Fraction(),
        backend=ExactBackend.PYTHON,
    )
    result = verify_mass_proof(proof)
    exact = exact_distribution(predictive)
    assert result.lower == sum(exact.values(), Fraction()) > 0
    assert result.omitted == Fraction(2491, 2500) and result.outside_valid_upper == 0
    assert result.tv_bound(PosteriorScope.FULL) == 0
    assert result.sample(Random(1), scope=PosteriorScope.FULL, max_tv=Fraction()) in exact


def test_alphabet_coverage_rejects_deleted_alias_and_malformed_alphabet():
    from mwpc_exact.language_coverage import check_language_coverage, terminal_alphabet_coverage

    state = recursive_probability().state
    coverage = terminal_alphabet_coverage(state.grammar)
    incomplete = recursive_probability(rows=((0, 1, 2, 3, 4),) * 2).state
    with pytest.raises(ValueError, match="missing"):
        check_language_coverage(incomplete, coverage)
    for alphabet in ([91.0, 93], [True, 93], [91, 93, 93], [91, 93, 97]):
        with pytest.raises((ValueError, TypeError)):
            check_language_coverage(state, {**coverage, "alphabet": alphabet})
    with pytest.raises(ValueError, match="ABSENT"):
        eos_state = recursive_probability(
            rows=((*range(6), 7),) * 2,
            eos=EOSPolicy(EOSMode.OPTIONAL, (7,), 7),
        ).state
        check_language_coverage(eos_state, coverage)


def test_independent_recursive_application_control_agrees_with_original_token_validator():
    from scripts.exact_commit.run_probability_probes import independent_recursive_paths

    emissions = (b"[", b"]", b"[]", b"[[", b"]]", b"[]", b"a", None)
    for slots in (1, 2):
        state = recursive_probability(rows=(tuple(range(7)),) * slots).state
        for prefix in ("", "[", "[[["):
            case = {"slots": slots, "probe": {"prefix": prefix, "suffix": ""}}
            relevant = set(range(6))
            actual = set(independent_recursive_paths(case, emissions, relevant))
            expected = set()
            # An independent CFG recognizer validates the full emitted byte word.
            from mwpc_exact.reference.recognizer import recognizes_cnf

            for path in product(range(7), repeat=slots):
                raw = prefix.encode() + b"".join(emissions[t] for t in path)
                if recognizes_cnf(state.grammar, tuple(raw)):
                    expected.add(path)
            assert actual == expected
