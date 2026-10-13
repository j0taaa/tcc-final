"""Fresh isolated matched operations for all three immutable compact controls."""

import argparse
import json
import os
import resource
import signal
import subprocess
import sys
import traceback
from pathlib import Path

from mwpc_exact.cfg_posterior import CompilationLimit
from mwpc_exact.tokenizer_bytes import CompositionalByteLevelAdapter

from ..table import LexerTable
from .benchmark import ROOT, WORK, alarm, digest, elapsed, now, operation
from .block_stats import Partition
from .compact import load


def worker(args):
    resource.setrlimit(resource.RLIMIT_AS, (3 * 1024**3,) * 2)
    protocol = json.loads((WORK / "consumer-v2-protocol.json").read_text())
    start = now()
    table = LexerTable(
        CompositionalByteLevelAdapter.from_token_pieces(
            json.loads((args.input / "vocabulary.json").read_text())
        )
    )
    partition = Partition(tuple(table.class_of), len(table.classes), protocol["block_size"])
    modules, origin = load() if args.method != "handoff" else (None, None)
    startup = elapsed(start)
    signal.signal(signal.SIGALRM, alarm)
    begin = now()
    signal.setitimer(signal.ITIMER_REAL, protocol["resources"]["seconds"])
    try:
        try:
            row = operation(
                table,
                partition,
                args.input / (args.case + ".json"),
                args.method,
                "cursor" if args.method == "handoff" else "compact_full_sparse",
                "numpy",
                protocol["seed"] + args.repeat,
                protocol,
                compact_modules=modules,
            )
        finally:
            signal.setitimer(signal.ITIMER_REAL, 0)
    except (CompilationLimit, MemoryError, TimeoutError, RecursionError) as error:
        signal.setitimer(signal.ITIMER_REAL, 0)
        row = dict(
            status="resource_refusal",
            reason=type(error).__name__ + ": " + str(error),
            operation=elapsed(begin),
        )
    except Exception as error:
        signal.setitimer(signal.ITIMER_REAL, 0)
        row = dict(
            status="error",
            reason=str(error),
            traceback=traceback.format_exc(),
            operation=elapsed(begin),
        )
    row.update(
        case=args.case,
        method=args.method,
        repeat=args.repeat,
        startup=startup,
        frozen_compiler=origin,
        peak_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
    )
    row["session_cold_total"] = {
        u: row.get("paid_total", row["operation"])[u] + startup[u] for u in ("wall", "cpu")
    }
    print(json.dumps(row), flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--case")
    parser.add_argument("--method")
    parser.add_argument("--repeat", type=int, default=0)
    args = parser.parse_args()
    if args.method:
        worker(args)
        return
    subprocess.run(["git", "diff", "--quiet", "HEAD", "--"], cwd=ROOT, check=True)
    protocol_path = WORK / "consumer-v2-compact-protocol.json"
    protocol = json.loads(protocol_path.read_text())
    cases = sorted(p.stem for p in args.input.glob("*.json") if p.with_suffix(".npy").exists())
    if len(cases) != 15 or args.output is None:
        raise ValueError("ALL15 original states and fresh output required")
    args.output.mkdir(parents=True, exist_ok=False)
    metadata = dict(
        protocol=protocol,
        protocol_sha256=digest(protocol_path),
        base_protocol_sha256=digest(WORK / "consumer-v2-protocol.json"),
        producer_commit=subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
        sources={str(p.relative_to(ROOT)): digest(p) for p in Path(__file__).parent.glob("*.py")},
        cases=cases,
        new_neural_forwards=0,
    )
    (args.output / "metadata.json").write_text(json.dumps(metadata, indent=2) + "\n")
    count = 0
    with (args.output / "rows.jsonl").open("w") as log:
        for repeat in range(protocol["repetitions"]):
            for i, case in enumerate(cases):
                methods = protocol["methods"]
                offset = (repeat + i) % len(methods)
                for method in methods[offset:] + methods[:offset]:
                    command = [
                        sys.executable,
                        "-m",
                        "attempts.24-certified-depth-approximation.work.consumer_v2.compact_benchmark",
                        "--input",
                        str(args.input),
                        "--case",
                        case,
                        "--method",
                        method,
                        "--repeat",
                        str(repeat),
                    ]
                    try:
                        completed = subprocess.run(
                            command,
                            capture_output=True,
                            text=True,
                            cwd=ROOT,
                            env=dict(os.environ, OPENBLAS_NUM_THREADS="1", OMP_NUM_THREADS="1"),
                            timeout=150,
                            check=False,
                        )
                        if completed.returncode:
                            row = dict(
                                case=case,
                                method=method,
                                repeat=repeat,
                                status="worker_error",
                                exit_code=completed.returncode,
                                stderr=completed.stderr,
                            )
                        else:
                            row = json.loads(completed.stdout)
                    except subprocess.TimeoutExpired:
                        row = dict(
                            case=case,
                            method=method,
                            repeat=repeat,
                            status="supervisor_refusal",
                            reason="explicit150s supervisor; no latency/capacity credit",
                        )
                    log.write(json.dumps(row) + "\n")
                    log.flush()
                    count += 1
                    print(
                        json.dumps(
                            dict(
                                records=count,
                                case=case[:8],
                                method=method,
                                repeat=repeat,
                                status=row["status"],
                            )
                        ),
                        flush=True,
                    )
    print(json.dumps(dict(records=count, planned=180, complete_campaign=True)), flush=True)


if __name__ == "__main__":
    main()
