"""A77 frozen finite oracle. No model, GPU, or measured clocks."""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import defaultdict
from fractions import Fraction as F
from itertools import permutations, product
from math import factorial, prod
from pathlib import Path
from random import Random
from unittest.mock import patch

from mwpc_exact.cfg_posterior import compile_cfg_sampler
from mwpc_exact.eos_policy import EOSMode, EOSPolicy
from mwpc_exact.mass_certificate import ProbabilityInput
from mwpc_exact.reference.byte_grammars import _SourceGrammarBuilder
from mwpc_exact.reference.normalization import normalize_to_cnf
from mwpc_exact.state import SelectionInput
from mwpc_exact.support import SupportPolicy, build_per_position_support
from mwpc_exact.tokenizer_bytes import CompositionalByteLevelAdapter
from mwpc_exact.types import SupportKind

EMISSIONS = (b"a", b"a", b"b", b"(", b")", b"+", b"*", b"(a")
CASES = ((2, 1, None), (3, 1, None), (2, 4, None), (2, 5, None), (2, 5, 3))


def ast(word):
    """Independent byte recognizer; internal AST children remain ordered."""

    def parse(i):
        if word[i : i + 1] in (b"a", b"b"):
            return word[i : i + 1].decode(), i + 1
        if word[i : i + 1] != b"(":
            raise ValueError
        left, i = parse(i + 1)
        if word[i : i + 1] not in (b"+", b"*"):
            raise ValueError
        op = word[i : i + 1].decode()
        right, i = parse(i + 1)
        if word[i : i + 1] != b")":
            raise ValueError
        return (op, left, right), i + 1

    value, end = parse(0)
    if end != len(word):
        raise ValueError
    return repr(value)


def grammar():
    b = _SourceGrammarBuilder(("E", "T"), start="E")
    b.rule("E", b"a")
    b.rule("E", b"b")
    b.rule("E", b"(", "E", "T", "E", b")")
    b.rule("T", b"+")
    b.rule("T", b"*")
    return b.build()


def bound(m, n, delta):
    if delta >= 1:
        return None
    return m * n * delta**2 / (2 * (1 - delta)) + 2 * (m - 1) * n**2 * delta**2 / (1 - delta) ** 2


def fixture(m, n, seed, bias):
    rng = Random(seed)
    bases = [[rng.randrange(1, 10) for _ in EMISSIONS] for _ in range(n)]
    signs = [[rng.choice((-1, 1)) for _ in EMISSIONS] for _ in range(n)]
    rows = []
    for j in range(m):
        coefficient = F(2 * j - (m - 1), m - 1)
        module = []
        for base, sign in zip(bases, signs, strict=True):
            weights = [b * (1 + bias * coefficient * s) for b, s in zip(base, sign, strict=True)]
            module.append(tuple(w / sum(weights) for w in weights))
        rows.append(tuple(module))
    return tuple(rows)


def mean_rows(weights):
    m, n = len(weights), len(weights[0])
    return tuple(
        tuple(sum(weights[j][k][v] for j in range(m)) / m for v in range(8)) for k in range(n)
    )


def input_data(source, rows, pin):
    n = len(rows)
    canvas = (pin,) + (None,) * (n - 1)
    support = build_per_position_support(
        canvas=canvas,
        policy=SupportPolicy(kind=SupportKind.EXPLICIT, vocabulary_size=8),
        explicit_support={k: tuple(range(8)) for k in range(n)},
    )
    state = SelectionInput(
        normalize_to_cnf(source).grammar,
        canvas,
        (),
        support,
        CompositionalByteLevelAdapter(EMISSIONS),
        EOSPolicy(EOSMode.ABSENT),
    )
    # Fixed IDs are interventions in the library input. Their original head
    # probabilities cancel within each module's conditional distribution.
    return ProbabilityInput(state, ((F(1),) if pin is not None else rows[0], *rows[1:]))


def enumerate_module(rows, pin):
    accepted = {}
    for path in product(range(8), repeat=len(rows)):
        if pin is not None and path[0] != pin:
            continue
        try:
            ast(b"".join(EMISSIONS[t] for t in path))
        except ValueError:
            continue
        accepted[path] = prod(rows[k][t] for k, t in enumerate(path))
    return accepted


def normalize(law):
    mass = sum(law.values(), F())
    assert mass > 0
    return {x: w / mass for x, w in law.items()}


def tv(left, right):
    return (
        sum((abs(left.get(x, F()) - right.get(x, F())) for x in left.keys() | right.keys()), F())
        / 2
    )


class Branch(Exception):
    def __init__(self, weights):
        self.weights = weights


def sampler_law(posterior):
    """Explore all categorical branches, weighting by their exact integer mass."""
    pending = [((), F(1))]
    result = defaultdict(F)
    explored = 0
    while pending:
        choices, mass = pending.pop()
        transcript = iter(choices)

        def choose(weights, _rng, transcript=transcript):
            if len(weights) == 1:
                return 0
            index = next(transcript, None)
            if index is None:
                raise Branch(weights)
            assert weights[index] > 0
            return index

        try:
            with patch("mwpc_exact.cfg_posterior._categorical", choose):
                output = posterior.sample(Random(0))
            result[output] += mass
        except Branch as branch:
            total = sum(branch.weights)
            for i, weight in enumerate(branch.weights):
                if weight:
                    pending.append(((*choices, i), mass * F(weight, total)))
        explored += 1
        assert explored <= 200_000, "resource_refusal_branch_cap"
    assert sum(result.values()) == 1
    return dict(result), explored


class CountRandom(Random):
    def __init__(self, seed):
        super().__init__(seed)
        self.bits = 0

    def getrandbits(self, k):
        self.bits += k
        return super().getrandbits(k)


def run_case(index, m, n, pin, bias):
    source = grammar()
    w = fixture(m, n, 770101 + index, bias)
    r = mean_rows(w)
    # Competent same-mean control: explicit unary pooling before grammar.
    manual = tuple(
        tuple(sum(column, F()) / m for column in zip(*(w[j][k] for j in range(m)), strict=True))
        for k in range(n)
    )
    assert r == manual
    delta = max(abs(w[j][k][v] / r[k][v] - 1) for j, k, v in product(range(m), range(n), range(8)))
    d = bound(m, n, delta)
    assert d is not None
    references = [enumerate_module(rows, pin) for rows in w]
    ref_q = enumerate_module(r, pin)
    assert all(set(rows) == set(ref_q) for rows in references)
    data = input_data(source, r, pin)
    plan = compile_cfg_sampler(source, data.state)
    posterior = plan.evaluate(data)
    mass = sum(ref_q.values(), F())
    assert posterior.valid_mass == mass / (r[0][pin] if pin is not None else 1)
    q = normalize(ref_q)
    assert sampler_law(posterior)[0] == q
    for k, domain in enumerate(data.state.support.rows):
        assert posterior.marginals[k] == tuple(
            sum(p for x, p in q.items() if x[k] == v) for v in domain
        )
    for rows, reference in zip(w, references, strict=True):
        original = plan.evaluate(input_data(source, rows, pin))
        assert original.valid_mass == sum(reference.values(), F()) / (
            rows[0][pin] if pin is not None else 1
        )
        assert sampler_law(original)[0] == normalize(reference)

    p_joint, q_joint, p_orbits, q_orbits, ratios = {}, {}, defaultdict(F), defaultdict(F), {}
    for x in product(ref_q, repeat=m):
        pw = prod(references[j][module] for j, module in enumerate(x))
        qw = prod(ref_q[module] for module in x)
        p_joint[x], q_joint[x] = pw, qw
        orbit = tuple(sorted(x))
        p_orbits[orbit] += pw
        q_orbits[orbit] += qw
    for orbit in p_orbits:
        a = sum(
            (
                prod(
                    w[j][k][orbit[pi[j]][k]] / r[k][orbit[pi[j]][k]]
                    for j, k in product(range(m), range(n))
                )
                for pi in permutations(range(m))
            ),
            F(),
        ) / factorial(m)
        assert a == p_orbits[orbit] / q_orbits[orbit]
        ratios[orbit] = a
    # Check exp/log claims independently with 80-digit Decimal; exact TVs and
    # exact rational D/4 remain the certified comparison used in the gate.
    from decimal import Decimal, localcontext

    def decimal(value):
        return Decimal(value.numerator) / Decimal(value.denominator)

    with localcontext() as context:
        context.prec = 80
        a_bound = F(m * n) * delta**2 / (2 * (1 - delta))
        b_bound = d - a_bound
        assert all(
            -decimal(a_bound) <= decimal(a).ln() <= decimal(b_bound) for a in ratios.values()
        )
        assert (decimal(max(ratios.values())) / decimal(min(ratios.values()))).ln() <= decimal(d)

    def project(joint, condition=False):
        result = defaultdict(F)
        for x, weight in joint.items():
            sigma = tuple(sorted(ast(b"".join(EMISSIONS[t] for t in module)) for module in x))
            if not condition or len(set(sigma)) == 1:
                result[sigma] += weight
        return normalize(result), sum(result.values(), F()) / sum(joint.values(), F())

    p_sem, _ = project(p_joint)
    q_sem, _ = project(q_joint)
    p_cond, pc = project(p_joint, True)
    q_cond, qc = project(q_joint, True)
    errors = [tv(p_sem, q_sem), tv(p_cond, q_cond)]
    assert all(error <= d / 4 for error in errors)
    # A sampler of the rare conditional uses these conditional tables, never H.
    rng = CountRandom(770201 + index)
    emitted = []
    for _ in range(32):
        pool = tuple(posterior.sample(rng) for _ in range(m))
        assert all(module in ref_q for module in pool)
        assert pin is None or all(module[0] == pin for module in pool)
        emitted.append(pool)
    max_bits = max(abs(v).bit_length() for row in posterior._weights for v in row)
    max_bits = max(max_bits, *(abs(v).bit_length() for v in posterior._inside))
    return {
        "case": index,
        "m": m,
        "n": n,
        "pin": pin,
        "bias": str(bias),
        "module_original_paths": len(q),
        "id_orbits": len(ratios),
        "semantic_bags": len(p_sem),
        "delta": str(delta),
        "D_over_4": str(d / 4),
        "tv_text": str(tv(normalize(p_joint), normalize(q_joint))),
        "tv_sem": str(errors[0]),
        "tv_sem_conditioned": str(errors[1]),
        "condition_mass_p": str(pc),
        "condition_mass_q": str(qc),
        "certificate_covers_epsilon": d <= F(1, 25),
        "charts_candidate": 1,
        "charts_same_mean_control": 1,
        "charts_exact_heterogeneous": m,
        "topology_compilations_all_controls": 1,
        "chart_cells": len(plan.terms),
        "chart_alternatives": plan.alternatives,
        "chart_max_integer_bits": max_bits,
        "rng_bits_32_pools": rng.bits,
        "output_ids": 32 * m * n,
        "output_sha256": hashlib.sha256(json.dumps(emitted).encode()).hexdigest(),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = {"scope": "finite_rational_correctness_not_novelty", "cases": [], "bernoulli": []}
    # The maintained API records internal telemetry. Disable those readings;
    # this oracle performs no benchmark and requires no GPU or timing window.
    with patch("mwpc_exact.cfg_posterior.perf_counter", return_value=0):
        for i, (m, n, pin) in enumerate(CASES):
            for bias in (F(1, 100), F(1, 5)):
                result["cases"].append(run_case(i, m, n, pin, bias))
    for delta in (F(1, 100), F(1, 10), F(1, 2)):
        p = {
            (x, y): (F(1, 2) + (1 if x else -1) * delta / 2)
            * (F(1, 2) - (1 if y else -1) * delta / 2)
            for x, y in product(range(2), repeat=2)
        }
        q = {x: F(1, 4) for x in p}
        ps, qs = defaultdict(F), defaultdict(F)
        for pair in p:
            ps[sum(pair)] += p[pair]
            qs[sum(pair)] += q[pair]
        assert tv(p, q) == delta / 2 + delta**2 / 4
        assert tv(ps, qs) == delta**2 / 2
        result["bernoulli"].append(
            {"delta": str(delta), "text_tv": str(tv(p, q)), "bag_tv": str(tv(ps, qs))}
        )
    # Rare invariant C: both categorical modules equal, with two rare symbols.
    base, delta = F(1, 1000), F(1, 10)
    rows = (
        (base * (1 + delta), base * (1 - delta), 1 - 2 * base),
        (base * (1 - delta), base * (1 + delta), 1 - 2 * base),
    )
    p = {(x, x): rows[0][x] * rows[1][x] for x in (0, 1)}
    q = {(x, x): base**2 for x in (0, 1)}
    assert tv(normalize(p), normalize(q)) == 0
    result["rare_condition"] = {
        "p_mass": str(sum(p.values())),
        "q_mass": str(sum(q.values())),
        "conditional_tv": "0",
        "sampler": "conditioned_tables_not_unconditional_chart",
    }
    # Stated recurrence: lengths 1 mod 4, operator weights folded at each split.
    splits = sum((253 - length + 1) * ((length - 1) // 4) for length in range(5, 254, 4))
    assert splits == 168672
    result["split_terms_n253"] = {
        "one_chart": splits,
        "eight_charts": 8 * splits,
        "kind": "recurrence_count_not_timing",
    }
    result["status"] = "PASS"
    with args.output.open("x") as stream:
        json.dump(result, stream, indent=2, sort_keys=True)
        stream.write("\n")


if __name__ == "__main__":
    main()
