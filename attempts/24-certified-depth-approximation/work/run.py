"""Rotate all frozen development/independent methods under equal physical limits."""

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
        raise ValueError("freeze producer before competitive measurements")
    args.output.mkdir(parents=True, exist_ok=False)
    (args.output / "matrices").mkdir()
    protocol = json.loads((WORK / "protocol.json").read_text())
    capture = json.loads((args.capture / "metadata.json").read_text())
    frozen, control_commit, control_hash = materialize()
    (args.output / "metadata.json").write_text(
        json.dumps(
            dict(
                protocol=protocol,
                capture=capture,
                producer_commit=subprocess.check_output(
                    ["git", "rev-parse", "HEAD"], text=True
                ).strip(),
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
            ),
            indent=2,
        )
        + "\n"
    )
    cases = [f"{doc['key']}-{m}" for doc in capture["selected"] for m in protocol["mask_counts"]]
    repeats = protocol["independent_repetitions"] if args.independent else protocol["repetitions"]
    env = dict(os.environ, OPENBLAS_NUM_THREADS="1", OMP_NUM_THREADS="1")
    with (args.output / "rows.jsonl").open("w") as log:
        for repeat in range(repeats):
            for index, case in enumerate(cases):
                methods = protocol["methods"]
                offset = (index + repeat) % len(methods)
                for method in methods[offset:] + methods[:offset]:
                    native = method in protocol["frozen_exact_methods"] or method == "rejection"
                    module = (
                        "attempts.23-canonical-epsilon-posterior.work.measure"
                        if native
                        else "attempts.24-certified-depth-approximation.work.measure"
                    )
                    command = [
                        sys.executable,
                        "-m",
                        module,
                        "--capture",
                        str(args.capture.resolve()),
                        "--case",
                        case,
                        "--method",
                        method.removeprefix("exact_"),
                        "--repeat",
                        str(repeat),
                    ]
                    worker_env = dict(env)
                    if native:
                        command += ["--matrices", str((args.output / "matrices").resolve())]
                        worker_env["PYTHONPATH"] = str(frozen / "src") + os.pathsep + str(frozen)
                    start = perf_counter()
                    try:
                        process = subprocess.run(
                            command,
                            cwd=frozen if native else ROOT,
                            env=worker_env,
                            text=True,
                            capture_output=True,
                            timeout=protocol["hard_supervisor_seconds"],
                        )
                        if process.returncode:
                            row = dict(
                                case=case.rsplit("-", 1)[0],
                                mask_count=int(case.rsplit("-", 1)[1]),
                                method=method,
                                repeat=repeat,
                                status="worker_error",
                                returncode=process.returncode,
                                stderr=process.stderr[-6000:],
                            )
                        else:
                            row = json.loads(process.stdout.splitlines()[-1])
                            row["method"] = method
                            row["implementation_source_commit"] = (
                                control_commit if native else row["commit"]
                            )
                    except subprocess.TimeoutExpired:
                        row = dict(
                            case=case.rsplit("-", 1)[0],
                            mask_count=int(case.rsplit("-", 1)[1]),
                            method=method,
                            repeat=repeat,
                            status="resource_refusal",
                            error="hard supervisor deadline includes startup/cleanup",
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
                                total=row.get("prepared_total"),
                            )
                        ),
                        flush=True,
                    )


if __name__ == "__main__":
    main()
