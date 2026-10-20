"""Frozen A79 offline runner and classical controls; never runs a model.

Random implements a reproducible PRNG program. Exact-law claims assume IID bits.
Object-size observations are neither RSS nor peaks; no memory gate uses them.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib
import inspect
import json
import math
import signal
import subprocess
import sys
import unittest
from collections import Counter
from contextlib import contextmanager
from fractions import Fraction as F
from functools import lru_cache
from pathlib import Path
from random import Random
from statistics import median
from time import perf_counter, process_time

from mwpc_exact.cfg_posterior import compile_cfg_sampler
from mwpc_exact.reference.limits import CompilationLimit

PACKAGE = "attempts.79-stochastic-circuit-sampling"
cases = importlib.import_module(PACKAGE + ".cases")
circuit = importlib.import_module(PACKAGE + ".circuit")
numeric = circuit._numeric()
HERE = Path(__file__).resolve().parent
METHODS = ("exact_plan", "sr_singleton", "sr_shared", "nearest", "interval64")
CANDIDATE = "sr_shared"
EPSILON, BASE_SEED, BIT_CAP = F(1, 100), 2026102000, 1_000_000


class CountingRandom(Random):
    def __init__(self, seed):
        super().__init__(seed)
        self.bits = self.calls = 0

    def getrandbits(self, k):
        if self.bits + k > BIT_CAP:
            raise numeric.RNGRefusal("bit_limit", self.bits, BIT_CAP)
        self.bits += k
        self.calls += 1
        return super().getrandbits(k)


def reachable_order(plan):
    keep, todo = set(), [] if plan.root is None else [plan.root]
    while todo:
        node = todo.pop()
        if node not in keep:
            keep.add(node)
            todo.extend(c for t in plan.terms[node] for c in t.children)
    return tuple(i for i in plan.order if i in keep)


def static_budgets(plan, order):
    budgets = [0] * len(plan.terms)
    for i in order:
        terms = plan.terms[i]
        budgets[i] = max((term_budget(t, budgets) for t in terms), default=0) + max(
            0, len(terms) - 1
        )
    return tuple(budgets)


def term_budget(term, budgets):
    return (
        1
        if term.choice is not None
        else (sum(budgets[c] for c in term.children) + 1 if term.children else 0)
    )


def check_rows(plan, rows):
    if len(rows) != len(plan.state.support.rows):
        raise ValueError("row count changed")
    for row, ids, pin in zip(rows, plan.state.support.rows, plan.state.canvas, strict=True):
        invalid = any(
            not isinstance(x, F) or x < 0 or x.denominator & (x.denominator - 1) for x in row
        )
        if len(row) != len(ids) or invalid or sum(row) > 1:
            raise ValueError("aligned nonnegative dyadic rows are required")
        if pin is not None and (ids != (pin,) or row != (F(1),)):
            raise ValueError("pins must remain original-ID deltas")


def traceback(plan, choose):
    output, pending = [None] * len(plan.state.canvas), [plan.root]
    if plan.root is None:
        raise circuit.ZeroMass("no valid derivation on support")
    while pending:
        node = pending.pop()
        term = plan.terms[node][choose(node)]
        if term.choice is not None:
            pos, index = term.choice
            if output[pos] is not None:
                raise AssertionError("repeated physical position")
            output[pos] = plan.state.support.rows[pos][index]
        pending.extend(reversed(term.children))
    if any(t is None for t in output):
        raise AssertionError("missing original token position")
    return tuple(output)


class ExactPlan:
    """Integer inside only; alternative products are recomputed on traceback."""

    def __init__(self, plan, rows, order=None):
        check_rows(plan, rows)
        self.plan, self.rows = plan, rows
        self.scales = tuple(max((x.denominator for x in row), default=1) for row in rows)
        self.weights = tuple(
            tuple(x.numerator * (s // x.denominator) for x in row)
            for row, s in zip(rows, self.scales, strict=True)
        )
        values = [0] * len(plan.terms)
        for i in reachable_order(plan) if order is None else order:
            values[i] = sum(plan.term_mass(t, self.weights, values) for t in plan.terms[i])
        self.values, self.stats = tuple(values), {}
        if plan.root is None or not values[plan.root]:
            raise circuit.ZeroMass("zero valid probability on support")

    def masses(self, node):
        return tuple(
            self.plan.term_mass(t, self.weights, self.values) for t in self.plan.terms[node]
        )

    def sample(self, rng):
        def choose(node):
            if len(self.plan.terms[node]) == 1:
                return 0
            masses = self.masses(node)
            draw = rng.randrange(sum(masses))
            for i, mass in enumerate(masses):
                if draw < mass:
                    return i
                draw -= mass
            raise AssertionError("integer draw outside total")

        return traceback(self.plan, choose)


class NeedExact(Exception):
    pass


def down(x):
    return max(0.0, math.nextafter(x, -math.inf))


def up(x):
    return math.nextafter(x, math.inf)


def guarded(x):
    if not math.isfinite(x) or (0 < x < sys.float_info.min):
        raise NeedExact("binary64 overflow/subnormal")
    return x


@lru_cache(maxsize=4096)
def gamma(k):
    if k >= 2**52:
        raise NeedExact("static relative error budget too large")
    return up(float(F(k, 2**53 - k))) if k else 0.0


def enclosure(value, k):
    """Outward-safe bounds on the exact real value; normal positive operations."""
    if not value:
        return 0.0, 0.0
    g = gamma(k)
    return down(value / up(1 + g)), up(value / down(1 - g))


def cdf_bounds(bounds):
    """Boundary intervals from independent prefix/suffix mass enclosures."""
    prefixes, suffixes = [(0.0, 0.0)], [(0.0, 0.0)] * (len(bounds) + 1)
    for lo, hi in bounds:
        a, b = prefixes[-1]
        prefixes.append((down(a + lo), up(b + hi)))
    for i in reversed(range(len(bounds))):
        a, b = suffixes[i + 1]
        lo, hi = bounds[i]
        suffixes[i] = (down(a + lo), up(b + hi))
    result = [(0.0, 0.0)]
    for i in range(1, len(bounds)):
        lo, hi = prefixes[i]
        sl, sh = suffixes[i]
        lower = down(lo / up(lo + sh)) if lo else 0.0
        denominator = down(hi + sl)
        upper = min(1.0, up(hi / denominator)) if denominator else 1.0
        if not math.isfinite(lower) or not math.isfinite(upper):
            raise NeedExact("nonfinite CDF certificate")
        result.append((lower, upper))
    return [*result, (1.0, 1.0)]


class UniformPrefix:
    """A retained half-open dyadic interval for one independent uniform."""

    def __init__(self, rng):
        self.rng, self.value, self.bits = rng, 0, 0
        self.extend(32)

    def extend(self, k=1):
        self.value = (self.value << k) | self.rng.getrandbits(k)
        self.bits += k

    def certified(self, boundaries):
        scale = 1 << self.bits
        for i in range(len(boundaries) - 1):
            a, b = boundaries[i][1].as_integer_ratio()
            c, d = boundaries[i + 1][0].as_integer_ratio()
            if self.value * b >= a * scale and (self.value + 1) * d <= c * scale:
                return i
        return None

    def exact(self, masses):
        total = sum(masses)
        if not total:
            raise circuit.ZeroMass("zero conditional probability")
        while True:
            scale, cumulative = 1 << self.bits, 0
            for i, mass in enumerate(masses):
                previous, cumulative = cumulative, cumulative + mass
                if (
                    self.value * total >= previous * scale
                    and (self.value + 1) * total <= cumulative * scale
                ):
                    return i
            self.extend()


class Interval64:
    """Classical binary64/static certificate with lazy retained-prefix refinement."""

    def __init__(self, plan, rows, order=None, budgets=None):
        if (sys.float_info.radix, sys.float_info.mant_dig, sys.float_info.rounds) != (2, 53, 1):
            raise circuit.CircuitRefusal("interval64 requires binary64 round-to-nearest")
        check_rows(plan, rows)
        self.plan, self.rows = plan, rows
        self.order = reachable_order(plan) if order is None else order
        self.budgets = static_budgets(plan, self.order) if budgets is None else budgets
        self.exact = None
        self.weights, self.values = (), ()
        self.stats = dict(
            exact_preparations=0,
            conditional_refinements=0,
            certified_choices=0,
            max_conditional_terms=0,
            fallback_reasons=[],
        )
        try:
            self.weights = tuple(tuple(guarded(float(x)) for x in row) for row in rows)
            if any(
                x and not v
                for row, wr in zip(rows, self.weights, strict=True)
                for x, v in zip(row, wr, strict=True)
            ):
                raise NeedExact("positive input converted to zero")
            values = [0.0] * len(plan.terms)
            for i in self.order:
                total = 0.0
                for t in plan.terms[i]:
                    total = guarded(total + self.mass(t, values))
                values[i] = total
            self.values = tuple(values)
            if plan.root is None or not values[plan.root]:
                raise circuit.ZeroMass("zero valid probability on support")
            gamma(self.budgets[plan.root])
        except NeedExact as error:
            self.refine(str(error))

    def mass(self, term, values):
        if term.choice is not None:
            p, j = term.choice
            return self.weights[p][j]
        if not term.children:
            return 1.0
        a, b = (values[c] for c in term.children)
        result = guarded(a * b)
        if a and b and not result:
            raise NeedExact("positive product underflowed")
        return result

    def refine(self, reason):
        if self.exact is None:
            self.stats["fallback_reasons"].append(reason)
            self.stats["exact_preparations"] += 1
            self.exact = ExactPlan(self.plan, self.rows, self.order)

    def sample(self, rng):
        def choose(node):
            terms = self.plan.terms[node]
            if len(terms) == 1:
                return 0
            uniform = UniformPrefix(rng)
            self.stats["max_conditional_terms"] = max(
                self.stats["max_conditional_terms"], len(terms)
            )
            if self.exact is None:
                try:
                    bounds = [
                        enclosure(self.mass(t, self.values), term_budget(t, self.budgets))
                        for t in terms
                    ]
                    side = uniform.certified(cdf_bounds(bounds))
                    if side is not None:
                        self.stats["certified_choices"] += 1
                        return side
                    raise NeedExact("CDF certificate ambiguous at retained prefix")
                except NeedExact as error:
                    self.stats["conditional_refinements"] += 1
                    self.refine(str(error))
            return uniform.exact(self.exact.masses(node))

        return traceback(self.plan, choose)


def select(data, word):
    """Original-head confidence; threshold .95, else leftmost maximum free slot."""
    confidence = tuple(
        row[ids.index(t)]
        for row, ids, t in zip(data.probabilities, data.state.support.rows, word, strict=True)
    )
    free = [i for i, pin in enumerate(data.state.canvas) if pin is None]
    chosen = [i for i in free if confidence[i] >= F(19, 20)]
    if not chosen and free:
        chosen = [min(free, key=lambda i: (-confidence[i], i))]
    return confidence, tuple(i in chosen for i in range(len(word)))


@contextmanager
def deadline(seconds):
    if seconds <= 0:
        raise TimeoutError("A79 soft wall-clock budget already exhausted")

    def expired(*_):
        raise TimeoutError("A79 soft wall-clock budget exhausted; law unresolved")

    previous = signal.signal(signal.SIGALRM, expired)
    signal.setitimer(signal.ITIMER_REAL, seconds)
    try:
        yield
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, previous)


def status(error):
    if isinstance(error, KeyboardInterrupt):
        return "interrupted"
    if isinstance(error, CompilationLimit):
        return "compilation_resource_refusal_unresolved"
    if isinstance(error, TimeoutError):
        return "timeout_unresolved"
    if isinstance(error, MemoryError):
        return "memory_refusal_unresolved"
    return getattr(error, "status", "implementation_error")


def encoded(value):
    return json.dumps(
        value,
        sort_keys=True,
        default=lambda x: (
            str(x) if isinstance(x, F) else (_ for _ in ()).throw(TypeError(type(x).__name__))
        ),
    )


def digest(value):
    return hashlib.sha256(encoded(value).encode()).hexdigest()


def source_manifest():
    root = HERE.parents[1]
    files = [
        HERE / "README.md",
        HERE / "theory.md",
        *sorted(HERE.glob("*.py")),
        *sorted((root / "src/mwpc_exact").rglob("*.py")),
    ]
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip()
    hashes = {}
    for path in files:
        relative, raw = str(path.relative_to(root)), path.read_bytes()
        frozen = subprocess.run(["git", "show", f"HEAD:{relative}"], cwd=root, capture_output=True)
        if frozen.returncode or frozen.stdout != raw:
            raise RuntimeError(f"freeze sources in Git before measurement: {relative}")
        hashes[relative] = hashlib.sha256(raw).hexdigest()
    return dict(producer_commit=commit, sha256=hashes)


def observe(evaluation, data, plan, binary, rng):
    """After timing: disjoint reachable Python sizes, not total RSS or peaks."""
    seen, sizes = set(), {}
    objects = [("head", data), ("original_plan_graph", plan)]
    if binary is not None:
        objects.extend((("binary_gates_extra", binary.gates), ("groups_extra", binary.groups)))
    arithmetic = getattr(evaluation, "arithmetic", None)
    objects.extend(
        (
            ("messages", evaluation.values),
            (
                "arithmetic_state_extra",
                (arithmetic, arithmetic.rng.getstate()) if arithmetic is not None else None,
            ),
            ("method_state_extra", evaluation),
            ("reconstruction_rng", (rng, rng.getstate())),
        )
    )
    for name, obj in objects:
        sizes[name + "_bytes"] = circuit.deep_bytes(obj, seen)
    stats = dict(evaluation.stats)
    if isinstance(evaluation, ExactPlan):
        stats["message_payload_bits"] = sum(x.bit_length() for x in evaluation.values)
    if arithmetic is not None:
        width = max((abs(v.exponent).bit_length() + 1 for v in evaluation.values), default=1)
        stats.update(
            E=width,
            exponent_width_scope="observed realization, not a global bound",
            message_payload_bits=len(evaluation.values) * (arithmetic.p + width),
            arithmetic=dict(arithmetic.stats),
        )
    stats.update(
        reconstruction_bits=rng.bits,
        reconstruction_calls=rng.calls,
        object_memory=sizes,
        peak_transient_buffer_bytes=None,
        rss_bytes=None,
    )
    return stats


def query(method, plan, binary, data, order, budgets, precisions, seed, *, observe_memory=True):
    reconstruction_seed = f"A79:reconstruction:{seed}"
    rng, evaluation = CountingRandom(reconstruction_seed), None
    record = dict(
        method=method,
        seed=seed,
        arithmetic_seed=seed,
        reconstruction_seed=reconstruction_seed,
        domain_separated_prng_streams=True,
    )
    measurement_flag = "measure" in inspect.signature(circuit.Circuit.evaluate).parameters
    wall, cpu = perf_counter(), process_time()
    try:
        with deadline(10):
            if method == "exact_plan":
                evaluation = ExactPlan(plan, data.probabilities, order)
                word = evaluation.sample(rng)
            elif method == "interval64":
                evaluation = Interval64(plan, data.probabilities, order, budgets)
                word = evaluation.sample(rng)
            else:
                options = {"measure": False} if measurement_flag else {}
                evaluation = binary.evaluate(
                    data.probabilities,
                    method,
                    precisions["nearest" if method == "nearest" else "sr"],
                    seed,
                    **options,
                )
                word = binary.sample(evaluation, rng)
            confidence, commitments = select(data, word)
        record.update(status="completed", word=word, confidence=confidence, commitments=commitments)
    except (Exception, KeyboardInterrupt) as error:
        record.update(status=status(error), error=f"{type(error).__name__}: {error}")
    finally:
        record.update(wall_seconds=perf_counter() - wall, cpu_seconds=process_time() - cpu)
        record.update(reconstruction_bits=rng.bits, reconstruction_calls=rng.calls)
    if evaluation is not None:
        try:
            record["observations"] = (
                observe(
                    evaluation,
                    data,
                    plan,
                    binary if method not in ("exact_plan", "interval64") else None,
                    rng,
                )
                if observe_memory
                else evaluation.stats
            )
        except (Exception, KeyboardInterrupt) as error:
            record.update(status=status(error), observation_error=str(error))
    return record


def summarize(rows):
    """Frozen time gate; object-size diagnostics cannot pass the RSS gate."""
    queries = [row for row in rows if row["phase"] == "query"]
    expected = {
        (case.name, method, j) for case in cases.cases() for method in METHODS for j in range(16)
    }
    keys = [(row["case"], row["method"], row["query"]) for row in queries]
    complete = (
        len(keys) == len(expected)
        and set(keys) == expected
        and all(row["status"] == "completed" and row.get("validated") is True for row in queries)
    )
    per_case, by_family = {}, {}
    for case in cases.cases():
        groups = {
            method: [row for row in queries if row["case"] == case.name and row["method"] == method]
            for method in METHODS
        }
        if any(
            len(group) != 16
            or any(
                row["status"] != "completed" or row.get("validated") is not True for row in group
            )
            for group in groups.values()
        ):
            per_case[case.name] = dict(status="inconclusive_unresolved")
            continue
        times = {
            method: median(row["wall_seconds"] for row in group) for method, group in groups.items()
        }
        if any(t <= 0 for t in times.values()):
            per_case[case.name] = dict(status="inconclusive_nonpositive_clock")
            complete = False
            continue
        control = min((method for method in METHODS if method != CANDIDATE), key=times.get)
        ratio = times[CANDIDATE] / times[control]
        per_case[case.name] = dict(
            status="completed", medians_seconds=times, best_control=control, candidate_ratio=ratio
        )
        by_family.setdefault(case.family, []).append(ratio)
    family_ratios = {
        family: median(ratios) for family, ratios in by_family.items() if len(ratios) == 9
    }
    winners = [family for family, ratio in family_ratios.items() if ratio <= 0.8]
    positive = complete and len(winners) >= 2
    return dict(
        candidate=CANDIDATE,
        expected_queries=len(expected),
        observed_queries=len(queries),
        completed_and_validated=complete,
        statuses=dict(Counter(row["status"] for row in queries)),
        cases=per_case,
        family_median_ratios=family_ratios,
        time_gate_families=winners,
        time_gate_pass=positive,
        memory_gate="inconclusive_no_isolated_RSS",
        decision=(
            "eligible_for_further_investigation"
            if positive
            else "nonpositive_development"
            if complete
            else "inconclusive_unresolved"
        ),
        tcc_contribution_established=False,
        neural_or_gpu_speedup_established=False,
    )


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, help="new output directory; never overwritten")
    parser.add_argument("--check", action="store_true", help="correctness tests only; no timings")
    args = parser.parse_args(argv)
    if args.check:
        suite = unittest.defaultTestLoader.discover(str(HERE), pattern="test_*.py")
        return int(not unittest.TextTestRunner(verbosity=2).run(suite).wasSuccessful())
    if args.output is None:
        parser.error("--output is required unless --check is used")
    sources = source_manifest()
    args.output.mkdir(parents=True, exist_ok=False)
    metadata = dict(
        sources=sources,
        python=sys.version,
        protocol="A79-offline-V1",
        epsilon=EPSILON,
        methods=METHODS,
        cases=[c.name for c in cases.cases()],
        limits=dict(
            compile_seconds=30,
            query_seconds=10,
            gates=200000,
            alternatives=1000000,
            rng_bits_per_stream=BIT_CAP,
        ),
        rng_model="IID fair streams in theorem; domain-separated Random in program",
        numeric_policy="new evaluation per output; uniform profile repeats head",
        timing="inside+traceback+confidence/commitments; validation/inspection extra",
        circuit_instrumentation_timed="measure"
        not in inspect.signature(circuit.Circuit.evaluate).parameters,
        memory="Python object estimates; peak/RSS unknown; memory gate inconclusive",
        primary_candidate=CANDIDATE,
        decision="family median of all nine case ratios; 20% in two families",
        state="running",
    )
    with (args.output / "metadata.json").open("x") as stream:
        stream.write(encoded(metadata) + "\n")
    interrupted, crashed = False, False
    with (args.output / "rows.jsonl").open("x", buffering=1) as output:

        def write(row):
            output.write(encoded(row) + "\n")
            output.flush()

        try:
            for case in cases.cases():
                plan = binary = None
                order = budgets = ()
                precisions, failures = {}, {}
                preparation = dict(phase="preparation", case=case.name)
                started = perf_counter()
                try:
                    source, data = cases.head(case, 0)
                    preparation.update(
                        head_preparation_seconds=perf_counter() - started,
                        grammar_sha256=hashlib.sha256(repr(source).encode()).hexdigest(),
                    )
                    started = perf_counter()
                    with deadline(30):
                        plan = compile_cfg_sampler(
                            source,
                            data.state,
                            max_chart_cells=200000,
                            max_alternatives=1000000,
                            timeout_seconds=30,
                        )
                    preparation["compile_seconds"] = perf_counter() - started
                    started = perf_counter()
                    order = reachable_order(plan)
                    budgets = static_budgets(plan, order)
                    preparation["control_structure_seconds"] = perf_counter() - started
                    started = perf_counter()
                    with deadline(30 - preparation["compile_seconds"]):
                        binary = circuit.build(plan)
                    preparation.update(circuit_seconds=perf_counter() - started, graph=binary.stats)
                    started = perf_counter()
                    with deadline(30):
                        precisions = {
                            k: circuit.precision_for(binary.stats["K"], EPSILON, k)
                            for k in ("sr", "nearest", "moments", "moments_improved")
                        }
                    preparation.update(
                        precision_preparation_seconds=perf_counter() - started,
                        precisions=precisions,
                        status="completed",
                    )
                except (Exception, KeyboardInterrupt) as error:
                    failed = METHODS if plan is None else ("sr_singleton", "sr_shared", "nearest")
                    failures = {
                        m: dict(status=status(error), error=f"{type(error).__name__}: {error}")
                        for m in failed
                    }
                    preparation.update(status=status(error), error=str(error))
                    if isinstance(error, KeyboardInterrupt):
                        write(preparation)
                        raise
                write(preparation)
                for method in METHODS:
                    warm = failures.get(method) or query(
                        method,
                        plan,
                        binary,
                        data,
                        order,
                        budgets,
                        precisions,
                        BASE_SEED,
                        observe_memory=False,
                    )
                    write(
                        dict(
                            warm,
                            phase="initialization",
                            method=method,
                            timed_trial=False,
                            case=case.name,
                        )
                    )
                    if warm["status"] == "interrupted":
                        raise KeyboardInterrupt
                for j in range(16):
                    started = perf_counter()
                    source, data = cases.head(case, j)
                    head_seconds = perf_counter() - started
                    head_hash = digest(
                        (
                            data.probabilities,
                            data.state.support.rows,
                            data.state.canvas,
                            tuple(
                                x.hex() if x is not None else None
                                for x in data.state.tokenizer_adapter.emissions
                            ),
                        )
                    )
                    for offset in range(len(METHODS)):
                        method = METHODS[(j + offset) % len(METHODS)]
                        row = (
                            dict(failures[method])
                            if method in failures
                            else query(
                                method,
                                plan,
                                binary,
                                data,
                                order,
                                budgets,
                                precisions,
                                BASE_SEED + j,
                            )
                        )
                        row.update(
                            phase="query",
                            method=method,
                            case=case.name,
                            family=case.family,
                            length=case.length,
                            profile=case.profile,
                            query=j,
                            seed=BASE_SEED + j,
                            timed_trial=True,
                            head_seed=20261020 + j,
                            head_sha256=head_hash,
                            head_preparation_seconds=head_seconds,
                        )
                        if row["status"] == "completed":
                            try:
                                cases.validate(case, data, row["word"])
                                row["validated"] = True
                            except Exception as error:
                                row.update(
                                    status="correctness_failure", validated=False, error=str(error)
                                )
                        write(row)
                        if row["status"] == "interrupted":
                            raise KeyboardInterrupt
        except KeyboardInterrupt:
            interrupted = True
        except Exception as error:
            crashed = True
            write(
                dict(
                    phase="runner",
                    status="implementation_error",
                    error=f"{type(error).__name__}: {error}",
                )
            )
        finally:
            metadata["state"] = (
                "interrupted"
                if interrupted
                else ("implementation_error" if crashed else "finished")
            )
            with (args.output / "completion.json").open("x") as stream:
                stream.write(encoded(metadata) + "\n")
    rows = [json.loads(line) for line in (args.output / "rows.jsonl").read_text().splitlines()]
    with (args.output / "decision.json").open("x") as stream:
        stream.write(encoded(summarize(rows)) + "\n")
    return 130 if interrupted else int(crashed)


if __name__ == "__main__":
    raise SystemExit(main())
