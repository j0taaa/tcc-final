"""Frozen full-factory development screen and paired analysis, no neural use."""

import hashlib
import json
import os
import platform
import resource
import signal
import subprocess
import sys
import time
from collections import Counter
from dataclasses import asdict
from pathlib import Path
from statistics import median

import gmpy2
from formula_control_v5 import CompiledFactory, direct_sample, original_specs
from retrospective_v6 import RetrospectiveFactory
from runtime_v4 import Bits, Factory, ResourceFail, bernoulli, mpq

HERE = Path(__file__).resolve().parent
PROTOCOL = json.loads((HERE / "cost-protocol-v7.json").read_text())


def timeout(_signal, _frame):
    raise TimeoutError("Worker wall resource limit")


def worker(case):
    spec = next(s for s in original_specs() if s.name == case["function"])
    p, method = mpq(case["p"]), case["method"]
    operation = PROTOCOL["operations"][case["operation"]]
    reuse = case["operation"] == "cached"
    direct = method.startswith("direct_")
    tape, outputs, details, stats = bytearray(), [], [], []
    status, error = "COMPLETE", None

    def construct():
        if direct:
            return None
        if method in ("formula", "derivative"):
            return CompiledFactory(spec, analytic=method == "derivative", reuse=reuse)
        cls = RetrospectiveFactory if method == "retrospective" else Factory
        return cls(spec.value, mpq(1, 4), spec.curvature, spec.h, reuse=reuse)

    def streams(seed):
        return (
            Bits(seed ^ PROTOCOL["source_seed_xor"]),
            Bits(seed ^ PROTOCOL["auxiliary_seed_xor"]),
            None if direct else Bits(seed ^ PROTOCOL["level_seed_xor"]),
        )

    resource.setrlimit(resource.RLIMIT_AS, (PROTOCOL["worker_address_space_bytes"],) * 2)
    signal.signal(signal.SIGALRM, timeout)
    signal.setitimer(signal.ITIMER_REAL, PROTOCOL["worker_wall_limit_seconds"])
    start_wall, start_cpu = time.perf_counter_ns(), time.process_time_ns()
    try:
        if reuse:
            factory = construct()
            source_rng, auxiliary_rng, level_rng = streams(operation["seed_start"])
        for i in range(operation["draws"]):
            if not reuse:
                factory = construct()
                source_rng, auxiliary_rng, level_rng = streams(operation["seed_start"] + i)
            before = len(tape)

            def source(source_rng=source_rng):
                bit = bernoulli(source_rng, p)
                tape.append(bit)
                return bit

            if direct:
                bit, used, planned = direct_sample(
                    spec.name,
                    source,
                    auxiliary_rng,
                    padded=method == "direct_padded",
                    short_circuit=method == "direct_short",
                )
                assert used == len(tape) - before and bit in (0, 1)
                details.append((used, planned))
            else:
                options = dict(level_rng=level_rng, max_coins=PROTOCOL["max_input_coins_per_draw"])
                if method in ("sparse", "dense"):
                    options["method"] = method
                draw = factory.sample(source, auxiliary_rng, **options)
                bit = draw.bit
                assert draw.n == len(tape) - before == draw.stats.source_calls
                assert draw.k == tape[before:].count(1) and bit in (0, 1)
                details.append((draw.n, draw.k, draw.level))
                stats.append(draw.stats)
            outputs.append(bit)
    except (ResourceFail, TimeoutError, MemoryError) as failure:
        status = type(failure).__name__
        error = str(failure)
    except Exception as failure:
        status, error = "ERROR", repr(failure)
    finally:
        elapsed_cpu = time.process_time_ns() - start_cpu
        elapsed_wall = time.perf_counter_ns() - start_wall
        signal.setitimer(signal.ITIMER_REAL, 0)
    counters = Counter()
    for stat in stats:
        for key, value in asdict(stat).items():
            if isinstance(value, int):
                counters[key] += value
    record = dict(
        case,
        status=status,
        error=error,
        api_wall_ns=elapsed_wall,
        api_cpu_ns=elapsed_cpu,
        peak_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        outputs=outputs,
        details=details,
        source_tape_hex=tape.hex(),
        source_tape_sha256=hashlib.sha256(tape).hexdigest(),
        source_calls=len(tape),
        counters=dict(counters),
    )
    print(json.dumps(record), flush=True)
    print(json.dumps(dict(worker_peak_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)))
    return int(status == "ERROR")


def analyze(rows):
    groups, results = {}, []
    for row in rows:
        key = row["function"], row["p"], row["operation"]
        groups.setdefault(key, {}).setdefault(row["method"], {})[row["repetition"]] = row
    tape_checks = 0
    for (name, p, operation), methods in groups.items():
        controls, comparisons = [m for m in methods if m != "sparse"], {}
        win = True
        for repetition in range(PROTOCOL["repetitions"]):
            core = [methods[m][repetition] for m in PROTOCOL["methods"][:5]]
            if all(r["status"] == "COMPLETE" for r in core):
                assert all(
                    (r["details"], r["source_tape_sha256"])
                    == (core[0]["details"], core[0]["source_tape_sha256"])
                    for r in core
                )
                tape_checks += len(core) - 1
        for control in controls:
            ratios = {"wall": [], "cpu": []}
            eligible = True
            for repetition in range(PROTOCOL["repetitions"]):
                left, right = methods["sparse"][repetition], methods[control][repetition]
                if left["status"] != "COMPLETE" or right["status"] != "COMPLETE":
                    eligible = False
                    continue
                for clock in ratios:
                    ratios[clock].append(left[f"api_{clock}_ns"] / right[f"api_{clock}_ns"])
            passed = eligible and all(
                len(values) == PROTOCOL["repetitions"] and median(values) <= 0.8 and max(values) < 1
                for values in ratios.values()
            )
            comparisons[control] = dict(
                eligible=eligible,
                strong_win=passed,
                median_ratios={c: median(v) if v else None for c, v in ratios.items()},
                paired_ratios=ratios,
            )
            win &= passed
        results.append(
            dict(function=name, p=p, operation=operation, strong_win=win, comparisons=comparisons)
        )
    wins = {
        o: sum(
            r["strong_win"]
            and r["function"] not in PROTOCOL["direct_eligible"]
            and r["operation"] == o
            for r in results
        )
        for o in PROTOCOL["operations"]
    }
    return dict(
        scope=PROTOCOL["scope"],
        rows=len(rows),
        expected_rows=PROTOCOL["rows"],
        statuses=dict(Counter(r["status"] for r in rows)),
        complete_outputs=sum(len(r.get("outputs", ())) for r in rows),
        actual_simulated_source_calls=sum(r.get("source_calls", 0) for r in rows),
        literal_core_pair_checks=tape_checks,
        nonpolynomial_strong_wins=wins,
        followup_gate="PASS_NECESSITY_ONLY" if max(wins.values()) >= 3 else "NEGATIVE",
        cases=results,
        goal="OPEN",
    )


def run(destination):
    destination = Path(destination)
    destination.mkdir(parents=True, exist_ok=False)
    (destination / "workers").mkdir()
    affinity = sorted(os.sched_getaffinity(0))
    os.sched_setaffinity(0, {affinity[0]})
    names = (
        "cost_v7.py",
        "cost-protocol-v7.json",
        "cost-contract-v7.md",
        "cost-runner-addendum-v7.md",
        "runtime_v4.py",
        "formula_control_v5.py",
        "retrospective_v6.py",
    )
    metadata = dict(
        source_commit=subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
        python=sys.version,
        gmpy2=gmpy2.version(),
        gmp=gmpy2.mp_version(),
        platform=platform.platform(),
        affinity=sorted(os.sched_getaffinity(0)),
        cpuinfo=Path("/proc/cpuinfo").read_text().split("\n\n")[0],
        hashes={n: hashlib.sha256((HERE / n).read_bytes()).hexdigest() for n in names},
        scope=PROTOCOL["scope"],
    )
    (destination / "metadata.json").write_text(json.dumps(metadata, indent=2) + "\n")
    rows = []
    ordinal = 0
    with (destination / "rows.jsonl").open("w") as file:
        for name in PROTOCOL["functions"]:
            for p in PROTOCOL["probabilities"]:
                methods = [
                    m
                    for m in PROTOCOL["methods"]
                    if not m.startswith("direct_") or name in PROTOCOL["direct_eligible"]
                ]
                for operation in PROTOCOL["operations"]:
                    for repetition in range(PROTOCOL["repetitions"]):
                        shift = (ordinal + repetition) % len(methods)
                        order = methods[shift:] + methods[:shift]
                        for method in order:
                            case = dict(
                                function=name,
                                p=p,
                                operation=operation,
                                repetition=repetition,
                                method=method,
                            )
                            index = len(rows)
                            before = resource.getrusage(resource.RUSAGE_CHILDREN)
                            started = time.perf_counter_ns()
                            try:
                                result = subprocess.run(
                                    [
                                        sys.executable,
                                        str(HERE / "cost_v7.py"),
                                        "--worker",
                                        json.dumps(case),
                                    ],
                                    capture_output=True,
                                    text=True,
                                    timeout=PROTOCOL["worker_wall_limit_seconds"] + 5,
                                )
                            except subprocess.TimeoutExpired as failure:
                                stdout = failure.stdout or b""
                                stderr = failure.stderr or b""
                                row = dict(case, status="SUPERVISOR_TIMEOUT", outputs=[])
                            else:
                                stdout, stderr = result.stdout, result.stderr
                                try:
                                    payload, peak = stdout.splitlines()
                                    row = json.loads(payload)
                                    row.update(json.loads(peak))
                                except ValueError:
                                    row = dict(case, status="WORKER_ERROR", outputs=[])
                                row["direct_exit_code"] = result.returncode
                            after = resource.getrusage(resource.RUSAGE_CHILDREN)
                            row["worker_wall_ns"] = time.perf_counter_ns() - started
                            row["worker_cpu_seconds"] = (
                                after.ru_utime + after.ru_stime - before.ru_utime - before.ru_stime
                            )
                            for label, data in (("stdout", stdout), ("stderr", stderr)):
                                (destination / "workers" / f"{index:04d}.{label}").write_bytes(
                                    data.encode() if isinstance(data, str) else data
                                )
                            rows.append(row)
                            file.write(json.dumps(row) + "\n")
                            file.flush()
                            if len(rows) % 60 == 0:
                                print(
                                    json.dumps(
                                        dict(completed=len(rows), expected=PROTOCOL["rows"])
                                    ),
                                    flush=True,
                                )
                    ordinal += 1
    assert len(rows) == PROTOCOL["rows"]
    summary = analyze(rows)
    (destination / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps({k: v for k, v in summary.items() if k != "cases"}), flush=True)


if __name__ == "__main__":
    if sys.argv[1] == "--worker":
        raise SystemExit(worker(json.loads(sys.argv[2])))
    run(sys.argv[1])
