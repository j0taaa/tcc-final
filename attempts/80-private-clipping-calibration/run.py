"""A80 V1: sequential, bounded offline experiment; no model or GPU.

The parent measures launch-to-first-validated-output using the machine's common
monotonic clock. Mandatory enumerable-law diagnostics precede that output and
are included in the gate. The exact control follows each configuration's
rotated five sampled controls. See implementation.md for pre-data corrections.

PRNG counts describe requested bits, not physical entropy or an executable DP
guarantee. Mathematical emission assumes ideal independent random bits.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib
import json
import math
import os
import platform
import resource
import subprocess
import sys
from fractions import Fraction as F
from pathlib import Path
from random import Random
from statistics import median
from time import perf_counter

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
PACKAGE = "attempts.80-private-clipping-calibration"
EXACT_CAP = 65_536
WORD_CAP = 200_000
WORKER_SECONDS = 120
CAMPAIGN_SECONDS = 900
ADDRESS_BYTES = 1 << 30
OUTPUT_WORDS = 16
REJECTION_CAP = 16


class WordBudgetRefusal(Exception):
    pass


def bounded_observations(observations, counter):
    iterator = iter(observations)
    while counter[0] < WORD_CAP:
        observation = next(iterator)
        counter[0] += 1
        yield observation
    raise WordBudgetRefusal("calibration word limit reached")


class CountingRandom(Random):
    def __init__(self, seed):
        super().__init__(seed)
        self.bits = self.calls = self.max_request_bits = self.float_calls = 0

    def getrandbits(self, k):
        self.bits += k
        self.calls += 1
        self.max_request_bits = max(self.max_request_bits, k)
        return super().getrandbits(k)

    def random(self):
        self.bits += 53
        self.float_calls += 1
        return super().random()

    def summary(self):
        return dict(
            requested_bits=self.bits,
            getrandbits_calls=self.calls,
            max_request_bits=self.max_request_bits,
            binary64_random_calls=self.float_calls,
        )


def modules():
    return (
        importlib.import_module(PACKAGE + ".cases"),
        importlib.import_module(PACKAGE + ".calibration"),
    )


def encoded(value):
    def convert(item):
        if isinstance(item, (F, Path)):
            return str(item)
        raise TypeError(type(item).__name__)

    return json.dumps(
        value,
        default=convert,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )


def write_event(value):
    print(encoded(value), flush=True)


def bernoulli(probability, rng):
    """Exact rational Bernoulli in the ideal-bit interpretation of randrange."""
    if not 0 <= probability <= 1:
        raise ValueError("probability outside [0,1]")
    if probability in (0, 1):
        return bool(probability)
    return rng.randrange(probability.denominator) < probability.numerator


def clipped(p, mu, a, R):
    return max(a * mu, min(p, R * a * mu))


def integer_width(*values):
    return max(
        (
            max(abs(x.numerator).bit_length(), x.denominator.bit_length())
            if isinstance(x, F)
            else abs(x).bit_length()
            for x in values
        ),
        default=0,
    )


def numeric_payload_bits(value):
    """Logical numerators AND denominators, counting repeated state entries."""
    if isinstance(value, F):
        return max(1, abs(value.numerator).bit_length()) + value.denominator.bit_length()
    if isinstance(value, int):
        return max(1, abs(value).bit_length())
    if isinstance(value, (tuple, list)):
        return sum(numeric_payload_bits(x) for x in value)
    raise TypeError(type(value).__name__)


def projection_work_bits_bound(p, mu, R):
    """Conservative Fraction arithmetic bound, not observed maximum (see notes)."""
    L = math.lcm(*(x.denominator for x in (*p, *mu)))
    return 8 * (L.bit_length() + integer_width(R.numerator) + integer_width(R.denominator) + 2)


def emit(prepared, a, R, rng):
    """Fresh reinforced-envelope proposals, then an independent mu fallback."""
    coefficient = 1 - 1 / R
    probability_private = coefficient / (coefficient + a)
    max_bits = 16 * (integer_width(a, R) + 1)
    for trial in range(1, REJECTION_CAP + 1):
        sampler = prepared.private if bernoulli(probability_private, rng) else prepared.reference
        word = sampler.draw(rng)
        p = prepared.private.probability(word)
        mu = prepared.reference.probability(word)
        envelope = coefficient * p + a * mu
        c = clipped(p, mu, a, R)
        if not 0 < c <= envelope:
            raise AssertionError("invalid reinforced rejection envelope")
        acceptance = c / envelope
        # Includes unreduced cross-products before Fraction normalization;
        # observed normalized operands alone would miss e.g. (1/2)*(1/3).
        max_bits = max(max_bits, 16 * (integer_width(a, R, p, mu) + 1))
        if bernoulli(acceptance, rng):
            return word, trial, False, max_bits
    return prepared.reference.draw(rng), REJECTION_CAP, True, max_bits


def payload_storage(value, seen=None):
    """Retained Python object storage, explicitly distinct from RSS."""
    seen = set() if seen is None else seen
    if id(value) in seen:
        return 0
    seen.add(id(value))
    result = sys.getsizeof(value)
    if isinstance(value, dict):
        result += sum(payload_storage(k, seen) + payload_storage(v, seen) for k, v in value.items())
    elif isinstance(value, (list, tuple)):
        result += sum(payload_storage(v, seen) for v in value)
    elif isinstance(value, F):
        result += payload_storage(value.numerator, seen) + payload_storage(value.denominator, seen)
    return result


def verify_projection(p, mu, a, R):
    """Independent mass witness; no reuse of the root solver's sweep state."""
    if len(p) != len(mu) or sum(p) != 1 or sum(mu) != 1 or any(x <= 0 for x in mu):
        raise AssertionError("enumerated input law is not normalized with positive reference")
    if not 1 / R <= a <= 1:
        raise AssertionError("root outside public interval")
    q = tuple(clipped(x, y, a, R) for x, y in zip(p, mu, strict=True))
    if sum(q) != 1:
        raise AssertionError("root does not normalize the clipped law")
    return q


def diagnostics(prepared, a, R, calibration, precheck, enumerated=None):
    if prepared.valid_count > EXACT_CAP:
        return dict(
            status="resource_refusal_enumeration",
            valid_count=prepared.valid_count,
            cap=EXACT_CAP,
            implication="inconclusive, not infeasible",
        )
    law = prepared.enumerate_law(EXACT_CAP) if enumerated is None else enumerated
    p, mu = tuple(row[1] for row in law), tuple(row[2] for row in law)
    root = calibration.exact_projection(p, mu, R)
    q_star = verify_projection(p, mu, root, R)
    if precheck:
        q, z = p, F(1)
    else:
        c = tuple(clipped(x, y, a, R) for x, y in zip(p, mu, strict=True))
        z = sum(c)
        q = tuple(x / z for x in c)
    ratios = tuple(x / y for x, y in zip(q, mu, strict=True))
    if sum(q) != 1 or min(ratios) <= 0 or max(ratios) > R * min(ratios):
        raise AssertionError("output normalized law is outside C_R")
    # This binary64 diagnostic is never called a certified log interval.
    excess = math.fsum(
        float(x)
        * (
            math.log(y.numerator)
            - math.log(y.denominator)
            - math.log(zq.numerator)
            + math.log(zq.denominator)
        )
        for x, y, zq in zip(p, q_star, q, strict=True)
        if x
    )
    L = math.lcm(*(x.denominator for x in (*p, *mu)))
    work_bound = max(
        projection_work_bits_bound(p, mu, R),
        16 * (L.bit_length() + integer_width(R, root, a if a is not None else 1) + 3),
    )
    return dict(
        status="exact_mass_witness_numeric_log_diagnostic",
        valid_count=len(law),
        a_star=root,
        Z=z,
        sum_output=sum(q),
        ratio_amplitude=max(ratios) / min(ratios),
        conditional_excess_kl_binary64=excess,
        rational_work_bits_bound=work_bound,
        work_bits_scope="conservative rational operations; binary64 log internals excluded",
        diagnostic_only=True,
        log_intervals_certified=False,
    )


def compact_certificate(certificate):
    serialized = encoded(certificate)
    if len(serialized) <= 16_384:
        return certificate
    return dict(
        omitted_large_certificate=True,
        serialized_characters=len(serialized),
        sha256=hashlib.sha256(serialized.encode()).hexdigest(),
        keys=sorted(certificate) if isinstance(certificate, dict) else None,
    )


def worker(args):
    resource.setrlimit(resource.RLIMIT_AS, (ADDRESS_BYTES, ADDRESS_BYTES))
    started = perf_counter()
    cases, calibration = modules()
    case = next(c for c in cases.cases() if (c.family, c.n) == (args.family, args.n))
    config = calibration.make_config(args.R)
    R = F(args.R)
    prefix = f"A80-v1|{args.family}|{args.n}|{args.R}|{args.seed}"
    source, auxiliary, emission = (
        CountingRandom(prefix + suffix) for suffix in ("|source", "|median", "|emit")
    )
    row = dict(family=args.family, n=args.n, R=args.R, seed=args.seed, method=args.method)
    prepared = cases.prepare(case)
    precheck_start = perf_counter()
    if prepared.min_ratio_product <= 0:
        raise AssertionError("positive official source has a nonpositive valid weight")
    precheck = prepared.max_ratio_product <= R * prepared.min_ratio_product
    # Max/min computation itself is charged by prepare(), not just this comparison.
    precheck_seconds = perf_counter() - precheck_start
    row.update(
        valid_count=prepared.valid_count,
        precheck_in_C_R=precheck,
        compile_seconds=prepared.compile_seconds,
        prepare_seconds=prepared.prepare_seconds,
        precheck_comparison_seconds=precheck_seconds,
    )
    enumerated = None
    calibration_start = perf_counter()
    if precheck:
        a, samples = None, 0
        row.update(
            status="ok_precheck_exact_P",
            collection_seconds=0.0,
            solve_seconds=0.0,
            calibration_state_numeric_bits=0,
            calibration_state_storage_bytes=0,
            calibration_max_work_bits=0,
            certificate=dict(exact_P_in_C_R=True),
        )
    elif args.method == "exact":
        if prepared.valid_count > EXACT_CAP:
            row.update(
                status="resource_refusal_enumeration",
                enumeration_cap=EXACT_CAP,
                implication="inconclusive, not infeasible",
            )
            return row
        collect_start = perf_counter()
        enumerated = prepared.enumerate_law(EXACT_CAP)
        p, mu = tuple(row[1] for row in enumerated), tuple(row[2] for row in enumerated)
        collect_seconds = perf_counter() - collect_start
        solve_start = perf_counter()
        a = calibration.exact_projection(p, mu, R)
        solve_seconds = perf_counter() - solve_start
        verify_projection(p, mu, a, R)
        samples = 0
        row.update(
            status="ok",
            collection_seconds=collect_seconds,
            solve_seconds=solve_seconds,
            calibration_state_numeric_bits=numeric_payload_bits((enumerated, p, mu)),
            calibration_state_storage_bytes=payload_storage((enumerated, p, mu)),
            calibration_max_work_bits=projection_work_bits_bound(p, mu, R),
            exact_state_scope=(
                "retained enumerated IDs/laws; freed sweep workspace excluded; RSS includes it"
            ),
            exact_work_bits_kind=(
                "conservative lcm bound, including Fraction cross-products; not observed"
            ),
            certificate=dict(exact_normalization=True, enumerated_words=len(enumerated)),
        )
    else:
        requested = config.M_median if args.method == "median" else config.M
        if requested > WORD_CAP:
            row.update(status="resource_refusal_word_budget", requested=requested, cap=WORD_CAP)
            return row
        consumed = [0]
        observations = bounded_observations(prepared.observations(source), consumed)
        result = calibration.calibrate(args.method, observations, config, auxiliary)
        a, samples = result.a, result.samples
        if samples != requested or consumed[0] != requested or not 1 / R <= a <= 1:
            raise AssertionError("calibrator violated its fixed budget or public interval")
        if not result.certificate.get("conditional_budget_certified"):
            raise AssertionError("calibrator did not certify the frozen conditional budget")
        row.update(
            status="ok",
            collection_seconds=result.collection_seconds,
            solve_seconds=result.solve_seconds,
            calibration_state_numeric_bits=result.state_numeric_bits,
            calibration_state_storage_bytes=result.state_storage_bytes,
            calibration_max_work_bits=result.max_work_bits,
            certificate=compact_certificate(result.certificate),
        )
    row.update(
        a=a,
        calibration_words=samples,
        calibration_full_seconds=perf_counter() - calibration_start,
        xi=config.xi,
        beta=config.beta,
        theoretical_scope="conditional_calibration_KL",
    )
    quality_start = perf_counter()
    row["quality"] = diagnostics(prepared, a, R, calibration, precheck, enumerated)
    row["quality_diagnostics_seconds"] = perf_counter() - quality_start
    emission_start = perf_counter()
    fallbacks = proposals = max_emission_bits = 0
    digest = hashlib.sha256()
    for index in range(OUTPUT_WORDS):
        if precheck:
            word, trials, fallback, bits = prepared.private.draw(emission), 0, False, 0
        else:
            word, trials, fallback, bits = emit(prepared, a, R, emission)
        prepared.validate(word)
        digest.update(encoded(word).encode("ascii"))
        digest.update(b"\n")
        fallbacks += int(fallback)
        proposals += trials
        max_emission_bits = max(max_emission_bits, bits)
        if index == 0:
            now = perf_counter()
            row.update(
                first_emission_validation_seconds=now - emission_start,
                worker_first_output_seconds=now - started,
                total_first_output_seconds=now - args.launch_start,
            )
            write_event(
                dict(
                    kind="first_output",
                    **{
                        k: row[k]
                        for k in (
                            "family",
                            "n",
                            "R",
                            "seed",
                            "method",
                            "total_first_output_seconds",
                        )
                    },
                )
            )
    row.update(
        emission_validation_16_seconds=perf_counter() - emission_start,
        validated_output_words=OUTPUT_WORDS,
        output_ids_digest=digest.hexdigest(),
        rejection_proposals=proposals,
        mu_fallbacks=fallbacks,
        emission_max_work_bits_bound=max_emission_bits,
        emission_work_bits_scope=(
            "conservative rational-arithmetic bound; source separate; not observed"
        ),
    )
    row.update(
        worker_total_seconds=perf_counter() - started,
        process_peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * 1024,
        source_rng=source.summary(),
        auxiliary_rng=auxiliary.summary(),
        emission_rng=emission.summary(),
        source_max_root_bits=integer_width(prepared.private.total, prepared.reference.total),
        source_max_work_bits=prepared.max_work_bits,
        source_ratio_operand_bits_bound=integer_width(prepared.max_ratio_product)
        + prepared.valid_count.bit_length(),
        marginal_final_KL_guarantee_claimed=False,
        executable_privacy_claimed=False,
    )
    return row


def producer_metadata():
    names = (
        "README.md",
        "theory.md",
        "implementation.md",
        "calibration.py",
        "cases.py",
        "run.py",
        "test_calibration.py",
        "test_cases.py",
        "test_run.py",
    )
    paths = [str((HERE / name).relative_to(ROOT)) for name in names]
    subprocess.run(
        ["git", "diff", "--exit-code", "HEAD", "--", *paths],
        cwd=ROOT,
        check=True,
        stdout=subprocess.DEVNULL,
    )
    subprocess.run(
        ["git", "diff", "--exit-code", "HEAD", "--", "src/mwpc_exact"],
        cwd=ROOT,
        check=True,
        stdout=subprocess.DEVNULL,
    )
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    for path in paths:
        subprocess.run(["git", "cat-file", "-e", commit + ":" + path], cwd=ROOT, check=True)
    return dict(
        producer_commit=commit,
        source_sha256={
            name: hashlib.sha256((HERE / name).read_bytes()).hexdigest() for name in names
        },
        python=sys.version,
        platform=platform.platform(),
        cpu_count=os.cpu_count(),
        protocol="A80-v1",
        process_address_limit=ADDRESS_BYTES,
        worker_wall_limit=WORKER_SECONDS,
        global_wall_limit=CAMPAIGN_SECONDS,
        exact_enumeration_cap=EXACT_CAP,
        calibration_word_cap=WORD_CAP,
        first_output_clock="parent launch monotonic through first independently validated word",
        diagnostics=(
            "mandatory enumeration precedes first output; paid in gate, process RSS and wall"
        ),
        exact_order="after rotated sampled methods",
        candidate="grid",
        privacy="ideal mathematical final-word channel only; PRNG/software not audited",
    )


def configuration_order(cases, calibration):
    for index, (family, n, R, seed) in enumerate(
        sorted(
            (c.family, c.n, R, seed) for c in cases.cases() for R in (2, 16) for seed in (11, 23)
        )
    ):
        rotation = index % len(calibration.METHODS)
        methods = calibration.METHODS[rotation:] + calibration.METHODS[:rotation] + ("exact",)
        for method in methods:
            yield dict(family=family, n=n, R=R, seed=seed, method=method)


def decision(rows):
    groups = {}
    for row in rows:
        key = tuple(row[k] for k in ("family", "n", "R", "seed"))
        groups.setdefault(key, {})[row["method"]] = row
    ratios, unresolved = {"dyck": [], "expr": []}, []
    details = []
    for key, group in sorted(groups.items()):

        def good(row):
            return row.get("status") in ("ok", "ok_precheck_exact_P")

        candidate = group.get("grid", {})
        controls = [r for method, r in group.items() if method != "grid" and good(r)]
        incomplete = [
            method
            for method, r in group.items()
            if not good(r)
            and not (method == "exact" and r.get("status") == "resource_refusal_enumeration")
        ]
        if not good(candidate) or not controls or incomplete or len(group) != 6:
            unresolved.append(
                dict(configuration=key, statuses={k: r.get("status") for k, r in group.items()})
            )
            continue
        best = min(controls, key=lambda r: r["total_first_output_seconds"])
        ratio = candidate["total_first_output_seconds"] / best["total_first_output_seconds"]
        ratios[key[0]].append(ratio)
        details.append(
            dict(
                configuration=key,
                best_control=best["method"],
                grid_to_best=ratio,
                precheck=candidate.get("precheck_in_C_R", False),
            )
        )
    medians = {key: median(value) if value else None for key, value in ratios.items()}
    complete = len(groups) == 24 and not unresolved and all(len(v) == 12 for v in ratios.values())
    gate = (
        (
            "pass_restricted_offline_gate"
            if all(v <= 0.8 for v in medians.values())
            else "fail_restricted_offline_gate"
        )
        if complete
        else "inconclusive_incomplete_comparisons"
    )
    return dict(
        gate=gate,
        family_median_grid_to_best=medians,
        compared_by_family={k: len(v) for k, v in ratios.items()},
        unresolved=unresolved,
        comparisons=details,
        general_dLLM_utility_established=False,
        worldwide_novelty_established=False,
        distinct_qualified_themes=0,
    )


def campaign(output):
    metadata = producer_metadata()
    cases, calibration = modules()
    output.mkdir(parents=True, exist_ok=False)
    (output / "metadata.json").write_text(encoded(metadata) + "\n")
    started, rows, interrupted = perf_counter(), [], False
    specifications = list(configuration_order(cases, calibration))
    with (output / "rows.jsonl").open("x") as stream:
        for spec in specifications:
            remaining = CAMPAIGN_SECONDS - (perf_counter() - started)
            row = dict(spec)
            if interrupted:
                row["status"] = "not_run_interrupted"
            elif remaining <= 0:
                row["status"] = "not_run_global_budget"
            else:
                launched = perf_counter()
                command = [
                    sys.executable,
                    "-m",
                    PACKAGE + ".run",
                    "--worker",
                    "--family",
                    spec["family"],
                    "--n",
                    str(spec["n"]),
                    "--R",
                    str(spec["R"]),
                    "--seed",
                    str(spec["seed"]),
                    "--method",
                    spec["method"],
                    "--launch-start",
                    repr(launched),
                ]
                try:
                    result = subprocess.run(
                        command,
                        cwd=ROOT,
                        text=True,
                        capture_output=True,
                        timeout=min(WORKER_SECONDS, remaining),
                        check=False,
                    )
                    events = [
                        json.loads(line) for line in result.stdout.splitlines() if line.strip()
                    ]
                    final = next((e for e in reversed(events) if e.get("kind") == "result"), None)
                    if final is None:
                        row.update(
                            status="worker_exit_without_result",
                            returncode=result.returncode,
                            stderr=result.stderr[-3000:],
                        )
                    else:
                        row.update(final)
                        row.pop("kind", None)
                        if result.returncode:
                            row.update(status="worker_nonzero_exit", returncode=result.returncode)
                except subprocess.TimeoutExpired as error:
                    row.update(
                        status="timeout_global_budget" if remaining < WORKER_SECONDS else "timeout",
                        stdout_checkpoint=(error.stdout or b"").decode(errors="replace")[-3000:]
                        if isinstance(error.stdout, bytes)
                        else (error.stdout or "")[-3000:],
                    )
                except KeyboardInterrupt:
                    row["status"], interrupted = "interrupted", True
                except (OSError, ValueError) as error:
                    row.update(
                        status="parent_worker_error",
                        exception=type(error).__name__,
                        message=str(error)[:3000],
                    )
                row["parent_process_wall_seconds"] = perf_counter() - launched
            rows.append(row)
            stream.write(encoded(row) + "\n")
            stream.flush()
            write_event({k: row[k] for k in ("family", "n", "R", "seed", "method", "status")})
    verdict = decision(rows)
    (output / "decision.json").write_text(encoded(verdict) + "\n")
    (output / "completion.json").write_text(
        encoded(
            dict(
                rows=len(rows),
                total_wall_seconds=perf_counter() - started,
                completed=not interrupted,
                interrupted=interrupted,
            )
        )
        + "\n"
    )
    write_event(verdict)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--worker", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--family", choices=("dyck", "expr"))
    parser.add_argument("--n", type=int)
    parser.add_argument("--R", type=int, choices=(2, 16))
    parser.add_argument("--seed", type=int)
    parser.add_argument(
        "--method", choices=("ratio_bisection", "indices", "grid", "gk", "median", "exact")
    )
    parser.add_argument("--launch-start", type=float)
    args = parser.parse_args()
    if args.worker:
        worker_started = perf_counter()
        try:
            row = worker(args)
        except MemoryError:
            row = dict(status="memory_refusal", virtual_address_limit=ADDRESS_BYTES)
        except Exception as error:
            name = type(error).__name__
            status = (
                "zero_mass"
                if "ZeroMass" in name
                else "resource_refusal"
                if "Limit" in name or "Refusal" in name
                else "unsupported"
                if isinstance(error, NotImplementedError)
                else "error"
            )
            row = dict(status=status, exception=name, message=str(error)[:3000])
        row.setdefault(
            "process_peak_rss_bytes", resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * 1024
        )
        row["worker_wall_seconds_including_error"] = perf_counter() - worker_started
        write_event(dict(kind="result", **row))
    elif args.output is None:
        parser.error("--output NEW_DIRECTORY is required")
    else:
        campaign(args.output)


if __name__ == "__main__":
    main()
