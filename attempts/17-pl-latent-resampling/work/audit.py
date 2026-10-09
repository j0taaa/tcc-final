"""Exact independent JSON/path and policy-gradient oracles; not benchmarks."""

from __future__ import annotations

import argparse
import itertools
import json
from collections import defaultdict
from dataclasses import dataclass
from fractions import Fraction as Q
from pathlib import Path
from random import Random
from time import perf_counter

from resampling import BaseRejection, Problem, RoundedProfiles, SingleTilt, TangentMixture

from mwpc_exact.cfg_posterior import compile_cfg_sampler
from mwpc_exact.eos_policy import EOSMode, EOSPolicy
from mwpc_exact.mass_certificate import ProbabilityInput
from mwpc_exact.reference.json_grammar import json_source_grammar
from mwpc_exact.reference.normalization import normalize_to_cnf
from mwpc_exact.state import SelectionInput
from mwpc_exact.support import SupportPolicy, build_per_position_support
from mwpc_exact.tokenizer_bytes import CompositionalByteLevelAdapter
from mwpc_exact.types import SupportKind


def fixture(n, weighted=False, values=(b"0", b"1"), fixed=None):
    emissions = (b"[", b"]", b",", *values)
    rows = [(0,)]
    for i in range(n):
        if i:
            rows.append((2,))
        rows.append(tuple(range(3, len(emissions))))
    rows.append((1,))
    canvas = tuple(row[0] if len(row) == 1 else None for row in rows)
    if fixed:
        canvas = tuple(fixed.get(i, t) for i, t in enumerate(canvas))
        rows = [
            (token,) if token is not None else row for token, row in zip(canvas, rows, strict=True)
        ]
    support = build_per_position_support(
        canvas=canvas,
        policy=SupportPolicy(kind=SupportKind.EXPLICIT, vocabulary_size=len(emissions)),
        explicit_support=dict(enumerate(rows)),
    )
    source = json_source_grammar()
    state = SelectionInput(
        normalize_to_cnf(source).grammar,
        canvas,
        (),
        support,
        CompositionalByteLevelAdapter(emissions),
        EOSPolicy(EOSMode.ABSENT),
    )
    rng = Random(20261008 + n)
    weights = [
        ([rng.randrange(1, 8) for _ in row] if weighted else [1] * len(row)) for row in support.rows
    ]
    probabilities = tuple(tuple(Q(x, sum(row)) for x in row) for row in weights)
    return compile_cfg_sampler(source, state), ProbabilityInput(state, probabilities)


def enumerated_paths(data):
    """JSON's own recognizer, no forest or project parser used for membership."""
    accepted = {}
    maps = [
        dict(zip(row, p, strict=True))
        for row, p in zip(data.state.support.rows, data.probabilities, strict=True)
    ]
    for path in itertools.product(*data.state.support.rows):
        text = b"".join(data.state.tokenizer_adapter.emissions[t] for t in path)
        try:
            json.loads(
                text.decode("utf-8"), parse_constant=lambda s: (_ for _ in ()).throw(ValueError(s))
            )
        except (ValueError, UnicodeDecodeError):
            continue
        accepted[path] = Q(1)
        for i, token in enumerate(path):
            accepted[path] *= maps[i][token]
    return accepted


def direct_pl(path, order, free, rates, indices):
    remaining, value = set(free), Q(1)
    for chosen in order:
        numerator = rates[chosen][indices[chosen][path[chosen]]]
        denominator = sum((rates[i][indices[i][path[i]]] for i in remaining), Q())
        value *= numerator / denominator
        remaining.remove(chosen)
    return value


def forest_law(base):
    """Integrate every categorical branch in the implemented top-down sampler."""
    laws = {}
    plan = base.plan
    for node in plan.order:
        law = defaultdict(Q)
        if not base.inside[node]:
            laws[node] = law
            continue
        for term in plan.terms[node]:
            probability = Q(plan.term_mass(term, base.integers, base.inside), base.inside[node])
            if not probability:
                continue
            if term.choice is not None:
                i, index = term.choice
                law[((i, plan.state.support.rows[i][index]),)] += probability
            elif not term.children:
                law[()] += probability
            else:
                left, right = term.children
                for a, pa in laws[left].items():
                    for b, pb in laws[right].items():
                        law[tuple(sorted(a + b))] += probability * pa * pb
        laws[node] = law
    return {
        tuple(token for _, token in pairs): probability
        for pairs, probability in laws[plan.root].items()
    }


def check_problem(
    p,
    paths,
    dyadic_unaries=False,
    tight_bounds=False,
    single_tilt=False,
    dyadic_coefficients=False,
    strengthened=False,
):
    target = {
        y: w * direct_pl(y, p.order, p.free, p.rates, p.indices)
        for y, w in paths.items()
        if all(y[i] == token for i, token in p.observed.items())
    }
    z = sum(target.values(), Q())
    if tight_bounds:
        tightened = p.tightened()
        assert tightened.L == min(p.total_rate(y) for y in target)
        assert tightened.H == max(p.total_rate(y) for y in target)
    mixture = TangentMixture(
        p,
        dyadic_unaries=dyadic_unaries,
        tight_bounds=tight_bounds,
        dyadic_coefficients=dyadic_coefficients,
        certify_scale=strengthened,
    )
    rejection = BaseRejection(p, tight_bounds=tight_bounds)
    proposal = defaultdict(Q)
    for alpha, _, component in mixture.components:
        law = forest_law(component)
        for path, probability in law.items():
            proposal[path] += alpha * component.mass * probability / mixture.mass
    accepted = {y: prob * mixture.acceptance(y) for y, prob in proposal.items()}
    success = sum(accepted.values(), Q())
    assert {y: w / success for y, w in accepted.items()} == {y: w / z for y, w in target.items()}
    bound = 1 if mixture.constant else 2 * len(mixture.components) + 1
    assert 1 / success <= bound
    base_law = forest_law(rejection.base)
    base_accepted = {y: prob * p.likelihood(y) / rejection.upper for y, prob in base_law.items()}
    base_success = sum(base_accepted.values(), Q())
    assert mixture.rejection_normalizer / z == 1 / success
    assert rejection.rejection_normalizer / z == 1 / base_success
    assert {y: w / base_success for y, w in base_accepted.items()} == {
        y: w / z for y, w in target.items()
    }
    if p.order and p.hidden:
        assert RoundedProfiles(p, dyadic_root=strengthened).law() == {
            y: w / z for y, w in target.items()
        }
    if single_tilt:
        single = SingleTilt(
            p, dyadic_coefficients=dyadic_coefficients, precise_envelope=strengthened
        )
        law = forest_law(single.base)
        accepted_single = {y: prob * single.acceptance(y) for y, prob in law.items()}
        single_success = sum(accepted_single.values(), Q())
        assert all(0 < single.acceptance(y) <= 1 for y in target)
        assert {y: w / single_success for y, w in accepted_single.items()} == {
            y: w / z for y, w in target.items()
        }
        assert single.rejection_normalizer / z == 1 / single_success
    for path, weight in target.items():
        assert p.likelihood(path) == weight / paths[path]
        if not mixture.constant:
            assert (
                p.likelihood(path)
                <= mixture.rejection_factor * mixture.envelope(path)
                <= bound * p.likelihood(path)
            )
    for method in (mixture, rejection):
        for seed in range(2):
            path, _ = method.sample(Random(seed))
            assert path in target
    return len(target)


def correctness(
    max_n=4,
    dyadic_unaries=False,
    tight_bounds=False,
    single_tilt=False,
    dyadic_coefficients=False,
    strengthened=False,
):
    events = paths_checked = 0
    for n in range(1, max_n + 1):
        for weighted in (False, True):
            plan, data = fixture(n, weighted)
            paths = enumerated_paths(data)
            free = tuple(i for i, t in enumerate(data.state.canvas) if t is None)
            for power in (1, 2):
                rates = tuple(tuple(q**power for q in row) for row in data.probabilities)
                for k in range(1, n):
                    for order in itertools.permutations(free, k):
                        for tokens in itertools.product(
                            *(data.state.support.rows[i] for i in order)
                        ):
                            p = Problem(
                                plan,
                                data.probabilities,
                                rates,
                                order,
                                dict(zip(order, tokens, strict=True)),
                            )
                            paths_checked += check_problem(
                                p,
                                paths,
                                dyadic_unaries,
                                tight_bounds,
                                single_tilt,
                                dyadic_coefficients,
                                strengthened,
                            )
                            events += 1
            print(
                f"exact-law fixture n={n}, weighted={weighted}: cumulative {events} events",
                flush=True,
            )
    for values in [
        (b"0", b"0", b"1"),
        (b"1", b"10"),
        (b"0", b"[0]", b"[1]"),
        (b"0", b"1", b"oops"),
    ]:
        plan, data = fixture(2, True, values)
        paths = enumerated_paths(data)
        free = tuple(i for i, t in enumerate(data.state.canvas) if t is None)
        rates = tuple(tuple(q**2 for q in row) for row in data.probabilities)
        for i in free:
            for token in data.state.support.rows[i]:
                if not any(path[i] == token for path in paths):
                    continue
                paths_checked += check_problem(
                    Problem(plan, data.probabilities, rates, (i,), {i: token}),
                    paths,
                    dyadic_unaries,
                    tight_bounds,
                    single_tilt,
                    dyadic_coefficients,
                    strengthened,
                )
                events += 1
    plan, data = fixture(2)
    paths = enumerated_paths(data)
    rates = tuple(tuple(Q(1) for _ in row) for row in data.probabilities)
    for order in [(), (1,), (1, 3)]:
        p = Problem(plan, data.probabilities, rates, order, {i: 3 for i in order})
        paths_checked += check_problem(
            p, paths, dyadic_unaries, tight_bounds, single_tilt, dyadic_coefficients, strengthened
        )
        events += 1
    return {"events": events, "conditional_original_paths": paths_checked, "exact_mismatches": 0}


@dataclass
class Dual:
    value: Q
    gradient: tuple

    def __add__(self, other):
        if not isinstance(other, Dual):
            other = Dual(Q(other), (Q(),) * len(self.gradient))
        return Dual(
            self.value + other.value,
            tuple(a + b for a, b in zip(self.gradient, other.gradient, strict=True)),
        )

    __radd__ = __add__

    def __mul__(self, other):
        if not isinstance(other, Dual):
            other = Dual(Q(other), (Q(),) * len(self.gradient))
        return Dual(
            self.value * other.value,
            tuple(
                a * other.value + b * self.value
                for a, b in zip(self.gradient, other.gradient, strict=True)
            ),
        )

    __rmul__ = __mul__

    def __truediv__(self, other):
        return Dual(
            self.value / other.value,
            tuple(
                (a * other.value - b * self.value) / other.value**2
                for a, b in zip(self.gradient, other.gradient, strict=True)
            ),
        )


def outer(vector):
    return tuple(tuple(a * b for b in vector) for a in vector)


def moments(rows, n):
    mean = tuple(sum((prob * score[i] for prob, score in rows), Q()) for i in range(n))
    covariance = tuple(
        tuple(
            sum((prob * score[i] * score[j] for prob, score in rows), Q()) - mean[i] * mean[j]
            for j in range(n)
        )
        for i in range(n)
    )
    return mean, covariance


def gradient_case(n, weighted, power, k, constrained=False):
    rng = Random(20261008 + n)
    probabilities = []
    for _ in range(n):
        a, b = (rng.randrange(1, 8), rng.randrange(1, 8)) if weighted else (1, 1)
        probabilities.append(Q(b, a + b))
    groups = defaultdict(list)
    objective = Dual(Q(), (Q(),) * n)
    dropped = []
    token_events = []
    normalizer = Dual(Q(), (Q(),) * n)
    for bits in itertools.product((0, 1), repeat=n):
        # The finite regular (hence LL(1)-representable) language of binary
        # JSON arrays with at least one 1 has a nonconstant grammar normalizer.
        if constrained and not any(bits):
            continue
        qs = []
        for i, bit in enumerate(bits):
            probability = probabilities[i] if bit else 1 - probabilities[i]
            derivative = probabilities[i] * (1 - probabilities[i]) * (1 if bit else -1)
            qs.append(Dual(probability, tuple(derivative if i == j else Q() for j in range(n))))
        rates = [q * q if power == 2 else q for q in qs]
        joint_tokens = Dual(Q(1), (Q(),) * n)
        for q in qs:
            joint_tokens *= q
        token_events.append((bits, rates, joint_tokens))
        normalizer += joint_tokens
    for bits, rates, joint_tokens in token_events:
        for order in itertools.permutations(range(n), k):
            probability = joint_tokens / normalizer
            remaining = set(range(n))
            inverse_sums = [Q()] * n
            for chosen in order:
                denominator = sum((rates[i] for i in remaining), Dual(Q(), (Q(),) * n))
                probability *= rates[chosen] / denominator
                for i in remaining:
                    inverse_sums[i] += 1 / denominator.value
                remaining.remove(chosen)
            reward = sum(bits[i] for i in order)
            objective += probability * reward
            # Independent closed-form complete score, including selection.
            score = tuple(
                reward
                * (
                    (bits[i] - probabilities[i])
                    * (1 + power * (i in order) - power * rates[i].value * inverse_sums[i])
                    - normalizer.gradient[i] / normalizer.value
                )
                for i in range(n)
            )
            assert score == tuple(reward * g / probability.value for g in probability.gradient)
            key = (order, tuple(bits[i] for i in order))
            groups[key].append((probability.value, score))
            dropped.append(
                (
                    probability.value,
                    tuple(
                        reward * (bits[i] - probabilities[i]) if i in order else Q()
                        for i in range(n)
                    ),
                )
            )
    rows = [entry for group in groups.values() for entry in group]
    assert sum((p for p, _ in rows), Q()) == 1
    mean, original = moments(rows, n)
    assert mean == objective.gradient
    observable, replicas = [], []
    for entries in groups.values():
        mass = sum((p for p, _ in entries), Q())
        conditional_mean = tuple(
            sum((p * score[i] for p, score in entries), Q()) / mass for i in range(n)
        )
        observable.append((mass, conditional_mean))
        for p, a in entries:
            for q, b in entries:
                replicas.append(
                    (p * q / mass, tuple((x + y) / 2 for x, y in zip(a, b, strict=True)))
                )
    rb_mean, observed = moments(observable, n)
    replica_mean, replica_cov = moments(replicas, n)
    assert mean == rb_mean == replica_mean
    hidden = tuple(tuple(original[i][j] - observed[i][j] for j in range(n)) for i in range(n))
    assert replica_cov == tuple(
        tuple(observed[i][j] + hidden[i][j] / 2 for j in range(n)) for i in range(n)
    )
    v_total = sum((original[i][i] for i in range(n)), Q())
    v_hidden = sum((hidden[i][i] for i in range(n)), Q())
    beta = v_hidden / v_total if v_total else Q()
    wrong_mean, _ = moments(dropped, n)
    return {
        "n": n,
        "weighted": weighted,
        "grammar": "at_least_one_1" if constrained else "all_binary_arrays",
        "rate_power": power,
        "k": k,
        "observable_events": len(groups),
        "complete_outcomes": len(rows),
        "variance_trace": str(v_total),
        "latent_fraction": str(beta),
        "one_replica_relative_variance_reduction": float(beta / 2),
        "max_relative_cost_overhead_for_benefit": float(beta / (2 - beta)),
        "dropping_latent_score_is_biased": wrong_mean != mean,
    }


def gradient_audit():
    return [
        gradient_case(n, weighted, power, k, constrained)
        for n in (2, 3, 4)
        for weighted in (False, True)
        for power in (1, 2)
        for k in range(1, n)
        for constrained in (False, True)
    ]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--dyadic", action="store_true")
    parser.add_argument("--tight-bounds", action="store_true")
    parser.add_argument("--single-tilt", action="store_true")
    parser.add_argument("--dyadic-coefficients", action="store_true")
    parser.add_argument("--strengthened", action="store_true")
    args = parser.parse_args()
    start = perf_counter()
    report = {
        "scope": "exact finite correctness oracles, no performance or training claim",
        "numeric_variant": "dyadic" if args.dyadic else "reference",
        "tight_bounds": args.tight_bounds,
        "single_tilt": args.single_tilt,
        "dyadic_coefficients": args.dyadic_coefficients,
        "strengthened": args.strengthened,
        "correctness": correctness(
            dyadic_unaries=args.dyadic,
            tight_bounds=args.tight_bounds,
            single_tilt=args.single_tilt,
            dyadic_coefficients=args.dyadic_coefficients,
            strengthened=args.strengthened,
        ),
        "gradient": gradient_audit(),
        "elapsed_seconds": perf_counter() - start,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x") as stream:
        stream.write(json.dumps(report, indent=2) + "\n")
    print(
        json.dumps(
            {
                "correctness": report["correctness"],
                "gradient_cases": len(report["gradient"]),
                "elapsed_seconds": report["elapsed_seconds"],
            }
        )
    )


if __name__ == "__main__":
    main()
