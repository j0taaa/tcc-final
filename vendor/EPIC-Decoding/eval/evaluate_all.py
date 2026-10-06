#!/usr/bin/env python3

import os
import sys
import json
import importlib
import time
from pathlib import Path
from multiprocessing import get_context, TimeoutError
import argparse
from tqdm import tqdm
import warnings
warnings.filterwarnings("ignore", category=UserWarning)

DATASET_CHECKER_MAP = {
    "HumanEval/MRI/cpp/1": "dllm.cpp",
    "HumanEval/MRI/cpp/2": "dllm.cpp",
    "HumanEval/MRI/cpp/3": "dllm.cpp",
    "jsonschema": "dllm.jsonmode",
    "THUDM/humaneval-x/cpp": "dllm.cpp",
    "zai-org/humaneval-x/cpp": "dllm.cpp",
    "smiles": "dllm.smiles",
}


def to_output_filename(input_filename, autocomplete=False, output_dir=None):
    """
    Convert input filename to output filename.

    If output_dir is given, write compiled outputs there instead of next to input.
    """
    input_path = Path(input_filename)

    if input_path.suffix != ".jsonl":
        raise ValueError("Input filename must end with .jsonl")

    suffix = ".autocompleted.compiled.jsonl" if autocomplete else ".compiled.jsonl"
    output_name = input_path.name[: -len(".jsonl")] + suffix

    if output_dir is not None:
        out_dir = Path(output_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        return str(out_dir / output_name)

    return str(input_path.with_name(output_name))


def is_input_jsonl(path):
    path = str(path)
    name = Path(path).name

    if not path.endswith(".jsonl"):
        return False
    if ".compiled" in name:
        return False
    if ".autocompleted" in name:
        return False
    return Path(path).is_file()


def timeout_result(line, autocomplete=False):
    try:
        instance = json.loads(line.strip())
        instance_id = instance.get("instance_id", "")
    except Exception:
        instance_id = ""

    return json.dumps(
        {
            "instance_id": instance_id,
            "syntax_ok": False,
            "passed_tests": False,
            "timed_out": True,
            "skipped": "check_all timeout",
            "autocomplete": autocomplete,
        }
    )



def process_line(line, autocomplete=False, timeout=40):
    """
    Process a single line of input and evaluate it using the task-specific checker.

    Args:
        line:
        autocomplete: If true, checks the status of the autocomplete field.

    Returns:

    """
    instance = json.loads(line.strip())
    dataset = instance.get("dataset", None)
    task_name = DATASET_CHECKER_MAP.get(dataset, None)
    if not task_name:
        print("Error: Dataset not found in DATASET_CHECKER_MAP.", file=sys.stderr)
        print("Available datasets:", file=sys.stderr)
        for key in sorted(DATASET_CHECKER_MAP.keys()):
            print(f"  - {key}", file=sys.stderr)
        sys.exit(1)
    try:
        parent_path = str(Path(__file__).parent.parent)
        sys.path.append(parent_path)
        checker_module = importlib.import_module(f"eval.{task_name}.checker")
    except ImportError as e:
        print(
            f"Error: Task '{task_name}' not found or has no checker module: {e}",
            file=sys.stderr,
        )
        print("Available tasks:", file=sys.stderr)
        for path in sorted(Path(__file__).parent.iterdir()):
            if path.is_dir():
                for subpath in sorted(path.iterdir()):
                    if subpath.is_dir() and (subpath / "checker.py").exists():
                        print(f"  - {path.name}.{subpath.name}", file=sys.stderr)
        sys.exit(1)

    if autocomplete:
        if instance.get("autocompletion"):
            instance["code"] = instance.get("autocompletion_raw", "")
            instance["extracted"] = instance.get("autocompletion", "")
        else:
            return (
                '{"skipped": "No autocompletion available", "instance_id": "'
                + instance.get("instance_id", "")
                + '"}'
            )

    result = checker_module.check_instance(instance, timeout=timeout)
    
    time_taken = instance.get("time_taken", None)
    if time_taken is not None and autocomplete:
        time_taken = time_taken - instance.get("time_taken_autocompletion", 0)

    result.update(
        {
            "time_taken": time_taken,
            "timed_out": instance.get("timed_out", False),
            "resamples": instance.get("resamples", None),
            "generated_tokens": instance.get("generated_tokens", None),
        }
    )

    return json.dumps(result)



def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("input_files", nargs="+")
    parser.add_argument(
        "--mode",
        choices=["raw", "autocomplete", "both"],
        default="both",
        help="Which outputs to check.",
    )
    parser.add_argument(
        "--output-dir",
        default=None,
        help="Directory to write *.compiled.jsonl files. Default: next to input.",
    )
    parser.add_argument("--timeout", type=int, default=40)
    parser.add_argument(
        "--task-timeout",
        type=int,
        default=800,
        help=(
            "Wall-clock timeout for one multiprocessing task. "
            "If a task exceeds this, write timeout result, terminate the pool, "
            "and retry unfinished tasks in a fresh pool. "
            "0 disables this watchdog."
        ),
    )
    parser.add_argument(
        "--global-timeout",
        type=int,
        default=0,
        help=(
            "Global wall-clock timeout for the whole run. "
            "If exceeded, write timeout results for all remaining tasks and stop. "
            "0 disables global timeout."
        ),
    )
    parser.add_argument(
        "--processes",
        type=int,
        default=36,
    )
    parser.add_argument(
        "--maxtasksperchild",
        type=int,
        default=10,
        help="Restart worker after this many completed tasks. For C++, try 1 or 10.",
    )
    args = parser.parse_args()

    jsonl_files = [f for f in args.input_files if is_input_jsonl(f)]

    if not jsonl_files:
        print("No input .jsonl files found after filtering compiled outputs.", file=sys.stderr)
        return

    if args.mode == "raw":
        autocomplete_modes = [False]
    elif args.mode == "autocomplete":
        autocomplete_modes = [True]
    else:
        autocomplete_modes = [True, False]

    all_jobs = []
    for jsonl_file in jsonl_files:
        with open(jsonl_file) as f:
            for line in f:
                if not line.strip():
                    continue
                for autocomplete in autocomplete_modes:
                    all_jobs.append((jsonl_file, autocomplete, line))

    reset_files = set()
    bar = tqdm(total=len(all_jobs))
    ctx = get_context("spawn")
    run_start_time = time.time()

    def ensure_output_file(input_file, autocomplete):
        output_filename = to_output_filename(
            input_file,
            autocomplete=autocomplete,
            output_dir=args.output_dir,
        )
        if output_filename not in reset_files:
            open(output_filename, "w").close()
            reset_files.add(output_filename)
        return output_filename

    def write_output(input_file, autocomplete, output_line):
        output_filename = ensure_output_file(input_file, autocomplete)
        with open(output_filename, mode="a") as f:
            print(output_line, flush=True, file=f)

    def write_timeout(input_file, autocomplete, line, reason):
        output_line = timeout_result(line, autocomplete=autocomplete)
        write_output(input_file, autocomplete, output_line)
        print(f"{reason}: {line[:200]}", file=sys.stderr)

    pending_jobs = list(all_jobs)

    try:
        while pending_jobs:
            pool = ctx.Pool(
                processes=args.processes,
                maxtasksperchild=args.maxtasksperchild,
            )
            terminate_pool = False

            submitted = []
            now = time.time()
            for input_file, autocomplete, line in pending_jobs:
                submitted.append(
                    (
                        input_file,
                        autocomplete,
                        pool.apply_async(
                            process_line,
                            (
                                line,
                                autocomplete,
                                args.timeout,
                            ),
                        ),
                        line,
                        now,
                    )
                )

            pending_jobs = []

            try:
                while submitted:
                    time.sleep(0.1)
                    now = time.time()
                    next_submitted = []
                    task_timeout_seen = False

                    global_timeout_elapsed = (
                        args.global_timeout > 0
                        and now - run_start_time > args.global_timeout
                    )

                    if global_timeout_elapsed:
                        print(
                            f"Global timeout reached after {args.global_timeout}s. "
                            f"Writing timeout results for {len(submitted)} remaining tasks.",
                            file=sys.stderr,
                        )

                    for input_file, autocomplete, async_result, line, submitted_at in submitted:
                        task_timeout_elapsed = (
                            args.task_timeout > 0
                            and now - submitted_at > args.task_timeout
                        )

                        if (
                            not async_result.ready()
                            and not task_timeout_elapsed
                            and not global_timeout_elapsed
                        ):
                            next_submitted.append(
                                (input_file, autocomplete, async_result, line, submitted_at)
                            )
                            continue

                        if async_result.ready():
                            try:
                                output_line = async_result.get(timeout=0)
                                write_output(input_file, autocomplete, output_line)
                            except TimeoutError:
                                write_timeout(
                                    input_file,
                                    autocomplete,
                                    line,
                                    "Timed out while collecting ready result",
                                )
                            except Exception as e:
                                write_timeout(
                                    input_file,
                                    autocomplete,
                                    line,
                                    f"Checker failed with {repr(e)}",
                                )
                            bar.update(1)
                            continue

                        if global_timeout_elapsed:
                            write_timeout(
                                input_file,
                                autocomplete,
                                line,
                                "Global timeout while processing line",
                            )
                            bar.update(1)
                            continue

                        if task_timeout_elapsed:
                            write_timeout(
                                input_file,
                                autocomplete,
                                line,
                                f"Task timeout after {args.task_timeout}s",
                            )
                            bar.update(1)
                            task_timeout_seen = True
                            continue

                    if global_timeout_elapsed:
                        terminate_pool = True
                        submitted = []
                        pending_jobs = []
                        break

                    if task_timeout_seen:
                        terminate_pool = True
                        pending_jobs = [
                            (input_file, autocomplete, line)
                            for input_file, autocomplete, _async_result, line, _submitted_at
                            in next_submitted
                        ]
                        submitted = []
                        print(
                            f"Restarting pool; retrying {len(pending_jobs)} unfinished tasks.",
                            file=sys.stderr,
                        )
                        break

                    submitted = next_submitted

            finally:
                if terminate_pool:
                    pool.terminate()
                else:
                    pool.close()
                pool.join()

    except KeyboardInterrupt:
        print("Interrupted.", file=sys.stderr)
        raise

    finally:
        bar.close()



if __name__ == "__main__":
    main()
