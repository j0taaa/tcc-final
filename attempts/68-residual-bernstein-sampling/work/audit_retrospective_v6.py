"""Independent full-chain and exact-prefix audit; no competitive timing."""

import hashlib
import json
import subprocess
import sys
from collections import Counter
from dataclasses import asdict
from fractions import Fraction as F
from math import comb, isqrt
from pathlib import Path

from audit import fixtures, independent_center
from audit_runtime_v4 import NeedMore, Prefix, fraction
from retrospective_v6 import Bounds, LazyStats, RetrospectiveFactory
from runtime_v4 import Bits, ResourceFail, bernoulli, rational

HERE = Path(__file__).resolve().parent


def independent(fn, n, k, h):
    m, x = n // 4, F(k, n)
    row = [independent_center(fn, m, F(i, m)) for i in range(m + 1)]
    elevated = sum(
        (
            F(comb(m, i) * comb(3 * m, k - i), comb(n, k)) * row[i]
            for i in range(max(0, k - 3 * m), min(m, k) + 1)
        ),
        F(),
    )
    return F(1, 2) + (independent_center(fn, n, x) - elevated) / (7 * h / (4 * m * isqrt(m)))


def main(destination):
    counts, records = Counter(), []
    prefix_chains = []
    for name, fn, curvature, h in fixtures():
        if h:
            for n in (64, 256):
                m = n // 4
                for k in range(n + 1):
                    target = independent(fn, n, k, h)
                    stats = LazyStats()
                    state = Bounds(m, k, rational(h), stats)
                    prior = (F(), F(1))
                    weights = []
                    while True:
                        lo, hi = map(fraction, state.interval())
                        assert prior[0] <= lo <= target <= hi <= prior[1]
                        counts["nested_intervals"] += 1
                        prior = lo, hi
                        if lo == hi:
                            assert lo == target
                            break
                        outcome = state.refine(lambda x, fn=fn: rational(fn(fraction(x))), stats)
                        if outcome == "term":
                            continue
                        i = outcome
                        nu = F(comb(m, i) * comb(3 * m, k - i), comb(n, k))
                        t = F(4 * i - k, 4 * isqrt(m))
                        poly = F(9, 20) + F(21, 20) * t**2 + t**4 / 12
                        weights.append(nu * poly)
                        assert len(weights) == 1 or weights[-1] <= weights[-2]
                        visited = state.visited
                        mass = sum(
                            (
                                F(comb(m, j) * comb(3 * m, k - j), comb(n, k))
                                * (
                                    F(9, 20)
                                    + F(21, 20) * F(4 * j - k, 4 * isqrt(m)) ** 2
                                    + F(4 * j - k, 4 * isqrt(m)) ** 4 / 12
                                )
                                * h
                                / (m * isqrt(m))
                                for j in visited
                            ),
                            F(),
                        )
                        assert fraction(state.remaining) == fraction(state.proposal.mass) - mass
                        counts["independent_remaining_masses"] += 1
                    assert sorted(state.visited) == list(range(max(0, k - 3 * m), min(m, k) + 1))
                    counts["complete_chains"] += 1
                    if n == 64 and k in (1, n // 2, n - 1):
                        prefix_chains.append((fn, curvature, h, n, k, target))
        for reuse in (False, True):
            for p in (F(1, 4), F(1, 2), F(3, 4)):
                cached = RetrospectiveFactory(
                    lambda x, fn=fn: rational(fn(fraction(x))), F(1, 4), curvature, h, reuse=reuse
                )
                for seed in range(8):
                    factory = (
                        cached
                        if reuse
                        else RetrospectiveFactory(
                            lambda x, fn=fn: rational(fn(fraction(x))), F(1, 4), curvature, h
                        )
                    )
                    sr, ar, lr = Bits(seed ^ 0x124), Bits(seed ^ 0x245), Bits(seed ^ 0x791)
                    tape = []

                    def source(sr=sr, p=p, tape=tape):
                        bit = bernoulli(sr, p)
                        tape.append(str(bit))
                        return bit

                    record = dict(function=name, p=str(p), seed=seed, reuse=reuse)
                    try:
                        draw = factory.sample(source, ar, level_rng=lr, max_coins=65536)
                    except ResourceFail as failure:
                        assert not tape
                        record.update(status="RESOURCE_FAIL", n=failure.n, level=failure.level)
                    else:
                        assert draw.n == len(tape) == draw.stats.source_calls
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
                        counts["complete_factory_calls"] += 1
                        counts["source_calls"] += draw.n
                    records.append(record)
        if h:
            factory = RetrospectiveFactory(
                lambda x, fn=fn: rational(fn(fraction(x))), F(1, 4), curvature, h, reuse=True
            )
            prior = (F(), F(1))
            for seed in range(32):
                draw = factory.vote(256, 128, Bits(seed))
                lo, hi = map(fraction, factory.bounds[256, 128].interval())
                assert prior[0] <= lo <= hi <= prior[1] and draw.stats.auxiliary_bits > 0
                prior = lo, hi
                counts["persistent_fresh_uniform_calls"] += 1
    for fn, curvature, h, n, k, target in prefix_chains:
        for width in (4, 8):
            ones = unresolved = 0
            for word in range(2**width):
                factory = RetrospectiveFactory(
                    lambda x, fn=fn: rational(fn(fraction(x))), F(1, 4), curvature, h
                )
                try:
                    answer = factory.vote(n, k, Prefix(format(word, f"0{width}b"))).bit
                except NeedMore:
                    unresolved += 1
                else:
                    ones += answer
                    lo, hi = F(word, 2**width), F(word + 1, 2**width)
                    assert (hi <= target) if answer else (lo >= target)
                counts["dyadic_prefixes"] += 1
            assert F(ones, 2**width) <= target <= F(ones + unresolved, 2**width)
    reference = {
        (x["function"], x["p"], x["seed"]): x
        for x in map(
            json.loads,
            (HERE.parents[2] / "docs/artifacts/raw/a68_formula_controls_v5_initial/draws.jsonl")
            .read_text()
            .splitlines(),
        )
        if x["method"] == "formula"
    }
    for record in records:
        old = reference[record["function"], record["p"], record["seed"]]
        assert all(record[key] == old[key] for key in ("status", "n", "k", "level", "source_tape"))
        counts["literal_source_matches"] += 1
    factory = RetrospectiveFactory(lambda x: mpq_dummy(x), F(1, 4), F(3, 4), F(3, 2))
    for n, k, method in ((17, 1, "dense"), (64, -1, "dense"), (64, 65, "dense"), (64, 2, "bad")):
        try:
            factory.vote(n, k, Bits(0), method)
        except ValueError:
            counts["guards"] += 1
        else:
            raise AssertionError("Invalid input accepted")
    try:
        factory.sample(
            lambda: (_ for _ in ()).throw(AssertionError("Source used")),
            Bits(0),
            level_rng=Prefix("1"),
            max_coins=15,
        )
    except ResourceFail:
        counts["resource_fail_before_source"] += 1
    else:
        raise AssertionError("Resource cap ignored")
    sources = (
        "retrospective_v6.py",
        "audit_retrospective_v6.py",
        "retrospective-control-theory-v6.md",
        "runtime_v4.py",
        "audit.py",
        "audit_runtime_v4.py",
    )
    summary = dict(
        status="PASS",
        source_commit=subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
        counts=dict(counts),
        hashes={s: hashlib.sha256((HERE / s).read_bytes()).hexdigest() for s in sources},
        scope="Classical lazy-control correctness; simulated inputs, no timing/genealogy/NN",
        goal="OPEN",
    )
    destination = Path(destination)
    destination.mkdir(parents=True, exist_ok=False)
    (destination / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    (destination / "draws.jsonl").write_text("".join(json.dumps(r) + "\n" for r in records))
    print(json.dumps(summary, indent=2))


def mpq_dummy(x):
    raise AssertionError("Guard unexpectedly called the function")


if __name__ == "__main__":
    main(sys.argv[1])
