"""Rotate all preregistered operations in separate equal-budget worker processes."""

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path
from time import perf_counter

WORK = Path(__file__).resolve().parent
ROOT = WORK.parents[2]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--capture", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if subprocess.check_output(["git", "status", "--porcelain"], cwd=ROOT).strip():
        raise ValueError("freeze producer source before measurements")
    if args.output.exists():
        raise FileExistsError(args.output)
    args.output.mkdir(parents=True)
    (args.output / "matrices").mkdir()
    protocol = json.loads((WORK / "protocol.json").read_text())
    metadata = json.loads((args.capture / "metadata.json").read_text())
    (args.output / "metadata.json").write_text(
        json.dumps(
            dict(
                capture=metadata,
                protocol=protocol,
                producer_commit=subprocess.check_output(
                    ["git", "rev-parse", "HEAD"], text=True
                ).strip(),
                timing=(
                    "Each worker imports before service startup; "
                    "diagnostic hash/IO excluded equally"
                ),
            ),
            indent=2,
        )
        + "\n"
    )
    repetitions = (
        protocol["fresh_repetitions"] if metadata["phase"] == "fresh" else protocol["repetitions"]
    )
    cases = [
        f"{doc['key']}-{masks}" for doc in metadata["selected"] for masks in protocol["mask_counts"]
    ]
    env = dict(os.environ, OPENBLAS_NUM_THREADS="1", OMP_NUM_THREADS="1")
    with (args.output / "rows.jsonl").open("w") as log:
        for repeat in range(repetitions):
            for index, case in enumerate(cases):
                methods = protocol["methods"]
                offset = (index + repeat) % len(methods)
                for method in methods[offset:] + methods[:offset]:
                    begin = perf_counter()
                    result = subprocess.run(
                        [
                            sys.executable,
                            "-m",
                            "attempts.22-full-vocabulary-posterior.work.measure",
                            "--capture",
                            str(args.capture.resolve()),
                            "--case",
                            case,
                            "--method",
                            method,
                            "--repeat",
                            str(repeat),
                            "--matrices",
                            str((args.output / "matrices").resolve()),
                        ],
                        cwd=ROOT,
                        env=env,
                        text=True,
                        capture_output=True,
                        check=False,
                    )
                    if result.returncode:
                        row = dict(
                            case=case.rsplit("-", 1)[0],
                            mask_count=int(case.rsplit("-", 1)[1]),
                            method=method,
                            repeat=repeat,
                            status="worker_error",
                            returncode=result.returncode,
                            stderr=result.stderr,
                            elapsed=perf_counter() - begin,
                        )
                    else:
                        row = json.loads(result.stdout)
                    log.write(json.dumps(row) + "\n")
                    log.flush()
                    print(
                        json.dumps(
                            {
                                k: row[k]
                                for k in ("case", "mask_count", "method", "repeat", "status")
                            }
                        ),
                        flush=True,
                    )
                    if row["status"] == "worker_error":
                        # An implementation error must be investigated, never silently
                        # reinterpreted as a losing control or resource refusal.
                        raise RuntimeError(row["stderr"])


if __name__ == "__main__":
    main()
