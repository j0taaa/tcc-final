#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path

CONDITIONS = {
    "baseline": {
        "CONSTRAINED_DIFFUSION_FAST_ENFA": "0",
        "CONSTRAINED_DIFFUSION_CACHE_SCOPE": "off",
        "CONSTRAINED_DIFFUSION_INCREMENTAL_LEXING": "0",
        "CONSTRAINED_DIFFUSION_FRAGMENT_CACHE": "0",
        "CONSTRAINED_DIFFUSION_DFA_FREE_CHECKER": "0",
        "CONSTRAINED_DIFFUSION_REGULAR_COVER_BATCH": "0",
    },
    "epic": {
        "CONSTRAINED_DIFFUSION_FAST_ENFA": "1",
        "CONSTRAINED_DIFFUSION_CACHE_SCOPE": "instance",
        "CONSTRAINED_DIFFUSION_INCREMENTAL_LEXING": "0",
        "CONSTRAINED_DIFFUSION_FRAGMENT_CACHE": "0",
        "CONSTRAINED_DIFFUSION_DFA_FREE_CHECKER": "1",
        "CONSTRAINED_DIFFUSION_REGULAR_COVER_BATCH": "1",
        "CONSTRAINED_DIFFUSION_REGULAR_COVER_MIN_BATCH": "2",
        "CONSTRAINED_DIFFUSION_REGULAR_COVER_EXACT": "1",
    },
}

MODEL_ALIASES = {
    "Dream-org/Dream-v0-Instruct-7B": "Dream",
    "GSAI-ML/LLaDA-8B-Instruct": "LLaDA",
    "apple/DiffuCoder-7B-Instruct": "DiffuCoder",
    "Dream-org/Dream-Coder-v0-Instruct-7B": "DreamCoder",
}

def model_alias(model_name):
    if model_name is None:
        return "na"
    return MODEL_ALIASES.get(str(model_name), safe_name(model_name))

def load_profile(path: Path) -> dict:
    if not path.exists():
        return {}
    if path.suffix == ".jsonl":
        rows = [json.loads(x) for x in path.read_text().splitlines() if x.strip()]
        return rows[-1] if rows else {}
    return json.loads(path.read_text())


def flat_get(profile: dict, section: str, name: str, field: str = None, default=0):
    obj = profile.get(section, {}).get(name, default)
    if field is None:
        return obj
    if isinstance(obj, dict):
        return obj.get(field, default)
    return default


def summarize(condition: str, rc: int, wall_s: float, profile: dict) -> dict:
    gl_total = flat_get(profile, "timers", "generated_language.total", "total", 0.0)
    gl_calls = flat_get(profile, "timers", "generated_language.total", "count", 0)
    min_total = flat_get(profile, "timers", "generated_language.minimize", "total", 0.0)
    inter_total = flat_get(profile, "timers", "decode.intersection", "total", 0.0)
    lex_total = flat_get(profile, "timers", "lex.rust_lex_string", "total", 0.0)
    prefix_total = (
        flat_get(profile, "timers", "prefix_suffix.matching_dfa_build", "total", 0.0)
        + flat_get(profile, "timers", "prefix_suffix.intersection_example_word", "total", 0.0)
    )
    counts = profile.get("counts", {})
    return {
        "condition": condition,
        "returncode": rc,
        "wall_s": wall_s,
        "generated_language_s": gl_total,
        "generated_language_calls": gl_calls,
        "minimize_s": min_total,
        "intersection_s": inter_total,
        "lex_rust_s": lex_total,
        "prefix_suffix_s": prefix_total,
        "lex_cache_hit": counts.get("lex.cache.hit", 0),
        "lex_cache_miss": counts.get("lex.cache.miss", 0),
        "prefix_suffix_hit": counts.get("prefix_suffix.cache.hit", 0),
        "prefix_suffix_miss": counts.get("prefix_suffix.cache.miss", 0),
        "incremental_hit": counts.get("incremental_lex_constrain_words.hit", 0),
        "incremental_miss": counts.get("incremental_lex_constrain_words.miss", 0),
        "fragment_hit": counts.get("fragment_cache.hit", 0),
        "fragment_miss": counts.get("fragment_cache.miss", 0),
    }


def infer_arg_value(cmd, name, default=None):
    if name not in cmd:
        return default
    i = cmd.index(name)
    if i + 1 >= len(cmd):
        return default
    return cmd[i + 1]

def safe_name(x):
    if x is None:
        return "na"
    return str(x).replace("/", "_").replace(":", "_")

def set_or_append_arg(cmd, name, value):
    cmd = list(cmd)
    if name in cmd:
        i = cmd.index(name)
        if i + 1 < len(cmd):
            cmd[i + 1] = str(value)
        else:
            cmd.append(str(value))
    else:
        cmd += [name, str(value)]
    return cmd

def run_unconstrained_once(args, out_dir, base_cmd):
    base_cmd = list(base_cmd)

    model = model_alias(infer_arg_value(base_cmd, "--model_name", "na"))
    seed = safe_name(infer_arg_value(base_cmd, "--seed", "na"))
    steps = safe_name(infer_arg_value(base_cmd, "--steps", "na"))
    tag = f"{model}_unconstrained_seed{seed}_steps{steps}"

    profile_path = out_dir / f"{tag}.json"
    log_path = out_dir / f"{tag}.log"

    result_dir = Path(args.result)
    result_dir.mkdir(parents=True, exist_ok=True)
    results_path = result_dir / f"{tag}.jsonl"

    run_cmd = set_or_append_arg(base_cmd, "--constrained", "False")
    if "--output_file" not in run_cmd:
        run_cmd += ["--output_file", str(results_path)]

    env = os.environ.copy()
    env.update({
        "CONSTRAINED_DIFFUSION_FAST_ENFA": "0",
        "CONSTRAINED_DIFFUSION_CACHE_SCOPE": "off",
        "CONSTRAINED_DIFFUSION_INCREMENTAL_LEXING": "0",
        "CONSTRAINED_DIFFUSION_FRAGMENT_CACHE": "0",
        "CONSTRAINED_DIFFUSION_DFA_FREE_CHECKER": "0",
        "CONSTRAINED_DIFFUSION_REGULAR_COVER_BATCH": "0",
    })
    env["CONSTRAINED_DIFFUSION_PROFILE_ENFA"] = "1"
    env["CONSTRAINED_DIFFUSION_PROFILE_ENFA_OUTPUT"] = str(profile_path)
    env.setdefault("CONSTRAINED_DIFFUSION_PROFILE_ENFA_PRINT", "0")

    if getattr(args, "print_command", False):
        print("[profile]", tag, "cmd", " ".join(run_cmd))

    start = time.perf_counter()
    with open(log_path, "w", encoding="utf-8") as log:
        proc = subprocess.run(run_cmd, env=env, stdout=log, stderr=subprocess.STDOUT)
    elapsed = time.perf_counter() - start

    if not profile_path.exists():
        with open(profile_path, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "counts": {},
                    "timers": {},
                    "values": {},
                    "metadata": {
                        "condition": "unconstrained",
                        "elapsed_wall_s": elapsed,
                        "returncode": proc.returncode,
                        "results_file": str(results_path),
                        "log_file": str(log_path),
                    },
                },
                f,
                indent=2,
            )

    if proc.returncode != 0:
        raise RuntimeError(
            f"[profile] unconstrained run failed with return code {proc.returncode}; see {log_path}"
        )

    return {
        "condition": "unconstrained",
        "returncode": proc.returncode,
        "wall_s": elapsed,
        "profile_path": str(profile_path),
        "log_path": str(log_path),
        "results_path": str(results_path),
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", required=True, help="Output directory for profiles")
    parser.add_argument("--result", required=True, help="Output directory for results")
    parser.add_argument(
        "--conditions",
        default=",".join(CONDITIONS.keys()),
        help="Comma-separated subset of condition names",
    )
    parser.add_argument("--print-command", action="store_true")
    parser.add_argument("cmd", nargs=argparse.REMAINDER, help="Command after --")
    args = parser.parse_args(argv)

    cmd = args.cmd
    if cmd and cmd[0] == "--":
        cmd = cmd[1:]
    if not cmd:
        parser.error("provide the benchmark command after --")

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    selected = [x.strip() for x in args.conditions.split(",") if x.strip()]

    summaries = []
    unconstrained_info = run_unconstrained_once(args, out_dir, cmd)
    profile = load_profile(Path(unconstrained_info["profile_path"]))
    row = summarize("unconstrained", unconstrained_info["returncode"], unconstrained_info["wall_s"], profile)
    summaries.append(row)
    print(json.dumps(row, ensure_ascii=False))
    
    for condition in selected:
        if condition not in CONDITIONS:
            raise SystemExit(f"Unknown condition {condition!r}. Known: {', '.join(CONDITIONS)}")

        model = model_alias(infer_arg_value(cmd, "--model_name", "na"))
        seed = safe_name(infer_arg_value(cmd, "--seed", "na"))
        steps = safe_name(infer_arg_value(cmd, "--steps", "na"))
        tag = f"{model}_{condition}_seed{seed}_steps{steps}"

        profile_path = out_dir / f"{tag}.json"
        log_path = out_dir / f"{tag}.log"
        
        result_dir = Path(args.result)
        result_dir.mkdir(parents=True, exist_ok=True)
        results_path = result_dir / f"{tag}.jsonl"

        run_cmd = list(cmd)
        if "--output_file" not in run_cmd:
            run_cmd += ["--output_file", str(results_path)]
        
        env = os.environ.copy()
        env.update(CONDITIONS[condition])
        env["CONSTRAINED_DIFFUSION_PROFILE_ENFA"] = "1"
        env["CONSTRAINED_DIFFUSION_PROFILE_ENFA_OUTPUT"] = str(profile_path)
        env.setdefault("CONSTRAINED_DIFFUSION_PROFILE_ENFA_PRINT", "0")
        if args.print_command:
            print("[profile]", condition, "env", CONDITIONS[condition], "cmd", " ".join(run_cmd))
        t0 = time.perf_counter()
        with open(log_path, "w", encoding="utf-8") as log:
            proc = subprocess.run(run_cmd, env=env, stdout=log, stderr=subprocess.STDOUT)
        wall_s = time.perf_counter() - t0
        profile = load_profile(profile_path)
        row = summarize(condition, proc.returncode, wall_s, profile)
        summaries.append(row)
        print(json.dumps(row, ensure_ascii=False))
        if proc.returncode != 0:
            print(f"[profile] condition {condition} failed; see {log_path}", file=sys.stderr)
            # Continue so partial profiles are still useful.

    summary_path = out_dir / "summary.json"
    summary_path.write_text(json.dumps(summaries, indent=2, ensure_ascii=False), encoding="utf-8")
    # Small TSV for quick spreadsheet/paste.
    if summaries:
        keys = list(summaries[0].keys())
        lines = ["\t".join(keys)]
        for row in summaries:
            lines.append("\t".join(str(row.get(k, "")) for k in keys))
        (out_dir / "summary.tsv").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return 0 if all(r["returncode"] == 0 for r in summaries) else 1


if __name__ == "__main__":
    raise SystemExit(main())
