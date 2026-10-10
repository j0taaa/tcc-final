"""Serial rotated all-case comparison; immutable controls and explicit failures."""

import argparse
import json
import os
import platform
import subprocess
import sys
from pathlib import Path
from time import perf_counter

from .frozen_control import ROOT, materialize

WORK = Path(__file__).resolve().parent


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--capture", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--independent", action="store_true")
    args = parser.parse_args()
    if subprocess.check_output(["git", "status", "--porcelain"], cwd=ROOT).strip():
        raise ValueError("freeze source and protocol before competitive timings")
    args.output.mkdir(parents=True, exist_ok=False)
    protocol = json.loads((WORK / "protocol.json").read_text())
    capture = json.loads((args.capture / "metadata.json").read_text())
    frozen, control_commit, control_hash = materialize()
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
    (args.output / "metadata.json").write_text(
        json.dumps(
            dict(
                protocol=protocol,
                capture=capture,
                producer_commit=commit,
                control_source_commit=control_commit,
                control_source_zip_sha256=control_hash,
                stage="independent" if args.independent else "development",
                measurement_host=dict(
                    system=platform.system(),
                    release=platform.release(),
                    machine=platform.machine(),
                    python=platform.python_version(),
                    affinity=sorted(os.sched_getaffinity(0)),
                    threads=dict(OPENBLAS=1, OMP=1),
                ),
                excluded_io=(
                    "Captured input/model loading, kernel imports and integrity IO; "
                    "identical frozen probabilities. Decoder cold startup and common "
                    "forward separately measured."
                ),
            ),
            indent=2,
        )
        + "\n"
    )
    cases = [f"{doc['key']}-{m}" for doc in capture["selected"] for m in protocol["mask_counts"]]
    if len(cases) != (15 if args.independent else 18):
        raise ValueError("all predeclared cases must be present")
    repeats = protocol["independent_repetitions"] if args.independent else protocol["repetitions"]
    env = dict(os.environ, OPENBLAS_NUM_THREADS="1", OMP_NUM_THREADS="1")
    with (args.output / "rows.jsonl").open("w") as log:
        for repeat in range(repeats):
            for index, case in enumerate(cases):
                methods = protocol["methods"]
                offset = (index + repeat) % len(methods)
                for method in methods[offset:] + methods[:offset]:
                    worker_env = dict(env)
                    # Frozen core only for frozen controls; the same immutable
                    # source is audited and the wrapper requests no marginals.
                    if method in protocol["frozen_exact_methods"]:
                        worker_env["PYTHONPATH"] = str(frozen / "src") + os.pathsep + str(ROOT)
                    command = [
                        sys.executable,
                        "-m",
                        "attempts.25-exact-envelope-sampling.work.measure",
                        "--capture",
                        str(args.capture.resolve()),
                        "--case",
                        case,
                        "--method",
                        method,
                        "--repeat",
                        str(repeat),
                    ]
                    base = dict(
                        case=case.rsplit("-", 1)[0],
                        mask_count=int(case.rsplit("-", 1)[1]),
                        method=method,
                        repeat=repeat,
                    )
                    start = perf_counter()
                    try:
                        process = subprocess.run(
                            command,
                            cwd=ROOT,
                            env=worker_env,
                            text=True,
                            capture_output=True,
                            timeout=protocol["hard_supervisor_seconds"],
                        )
                        if process.returncode:
                            row = dict(
                                base,
                                status="worker_error",
                                first_status="worker_error",
                                returncode=process.returncode,
                                stderr=process.stderr[-6000:],
                            )
                        else:
                            row = json.loads(process.stdout.splitlines()[-1])
                            row["implementation_source_commit"] = (
                                control_commit
                                if method in protocol["frozen_exact_methods"]
                                else commit
                            )
                    except subprocess.TimeoutExpired:
                        row = dict(
                            base,
                            status="resource_refusal",
                            first_status="unobserved",
                            error="external supervisor; no first-operation capacity credit",
                        )
                    row["supervisor_wall"] = perf_counter() - start
                    log.write(json.dumps(row) + "\n")
                    log.flush()
                    print(
                        json.dumps(
                            dict(
                                case=case[:8],
                                masks=row["mask_count"],
                                method=method,
                                repeat=repeat,
                                status=row["status"],
                                first_status=row["first_status"],
                                first_total=row.get("first_total"),
                                batch_total=row.get("batch_total"),
                            )
                        ),
                        flush=True,
                    )


if __name__ == "__main__":
    main()
