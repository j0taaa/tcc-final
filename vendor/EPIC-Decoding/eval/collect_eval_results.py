#!/usr/bin/env python3
import argparse
import csv
import json
import math
import re
from collections import defaultdict
from pathlib import Path
from statistics import mean, stdev


CONDITION_KEYS = [
    "unconstrained",
    "baseline",
    "cache",
    "earley",
    "cache_earley",
    "regular",
    "cache_regular",
    "earley_regular",
    "epic",
]


def read_records(path: Path):
    """
    Supports:
      - .jsonl: one JSON object per line
      - .json: list[object]
      - .json: {"results": [...]}, {"data": [...]}, etc.
      - .json: single object
    """
    if path.suffix == ".jsonl":
        rows = []
        with path.open() as f:
            for line in f:
                line = line.strip()
                if line:
                    rows.append(json.loads(line))
        return rows

    with path.open() as f:
        obj = json.load(f)

    if isinstance(obj, list):
        return obj

    if isinstance(obj, dict):
        for key in ["results", "data", "instances", "rows", "logs"]:
            if key in obj and isinstance(obj[key], list):
                return obj[key]
        return [obj]

    raise ValueError(f"Unsupported JSON structure in {path}")


def read_jsonl(path: Path):
    return read_records(path)


def strip_suffixes(name: str):
    for suffix in [
        ".autocompleted.compiled.jsonl",
        ".compiled.jsonl",
        ".jsonl",
    ]:
        if name.endswith(suffix):
            return name[: -len(suffix)]
    return name


def is_autocompleted_file(path: Path):
    return path.name.endswith(".autocompleted.compiled.jsonl")


def auto_file_for_raw(raw_path: Path):
    return raw_path.with_name(
        raw_path.name.replace(".compiled.jsonl", ".autocompleted.compiled.jsonl")
    )


def raw_file_for_auto(auto_path: Path):
    return auto_path.with_name(
        auto_path.name.replace(".autocompleted.compiled.jsonl", ".compiled.jsonl")
    )


def parse_seed_step(path: Path):
    name = path.name

    seed_patterns = [
        r"(?:^|[_\-.])s=(\d+)(?:[_\-.]|$)",
        r"(?:^|[_\-.])seed=(\d+)(?:[_\-.]|$)",
        r"(?:^|[_\-.])seed(\d+)(?:[_\-.]|$)",
    ]

    step_patterns = [
        r"(?:^|[_\-.])sz=(\d+)(?:[_\-.]|$)",
        r"(?:^|[_\-.])steps=(\d+)(?:[_\-.]|$)",
        r"(?:^|[_\-.])step=(\d+)(?:[_\-.]|$)",
        r"(?:^|[_\-.])steps(\d+)(?:[_\-.]|$)",
        r"(?:^|[_\-.])step(\d+)(?:[_\-.]|$)",
    ]

    seed = None
    step = None

    for pat in seed_patterns:
        m = re.search(pat, name)
        if m:
            seed = int(m.group(1))
            break

    for pat in step_patterns:
        m = re.search(pat, name)
        if m:
            step = int(m.group(1))
            break

    return seed, step


def parse_condition_key(path: Path):
    stem = strip_suffixes(path.name)
    for key in sorted(CONDITION_KEYS, key=len, reverse=True):
        if re.search(rf"(?:^|_){re.escape(key)}(?:_|$)", stem):
            return key
    return None


def parse_condition_label(path: Path):
    key = parse_condition_key(path)
    if key is None:
        return None

    if is_autocompleted_file(path):
        return key
    return f"{key}-"


def parse_model(path: Path, dataset: str):
    name = strip_suffixes(path.name)

    for key in sorted(CONDITION_KEYS, key=len, reverse=True):
        name = re.sub(rf"(?:^|_){re.escape(key)}(?:_|$)", "_", name)

    name = re.split(r"[_\-.]s=\d+", name)[0]
    name = re.split(r"[_\-.]seed=\d+", name)[0]
    name = re.split(r"[_\-.]seed\d+", name)[0]

    prefixes = [
        dataset,
        "cpp",
        "json",
        "smiles",
        "jsonschema",
        "THUDM_humaneval-x_cpp",
        "zai-org_humaneval-x_cpp",
        "humaneval-x_cpp",
    ]

    for p in prefixes:
        if name.startswith(p + "_"):
            name = name[len(p) + 1 :]

    name = re.sub(r"_+", "_", name).strip("_")
    return name or "unknown_model"


def raw_log_file_for_compiled(compiled_path: Path, log_root: Path, dataset: str):
    raw_name = compiled_path.name
    raw_name = raw_name.replace(".autocompleted.compiled.jsonl", ".json")
    raw_name = raw_name.replace(".compiled.jsonl", ".json")
    return log_root / dataset / raw_name


def safe_float(x):
    if x is None:
        return None
    try:
        x = float(x)
    except Exception:
        return None
    if not math.isfinite(x):
        return None
    return x


def get_row_time(row, autocomplete=False):
    t = safe_float(row.get("metadata").get("elapsed_wall_s"))
    if t is None:
        return None

    if autocomplete:
        auto_t = safe_float(row.get("time_taken_autocompletion"))
        if auto_t is not None:
            t -= auto_t

    return t


def summarize_time_from_log(log_path: Path, autocomplete=False):
    if not log_path.exists():
        return {
            "n_time_instances": 0,
            "decoding_time": float("nan"),
        }

    rows = read_jsonl(log_path)
    times = [get_row_time(r, autocomplete=autocomplete) for r in rows]
    times = [t for t in times if t is not None]

    return {
        "n_time_instances": len(times),
        "decoding_time": mean(times) if times else float("nan"),
    }


def summarize_compiled_rows(rows):
    if not rows:
        return {
            "n_instances": 0,
            "syntax_acc": float("nan"),
            "functional_acc": float("nan"),
        }

    n = len(rows)
    return {
        "n_instances": n,
        "syntax_acc": 100.0 * sum(bool(r.get("syntax_ok", False)) for r in rows) / n,
        "functional_acc": 100.0 * sum(bool(r.get("passed_tests", False)) for r in rows) / n,
    }


def summarize_autocompleted_accuracy(auto_path: Path):
    raw_path = raw_file_for_auto(auto_path)

    if not raw_path.exists():
        return summarize_compiled_rows(read_jsonl(auto_path))

    raw_rows = read_jsonl(raw_path)
    auto_rows = read_jsonl(auto_path)

    auto_by_id = {}
    for row in auto_rows:
        iid = row.get("instance_id")
        if iid is not None:
            auto_by_id[iid] = row

    merged = []
    for raw in raw_rows:
        iid = raw.get("instance_id")
        auto = auto_by_id.get(iid)
        if auto is not None and "skipped" not in auto:
            merged.append(auto)
        else:
            merged.append(raw)

    return summarize_compiled_rows(merged)


def collect_per_seed(eval_root: Path, log_root: Path, seeds, steps):
    per_seed = []
    skipped = defaultdict(int)

    for dataset in ["cpp", "json", "smiles"]:
        eval_dir = eval_root / dataset
        if not eval_dir.exists():
            continue

        for compiled_path in sorted(eval_dir.rglob("*.compiled.jsonl")):
            seed, step = parse_seed_step(compiled_path)
            if seed is None:
                skipped["missing_seed"] += 1
                continue
            if step is None:
                skipped["missing_step"] += 1
                continue
            if seed not in seeds:
                skipped["seed_filter"] += 1
                continue
            if step not in steps:
                skipped["step_filter"] += 1
                continue

            condition_key = parse_condition_key(compiled_path)
            if condition_key is None:
                skipped["missing_condition_key"] += 1
                continue

            condition = parse_condition_label(compiled_path)
            model = parse_model(compiled_path, dataset)

            log_path = raw_log_file_for_compiled(compiled_path, log_root, dataset)
            autocomplete = is_autocompleted_file(compiled_path)

            if autocomplete:
                acc_summary = summarize_autocompleted_accuracy(compiled_path)
            else:
                acc_summary = summarize_compiled_rows(read_jsonl(compiled_path))

            time_summary = summarize_time_from_log(log_path, autocomplete=autocomplete)

            per_seed.append(
                {
                    "dataset": dataset,
                    "model": model,
                    "step": step,
                    "seed": seed,
                    "condition_key": condition_key,
                    "condition": condition,
                    "autocompleted": autocomplete,
                    **time_summary,
                    **acc_summary,
                    "compiled_file": str(compiled_path),
                    "time_log_file": str(log_path),
                }
            )

    return per_seed, skipped


def add_relative_time(per_seed, base_condition_key):
    base_time = {}

    for row in per_seed:
        if (
            row["condition_key"] == base_condition_key
            and row["autocompleted"] is False
        ):
            key = (row["dataset"], row["model"], row["step"], row["seed"])
            base_time[key] = row["decoding_time"]

    for row in per_seed:
        key = (row["dataset"], row["model"], row["step"], row["seed"])
        b = base_time.get(key)

        if b is None or not math.isfinite(b) or b == 0:
            row["relative_time_pct"] = float("nan")
        else:
            row["relative_time_pct"] = 100.0 * (row["decoding_time"]-b) / b


def mean_std(values):
    values = [v for v in values if v is not None and math.isfinite(v)]
    if not values:
        return float("nan"), float("nan")
    if len(values) == 1:
        return values[0], 0.0
    return mean(values), stdev(values)


def condition_sort_key(condition: str):
    no_dash = condition.rstrip("-")
    try:
        idx = CONDITION_KEYS.index(no_dash)
    except ValueError:
        idx = 999

    is_auto = not condition.endswith("-")
    return idx, int(is_auto)


def aggregate(per_seed):
    groups = defaultdict(list)

    for row in per_seed:
        key = (
            row["dataset"],
            row["model"],
            row["step"],
            row["condition"],
        )
        groups[key].append(row)

    summary_rows = []

    for (dataset, model, step, condition), rows in groups.items():
        seeds = sorted({r["seed"] for r in rows})
        n_instances = sorted({r["n_instances"] for r in rows})
        n_time_instances = sorted({r["n_time_instances"] for r in rows})
        condition_keys = sorted({r["condition_key"] for r in rows})

        time_m, time_s = mean_std([r["decoding_time"] for r in rows])
        rel_m, rel_s = mean_std([r["relative_time_pct"] for r in rows])
        syn_m, syn_s = mean_std([r["syntax_acc"] for r in rows])
        fun_m, fun_s = mean_std([r["functional_acc"] for r in rows])

        summary_rows.append(
            {
                "dataset": dataset,
                "model": model,
                "step": step,
                "condition_key": ";".join(condition_keys),
                "condition": condition,
                "seeds": ";".join(map(str, seeds)),
                "n_seeds": len(seeds),
                "n_instances": ";".join(map(str, n_instances)),
                "n_time_instances": ";".join(map(str, n_time_instances)),
                "decoding_time_mean": time_m,
                "decoding_time_std": time_s,
                "relative_time_pct_mean": rel_m,
                "relative_time_pct_std": rel_s,
                "syntax_acc_mean": syn_m,
                "syntax_acc_std": syn_s,
                "functional_acc_mean": fun_m,
                "functional_acc_std": fun_s,
            }
        )

    summary_rows.sort(
        key=lambda r: (
            r["dataset"],
            r["model"],
            r["step"],
            condition_sort_key(r["condition"]),
        )
    )

    return summary_rows


def write_csv(path: Path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)

    if not rows:
        path.write_text("")
        return

    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def parse_int_set(s: str):
    return {int(x) for x in s.split(",") if x.strip()}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--eval-root", default="eval_results")
    parser.add_argument("--log-root", default="./result_logging")
    parser.add_argument("--out", default="eval_results/summary.csv")
    parser.add_argument("--detail-out", default="eval_results/per_seed_detail.csv")
    parser.add_argument("--seeds", default="42,43,44")
    parser.add_argument("--steps", default="16,32,64,128,256")
    parser.add_argument(
        "--base-condition-key",
        default="unconstrained",
        choices=CONDITION_KEYS,
        help="Condition key used as denominator for relative_time_pct.",
    )
    args = parser.parse_args()

    seeds = parse_int_set(args.seeds)
    steps = parse_int_set(args.steps)

    per_seed, skipped = collect_per_seed(
        eval_root=Path(args.eval_root),
        log_root=Path(args.log_root),
        seeds=seeds,
        steps=steps,
    )
    add_relative_time(per_seed, base_condition_key=args.base_condition_key)
    summary = aggregate(per_seed)

    write_csv(Path(args.detail_out), per_seed)
    write_csv(Path(args.out), summary)

    print(f"Wrote {args.detail_out} ({len(per_seed)} rows)")
    print(f"Wrote {args.out} ({len(summary)} rows)")

    if skipped:
        print("Skipped files:")
        for k in sorted(skipped):
            print(f"  {k}: {skipped[k]}")


if __name__ == "__main__":
    main()