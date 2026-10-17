"""Independent exact-bit/GMP oracle plus complete matched factory executions."""

import hashlib
import json
import subprocess
import sys
from collections import Counter
from dataclasses import asdict
from fractions import Fraction as F
from math import comb, isqrt
from pathlib import Path

import gmpy2
from audit import fixtures, independent_center
from runtime_v4 import (
    Bits,
    Factory,
    LazyUniform,
    Proposal,
    ResourceFail,
    Stats,
    bernoulli,
    binomial,
    geometric,
    randbelow,
    rational,
    weighted_elevation,
)
from sparse_v3 import Proposal as FractionProposal
from sparse_v3 import RejectionPlan

HERE = Path(__file__).resolve().parent


def fraction(value):
    return F(int(value.numerator), int(value.denominator))


class NeedMore(Exception):
    pass


class Prefix:
    def __init__(self, word):
        self.word, self.used = word, 0

    def getrandbits(self, count):
        if self.used + count > len(self.word):
            raise NeedMore
        block = self.word[self.used : self.used + count]
        self.used += count
        return int(block, 2) if count else 0


def main(destination):
    counts = Counter()
    for n in range(129):
        for k in range(n + 1):
            assert int(binomial(n, k)) == comb(n, k)
            counts["balanced_binomials"] += 1
    for n in (256, 1024, 4096):
        for k in (0, 1, n // 2, n - 1, n):
            assert int(binomial(n, k)) == comb(n, k)
            counts["larger_binomials"] += 1
    for m in (1, 2, 4, 16, 64):
        ks = range(4 * m + 1) if m < 64 else (0, 1, 64, 128, 192, 255, 256)
        for k in ks:
            values = [F((i - m // 2) ** 3, (7, 11, 13, 17, 19)[i % 5]) for i in range(m + 1)]
            lo, hi = max(0, k - 3 * m), min(m, k)
            direct = sum(
                (comb(m, i) * comb(3 * m, k - i) * values[i] for i in range(lo, hi + 1)), F()
            ) / comb(4 * m, k)
            balanced = weighted_elevation(
                m, k, lambda i, values=values: rational(values[i]), Stats()
            )
            assert fraction(balanced) == direct
            counts["variable_denominator_weighted_sums"] += 1
    for width in (4, 8, 12):
        for p in (F(), F(1), F(1, 2), F(1, 3), F(2, 3), F(1, 7), F(127, 128)):
            successes = unresolved = consumed = 0
            for ticket in range(2**width):
                rng = Prefix(format(ticket, f"0{width}b"))
                try:
                    successes += bernoulli(rng, p)
                except NeedMore:
                    unresolved += 1
                consumed += rng.used
                counts["exhaustive_bernoulli_prefixes"] += 1
            assert F(successes, 2**width) <= p <= F(successes + unresolved, 2**width)
            assert unresolved <= 1 and F(consumed, 2**width) <= 2
        for r in (F(1, 2), F(3, 4), F(31, 32)):
            outputs, unresolved = Counter(), 0
            for ticket in range(2**width):
                try:
                    outputs[geometric(Prefix(format(ticket, f"0{width}b")), r)] += 1
                except NeedMore:
                    unresolved += 1
                counts["exhaustive_geometric_prefixes"] += 1
            assert sum(outputs.values()) + unresolved == 2**width
            for j in range(6):
                assert (
                    F(outputs[j], 2**width)
                    <= (1 - r) * r**j
                    <= F(outputs[j] + unresolved, 2**width)
                )
                cumulative = sum(v for key, v in outputs.items() if key <= j)
                assert (
                    F(cumulative, 2**width)
                    <= 1 - r ** (j + 1)
                    <= F(cumulative + unresolved, 2**width)
                )
        for bound in (1, 2, 3, 7, 16, 17):
            outputs, unresolved = Counter(), 0
            for ticket in range(2**width):
                try:
                    outputs[randbelow(Prefix(format(ticket, f"0{width}b")), bound)] += 1
                except NeedMore:
                    unresolved += 1
                counts["exhaustive_integer_prefixes"] += 1
            assert sum(outputs.values()) + unresolved == 2**width
            for j in range(bound):
                assert (
                    F(outputs[j], 2**width) <= F(1, bound) <= F(outputs[j] + unresolved, 2**width)
                )
    for width in (4, 8):
        for ticket in range(2**width):
            uniform = LazyUniform(Prefix(format(ticket, f"0{width}b")))
            for p in (F(1, 2), F(1, 3), F(2, 3), F(1, 7)):
                try:
                    result = uniform.less(p)
                except NeedMore:
                    break
                if result:
                    assert F(ticket + 1, 2**width) <= p
                else:
                    assert F(ticket, 2**width) >= p
                counts["shared_uniform_comparisons"] += 1
    for m in (16, 64, 256):
        for k in range(4 * m + 1):
            native = Proposal(m, k, rational(1), Stats())
            old = FractionProposal(m, k, F(1))
            assert fraction(native.total) == old.total
            assert fraction(native.mass) == old.mass
            assert fraction(native.term_probability) == old.term_probability
            assert fraction(native.residual_probability) == old.residual_probability
            native.prepare()
            reference = RejectionPlan(old)
            mode, weight, left, right = native.plan
            assert (mode, left, right) == (reference.mode, reference.left, reference.right)
            assert fraction(weight) == reference.mode_weight
            for i in (old.left, mode, old.right):
                assert fraction(native.point_weight(i)) == old.point_weight(i)
                counts["gmp_proposal_point_weights"] += 1
            counts["gmp_proposals"] += 1
    conditional_components = Counter()
    for _name, fn, curvature, h in fixtures():
        if not h:
            continue

        def callback(x, fn=fn):
            return fn(fraction(x))

        factory = Factory(callback, F(1, 4), curvature, h)
        for m in (16, 64):
            row = [independent_center(fn, m, F(i, m)) for i in range(m + 1)]
            for k in range(4 * m + 1):
                lo, hi = max(0, k - 3 * m), min(m, k)
                elevated = sum(
                    (comb(m, i) * comb(3 * m, k - i) * row[i] for i in range(lo, hi + 1)), F()
                ) / comb(4 * m, k)
                target = F(1, 2) + (independent_center(fn, 4 * m, F(k, 4 * m)) - elevated) / (
                    7 * h / (4 * m * isqrt(m))
                )
                dense = factory.vote(4 * m, k, Bits(1024 * m + k), "dense")
                assert fraction(factory.scalars[4 * m, k]) == target
                sparse = factory.vote(4 * m, k, Bits(1024 * m + k), "sparse")
                assert sparse.stats.f_requests <= 6
                assert dense.bit in (0, 1) and sparse.bit in (0, 1)
                if sparse.stats.component in ("fair", "endpoint"):
                    assert sparse.stats.f_requests == 0
                if sparse.stats.component == "term":
                    assert sparse.stats.known_weights == 0
                conditional_components[sparse.stats.component] += 1
                counts["native_conditional_kernel_pairs"] += 1
    records, paired = [], []
    for name, fn, curvature, h in fixtures():

        def callback(x, fn=fn):
            return fn(fraction(x))

        for p in (F(1, 4), F(1, 2), F(3, 4)):
            for seed in range(32):
                pair = []
                for method in ("sparse", "dense"):
                    source_rng, aux_rng, level_rng = (
                        Bits(seed ^ 0x124),
                        Bits(seed ^ 0x245),
                        Bits(seed ^ 0x791),
                    )
                    source_tape = []

                    def coin(p=p, source_rng=source_rng, source_tape=source_tape):
                        bit = bernoulli(source_rng, p)
                        source_tape.append(str(bit))
                        return bit

                    factory = Factory(callback, F(1, 4), curvature, h)
                    record = dict(function=name, p=str(p), seed=seed, method=method)
                    try:
                        result = factory.sample(coin, aux_rng, method, level_rng, max_coins=65536)
                    except ResourceFail as failure:
                        assert not source_tape
                        record.update(status="RESOURCE_FAIL", n=failure.n, level=failure.level)
                        counts["whole_factory_resource_failures"] += 1
                    else:
                        assert result.bit in (0, 1)
                        assert result.n == result.stats.source_calls == len(source_tape)
                        assert result.k == source_tape.count("1")
                        assert result.n == factory.n0 * 4**result.level
                        if method == "sparse":
                            assert result.stats.f_requests <= 6
                        record.update(
                            status="COMPLETE",
                            bit=result.bit,
                            n=result.n,
                            k=result.k,
                            level=result.level,
                            stats=asdict(result.stats),
                            source_bits=source_rng.used,
                            source_tape="".join(source_tape),
                        )
                        counts["whole_factory_complete"] += 1
                        counts["actual_source_coin_calls"] += result.n
                    records.append(record)
                    pair.append(record)
                assert pair[0]["status"] == pair[1]["status"]
                for key in ("n", "level", "k", "source_tape"):
                    assert pair[0].get(key) == pair[1].get(key)
                paired.append(dict(function=name, p=str(p), seed=seed))
                counts["matched_whole_factory_pairs"] += 1
        for method in ("sparse", "dense"):
            cached = Factory(callback, F(1, 4), curvature, h, reuse=True)
            first = cached.vote(16, 7, Bits(1), method)
            second_rng = Bits(2)
            second = cached.vote(16, 7, second_rng, method)
            assert first.stats.f_requests == 3 and second.stats.f_requests == 0
            assert second.stats.scalar_cache_hits == 1 and second_rng.used > 0
            counts["base_cache_replays"] += 1
            if h:
                for seed in (1, 2, 3):
                    vote = cached.vote(64, 32, Bits(seed), method)
                    assert vote.bit in (0, 1)
                    if seed != 1 and method == "dense":
                        assert vote.stats.f_requests == 0 and vote.stats.scalar_cache_hits == 1
                    counts["higher_cache_replays"] += 1
    forced = Factory(lambda x: rational(F(1, 4)) + x**3 / 4, F(1, 4), F(3, 2), F(3, 2))

    def forbidden_source():
        raise AssertionError("Resource failure consumed an input coin")

    try:
        forced.sample(forbidden_source, Bits(1), level_rng=Prefix("0" * 17 + "001"), max_coins=64)
    except ResourceFail as failure:
        assert failure.n > 64 and failure.level == 5 and failure.level_bits == 20
        counts["explicit_resource_failure_before_source"] += 1
    else:
        raise AssertionError("Over-limit level not refused")
    for action in (
        lambda: rational(0.5),
        lambda: bernoulli(Bits(0), F(2)),
        lambda: geometric(Bits(0), F(1)),
        lambda: randbelow(Bits(0), 0),
        lambda: Factory(lambda x: x, F(), F(), F()),
        lambda: forced.vote(16.0, 0, Bits(1)),
        lambda: forced.vote(16, 17, Bits(1)),
        lambda: forced.sample(forbidden_source, Bits(1), method="bad"),
    ):
        try:
            action()
        except (TypeError, ValueError):
            counts["invalid_input_guards"] += 1
        else:
            raise AssertionError("Invalid exact-runtime input accepted")
    sources = (
        "runtime_v4.py",
        "audit_runtime_v4.py",
        "runtime-contract-v4.md",
        "requirements-v4.txt",
        "audit.py",
        "sparse_v3.py",
        "residual.py",
        "sparse-proposal-theory-v3.md",
    )
    summary = dict(
        status="PASS",
        source_commit=subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
        python=sys.version,
        gmpy2=gmpy2.version(),
        gmp=gmpy2.mp_version(),
        counts=dict(counts),
        conditional_components=dict(conditional_components),
        hashes={name: hashlib.sha256((HERE / name).read_bytes()).hexdigest() for name in sources},
        scope="Exact runtime preflight, no competitive timing or genealogy/NN run.",
        limits="Formula-aware/derivative/direct/cached controls and full-cost gate OPEN.",
    )
    target = Path(destination)
    target.mkdir(parents=True, exist_ok=False)
    (target / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    (target / "draws.jsonl").write_text("".join(json.dumps(row) + "\n" for row in records))
    (target / "paired.json").write_text(json.dumps(paired, indent=2) + "\n")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main(sys.argv[1])
