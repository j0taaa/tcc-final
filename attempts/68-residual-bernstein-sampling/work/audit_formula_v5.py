"""Independent exact checks of classical compact controls, no timing campaign."""

import hashlib
import json
import subprocess
import sys
from collections import Counter
from dataclasses import asdict
from fractions import Fraction as F
from itertools import product
from math import comb, isqrt
from pathlib import Path

from audit import fixtures, independent_center
from audit_runtime_v4 import Prefix, fraction
from formula_control_v5 import (
    CompiledFactory,
    FormulaStats,
    Piecewise,
    direct_plan,
    direct_sample,
    hg_interval,
    original_specs,
)
from runtime_v4 import Bits, ResourceFail, bernoulli, rational

HERE = Path(__file__).resolve().parent


def analytic_second(name, x):
    return {
        "constant": F(),
        "affine": F(),
        "quadratic": F(1, 2),
        "cubic": 3 * x / 2,
        "spline": 3 * max(F(), x - F(1, 2)) / 2,
        "reflected_spline": 3 * max(F(), F(1, 2) - x) / 2,
    }[name]


def main(destination):
    counts, observed_work = Counter(), Counter()
    records = []
    old = {name: (fn, curvature, h) for name, fn, curvature, h in fixtures()}
    specs = original_specs()
    for spec in specs:
        fn = old[spec.name][0]
        for n in (16, 64, 256):
            for i in range(n + 1):
                x = F(i, n)
                assert fraction(spec.value(rational(x))) == fn(x)
                assert fraction(spec.second(rational(x))) == analytic_second(spec.name, x)
                counts["piece_values_and_derivatives"] += 1
    for total in (5, 16, 64):
        for successes in range(total + 1):
            for draws in sorted({0, 1, total // 2, total}):
                left, right = max(0, draws - (total - successes)), min(draws, successes)
                for cut in range(left - 1, right + 1):
                    for lo, hi in ((left, cut), (cut + 1, right), (cut, cut), (2, 1)):
                        target = sum(
                            (
                                F(
                                    comb(draws, i) * comb(total - draws, successes - i),
                                    comb(total, successes),
                                )
                                for i in range(max(left, lo), min(right, hi) + 1)
                            ),
                            F(),
                        )
                        actual = hg_interval(total, successes, draws, lo, hi, FormulaStats(), {})
                        assert fraction(actual) == target
                        counts["hypergeometric_interval_masses"] += 1
    for spec in specs:
        fn, _curvature, h = old[spec.name]
        for analytic in (False, True):
            compiled = CompiledFactory(spec, analytic=analytic)
            degrees = (16, 64, 256) if h else (16,)

            def center(n, x, fn=fn, name=spec.name, analytic=analytic):
                if not analytic:
                    return independent_center(fn, n, x)
                return fn(x) - x * (1 - x) * analytic_second(name, x) / (2 * (n - 1))

            for n in degrees:
                row = [center(n // 4, F(i, n // 4)) for i in range(n // 4 + 1)] if n > 16 else []
                for k in range(n + 1):
                    if n == 16:
                        delta = h / (n * isqrt(n))
                        target = (center(n, F(k, n)) - delta) / (1 - 2 * delta)
                    else:
                        m = n // 4
                        elevated = sum(
                            (
                                comb(m, i) * comb(3 * m, k - i) * row[i]
                                for i in range(max(0, k - 3 * m), min(m, k) + 1)
                            ),
                            F(),
                        ) / comb(n, k)
                        target = F(1, 2) + (center(n, F(k, n)) - elevated) / (
                            7 * h / (4 * m * isqrt(m))
                        )
                    draw = compiled.vote(n, k, Bits(n + k))
                    assert fraction(compiled.scalars[n, k]) == target
                    assert 0 <= target <= 1 and draw.bit in (0, 1)
                    assert draw.stats.f_requests == 0
                    observed_work["formula_evaluations"] += draw.stats.formula_evaluations
                    observed_work["interval_terms"] += draw.stats.interval_terms
                    observed_work["compiled_segments"] += draw.stats.compiled_segments
                    counts["compiled_conditional_kernels"] += 1
            cached = CompiledFactory(spec, analytic=analytic, reuse=True)
            n = 64 if h else 16
            cached.vote(n, n // 2, Bits(1))
            second = cached.vote(n, n // 2, Bits(2))
            assert second.stats.scalar_cache_hits == 1
            assert second.stats.formula_evaluations == second.stats.interval_requests == 0
            assert second.stats.auxiliary_bits > 0
            counts["compiled_cache_replays"] += 1
            for p in (F(1, 4), F(1, 2), F(3, 4)):
                for seed in range(8):
                    factory = CompiledFactory(spec, analytic=analytic)
                    source_rng, aux_rng, level_rng = (
                        Bits(seed ^ 0x124),
                        Bits(seed ^ 0x245),
                        Bits(seed ^ 0x791),
                    )
                    tape = []

                    def source(p=p, source_rng=source_rng, tape=tape):
                        bit = bernoulli(source_rng, p)
                        tape.append(str(bit))
                        return bit

                    record = dict(function=spec.name, method=factory.label, p=str(p), seed=seed)
                    try:
                        draw = factory.sample(source, aux_rng, level_rng=level_rng, max_coins=65536)
                    except ResourceFail as failure:
                        assert not tape
                        record.update(status="RESOURCE_FAIL", n=failure.n, level=failure.level)
                        counts["formula_resource_failures"] += 1
                    else:
                        assert draw.stats.source_calls == draw.n == len(tape)
                        assert draw.k == tape.count("1") and draw.bit in (0, 1)
                        record.update(
                            status="COMPLETE",
                            n=draw.n,
                            k=draw.k,
                            level=draw.level,
                            bit=draw.bit,
                            source_tape="".join(tape),
                            stats=asdict(draw.stats),
                        )
                        counts["formula_factory_complete"] += 1
                        counts["formula_actual_source_calls"] += draw.n
                    records.append(record)
    for spec in specs[:4]:
        fn = old[spec.name][0]
        tickets = 2 if spec.name == "constant" else 4
        for padded, short in ((False, False), (False, True), (True, False)):
            for p in (F(), F(1, 8), F(1, 3), F(1, 2), F(3, 4), F(7, 8), F(1)):
                probability, mean_calls = F(), F()
                for ticket in range(tickets):
                    planned, _, _ = direct_plan(spec.name, ticket, padded)
                    for parents in product((0, 1), repeat=planned):
                        observed = []
                        stream = iter(parents)

                        def source(observed=observed, stream=stream):
                            bit = next(stream)
                            observed.append(bit)
                            return bit

                        word = format(ticket, "01b" if tickets == 2 else "02b")
                        bit, used, declared = direct_sample(
                            spec.name, source, Prefix(word), padded=padded, short_circuit=short
                        )
                        weight = (
                            F(1, tickets) * p ** sum(parents) * (1 - p) ** (planned - sum(parents))
                        )
                        probability += weight * bit
                        mean_calls += weight * used
                        assert used == len(observed) and declared == planned
                        if not short:
                            assert used == planned
                        counts["direct_ticket_parent_cases"] += 1
                assert probability == fn(p)
                if padded:
                    assert (
                        mean_calls
                        == {
                            "constant": F(1),
                            "affine": F(1),
                            "quadratic": F(5, 4),
                            "cubic": F(3, 2),
                        }[spec.name]
                    )
                counts["direct_complete_laws"] += 1
    for action in (
        lambda: hg_interval(5, 6, 2, 0, 1, FormulaStats(), {}),
        lambda: hg_interval(5, 2, 6, 0, 1, FormulaStats(), {}),
        lambda: Piecewise("bad", (F(1, 2),), ((F(1),),), F(), F()),
        lambda: CompiledFactory(specs[-1]).vote(32, 0, Bits(0)),
        lambda: direct_sample("spline", lambda: 0, Bits(0)),
        lambda: direct_sample("cubic", lambda: 0, Bits(0), padded=True, short_circuit=True),
    ):
        try:
            action()
        except ValueError:
            counts["invalid_input_guards"] += 1
        else:
            raise AssertionError("Invalid control input accepted")
    sources = (
        "formula_control_v5.py",
        "audit_formula_v5.py",
        "formula-control-theory-v5.md",
        "runtime_v4.py",
        "audit_runtime_v4.py",
        "audit.py",
    )
    summary = dict(
        status="PASS",
        source_commit=subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
        counts=dict(counts),
        observed_formula_work=dict(observed_work),
        hashes={name: hashlib.sha256((HERE / name).read_bytes()).hexdigest() for name in sources},
        scope="Classical control correctness; no competitive timing or genealogy/NN run.",
        goal="OPEN",
    )
    target = Path(destination)
    target.mkdir(parents=True, exist_ok=False)
    (target / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    (target / "draws.jsonl").write_text("".join(json.dumps(row) + "\n" for row in records))
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main(sys.argv[1])
