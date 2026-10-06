#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import math
import re
from collections import defaultdict
from pathlib import Path
from statistics import mean, stdev
from typing import Any, Iterable

TASKS = ("cpp", "json", "smiles")

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

def safe_float(x: Any, default: float = float("nan")) -> float:
    try:
        if x is None:
            return default
        v = float(x)
        return v if math.isfinite(v) else default
    except Exception:
        return default


def safe_int(x: Any, default: int = 0) -> int:
    v = safe_float(x, float("nan"))
    return int(v) if math.isfinite(v) else default


def finite_values(xs: Iterable[Any]) -> list[float]:
    out = []
    for x in xs:
        v = safe_float(x)
        if math.isfinite(v):
            out.append(v)
    return out


def mean_std(xs: Iterable[Any]) -> tuple[float, float]:
    vals = finite_values(xs)
    if not vals:
        return float("nan"), float("nan")
    if len(vals) == 1:
        return vals[0], 0.0
    return mean(vals), stdev(vals)


def sum_finite(xs: Iterable[Any]) -> float:
    vals = finite_values(xs)
    return sum(vals) if vals else float("nan")


def read_records(path: Path) -> list[dict[str, Any]]:
    """Read json/jsonl as records. Accepts list, single object, or common wrapper keys."""
    if path.suffix == ".jsonl":
        rows: list[dict[str, Any]] = []
        with path.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                    if isinstance(obj, dict):
                        rows.append(obj)
                except Exception:
                    pass
        return rows

    with path.open("r", encoding="utf-8") as f:
        obj = json.load(f)

    if isinstance(obj, list):
        return [x for x in obj if isinstance(x, dict)]
    if isinstance(obj, dict):
        for key in ("results", "data", "instances", "rows", "logs", "records"):
            if isinstance(obj.get(key), list):
                return [x for x in obj[key] if isinstance(x, dict)]
        return [obj]
    return []


def read_json_object(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        obj = json.load(f)
    return obj if isinstance(obj, dict) else {"records": obj}

def strip_eval_suffixes(name: str) -> str:
    for suffix in (
        ".autocompleted.compiled.jsonl",
        ".compiled.jsonl",
        ".jsonl",
        ".json",
    ):
        if name.endswith(suffix):
            return name[: -len(suffix)]
    return name


def is_autocompleted_eval(path: Path) -> bool:
    n = path.name.lower()
    return n.endswith(".autocompleted.compiled.jsonl") or "autocompleted" in n or "autocomplete" in n


def raw_eval_for_auto(auto_path: Path) -> Path:
    return auto_path.with_name(auto_path.name.replace(".autocompleted.compiled.jsonl", ".compiled.jsonl"))


def parse_seed_step(path: Path) -> tuple[int | None, int | None]:
    name = path.name
    seed = None
    step = None
    for pat in (
        r"(?:^|[_\-.])s=(\d+)(?:[_\-.]|$)",
        r"(?:^|[_\-.])seed=(\d+)(?:[_\-.]|$)",
        r"(?:^|[_\-.])seed(\d+)(?:[_\-.]|$)",
    ):
        m = re.search(pat, name, flags=re.IGNORECASE)
        if m:
            seed = int(m.group(1))
            break
    for pat in (
        r"(?:^|[_\-.])sz=(\d+)(?:[_\-.]|$)",
        r"(?:^|[_\-.])steps=(\d+)(?:[_\-.]|$)",
        r"(?:^|[_\-.])step=(\d+)(?:[_\-.]|$)",
        r"(?:^|[_\-.])steps(\d+)(?:[_\-.]|$)",
        r"(?:^|[_\-.])step(\d+)(?:[_\-.]|$)",
    ):
        m = re.search(pat, name, flags=re.IGNORECASE)
        if m:
            step = int(m.group(1))
            break
    return seed, step


def parse_condition_key(path: Path) -> str | None:
    stem = strip_eval_suffixes(path.name)
    stem = re.sub(r"(?:^|_)autocompleted(?:_|$)", "_", stem, flags=re.IGNORECASE)
    for key in sorted(CONDITION_KEYS, key=len, reverse=True):
        if re.search(rf"(?:^|_){re.escape(key)}(?:_|$)", stem, flags=re.IGNORECASE):
            return key
    return None


def parse_condition_label(path: Path) -> str | None:
    key = parse_condition_key(path)
    if key is None:
        return None
    return key if is_autocompleted_eval(path) else f"{key}-"


def infer_task_from_path(path: Path) -> str:
    parts = [p.lower() for p in path.parts]
    stem = path.stem.lower()
    for task in TASKS:
        if task in parts:
            return task
    for task in TASKS:
        if stem == task or stem.startswith(task + "_") or f"_{task}_" in stem:
            return task
    if "humaneval" in stem or "cpp" in stem:
        return "cpp"
    if "json" in stem:
        return "json"
    if "smiles" in stem:
        return "smiles"
    return "unknown"


def parse_model(path: Path, dataset: str) -> str:
    name = strip_eval_suffixes(path.name)
    name = re.sub(r"(?:^|_)autocompleted(?:_|$)", "_", name, flags=re.IGNORECASE)

    for key in sorted(CONDITION_KEYS, key=len, reverse=True):
        name = re.sub(rf"(?:^|_){re.escape(key)}(?:_|$)", "_", name, flags=re.IGNORECASE)

    name = re.split(r"[_\-.]s=\d+", name, flags=re.IGNORECASE)[0]
    name = re.split(r"[_\-.]seed=\d+", name, flags=re.IGNORECASE)[0]
    name = re.split(r"[_\-.]seed\d+", name, flags=re.IGNORECASE)[0]

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

    name = re.sub(r"_+", "_", name).strip("_-. ")
    return name or "unknown_model"


def eval_to_log_path(eval_path: Path, log_root: Path, dataset: str) -> Path:
    raw_name = eval_path.name
    raw_name = raw_name.replace(".autocompleted.compiled.jsonl", ".json")
    raw_name = raw_name.replace(".compiled.jsonl", ".json")
    raw_name = raw_name.replace(".jsonl", ".json")
    return log_root / dataset / raw_name


def collect_eval_files(eval_root: Path) -> list[Path]:
    files = []
    for task in TASKS:
        d = eval_root / task
        if not d.exists():
            continue
        files.extend(d.rglob("*.compiled.jsonl"))
    if not files:
        for p in eval_root.rglob("*.jsonl"):
            n = p.name.lower()
            if "summary" in n or "per_seed" in n or "analysis_" in n:
                continue
            files.append(p)
    return sorted(files)

def summarize_compiled_rows(rows: list[dict[str, Any]]) -> dict[str, Any]:
    n = len(rows)
    if n == 0:
        return {
            "eval_file_found": False,
            "n_instances": 0,
            "syntax_acc": float("nan"),
            "functional_acc": float("nan"),
            "syntax_ok_count": 0,
            "passed_tests_count": 0,
        }
    syntax_ok = sum(1 for r in rows if bool(r.get("syntax_ok", False)))
    passed = sum(1 for r in rows if bool(r.get("passed_tests", False)))
    return {
        "eval_file_found": True,
        "n_instances": n,
        "syntax_acc": 100.0 * syntax_ok / n,
        "functional_acc": 100.0 * passed / n,
        "syntax_ok_count": syntax_ok,
        "passed_tests_count": passed,
    }


def summarize_autocompleted_accuracy(auto_path: Path) -> dict[str, Any]:
    raw_path = raw_eval_for_auto(auto_path)
    if not raw_path.exists():
        return summarize_compiled_rows(read_records(auto_path))

    raw_rows = read_records(raw_path)
    auto_rows = read_records(auto_path)
    auto_by_id = {r.get("instance_id"): r for r in auto_rows if r.get("instance_id") is not None}

    merged = []
    for raw in raw_rows:
        iid = raw.get("instance_id")
        auto = auto_by_id.get(iid)
        if auto is not None and "skipped" not in auto:
            merged.append(auto)
        else:
            merged.append(raw)
    return summarize_compiled_rows(merged)

def nested_get(obj: dict[str, Any], dotted: str) -> Any:
    cur: Any = obj
    for part in dotted.split("."):
        if not isinstance(cur, dict) or part not in cur:
            return None
        cur = cur[part]
    return cur


def timer_total(obj: dict[str, Any], *exact_keys: str) -> float:
    timers = obj.get("timers", {}) if isinstance(obj, dict) else {}
    total = 0.0
    found = False
    for key in exact_keys:
        t = timers.get(key)
        if isinstance(t, dict):
            v = safe_float(t.get("total"), float("nan"))
            if not math.isfinite(v):
                v = safe_float(t.get("wall_s"), float("nan"))
            if math.isfinite(v):
                total += v
                found = True
        else:
            v = safe_float(t, float("nan"))
            if math.isfinite(v):
                total += v
                found = True
    return total if found else float("nan")


def timer_total_matching(
    obj: dict[str, Any],
    include_any: tuple[str, ...] = (),
    include_all: tuple[str, ...] = (),
    exclude_any: tuple[str, ...] = (),
) -> float:
    timers = obj.get("timers", {}) if isinstance(obj, dict) else {}
    total = 0.0
    found = False
    ia = tuple(s.lower() for s in include_any)
    iall = tuple(s.lower() for s in include_all)
    ea = tuple(s.lower() for s in exclude_any)

    for key, t in timers.items():
        k = str(key).lower()
        if ia and not any(x in k for x in ia):
            continue
        if iall and not all(x in k for x in iall):
            continue
        if ea and any(x in k for x in ea):
            continue
        if isinstance(t, dict):
            v = safe_float(t.get("total"), float("nan"))
            if not math.isfinite(v):
                v = safe_float(t.get("wall_s"), float("nan"))
        else:
            v = safe_float(t, float("nan"))
        if math.isfinite(v):
            total += v
            found = True
    return total if found else float("nan")


def value_stat(obj: dict[str, Any], key: str, stat: str) -> float:
    values = obj.get("values", {}) if isinstance(obj, dict) else {}
    d = values.get(key)
    if isinstance(d, dict):
        return safe_float(d.get(stat))
    return float("nan")


def count_value(obj: dict[str, Any], key: str) -> float:
    counts = obj.get("counts", {}) if isinstance(obj, dict) else {}
    return safe_float(counts.get(key), default=0.0)


def parallel_commit_success_rate_pct(selected_count: Any, no_selection: Any) -> float:
    sc = safe_float(selected_count, float("nan"))
    ns = safe_float(no_selection, float("nan"))
    if not math.isfinite(sc):
        sc = 0.0
    if not math.isfinite(ns):
        ns = 0.0
    denom = sc + ns
    return 100.0 * sc / denom if denom > 0 else float("nan")


def top_level_wall_s(obj: dict[str, Any]) -> float:
    candidates = [
        obj.get("wall_s"),
        obj.get("elapsed_wall_s"),
        obj.get("time_s"),
        obj.get("decoding_time"),
        nested_get(obj, "metadata.wall_s"),
        nested_get(obj, "metadata.elapsed_wall_s"),
        nested_get(obj, "metadata.time_s"),
    ]
    for c in candidates:
        v = safe_float(c)
        if math.isfinite(v):
            return v
    for k in ("wall_s", "total", "decode.total", "decoding.total"):
        v = timer_total(obj, k)
        if math.isfinite(v):
            return v
    return float("nan")


def empty_profile_summary() -> dict[str, Any]:
    keys = [
        "profile_log_found",
        "decoding_time_s",
        "lexing_time_s",
        "lex_rust_s",
        "lex_materialize_s",
        "dfa_minimization_time_s",
        "dfa_determinization_time_s",
        "dfa_build_s",
        "intersection_time_s",
        "decode_intersection_s",
        "decode_graph_intersection_s",
        "regular_cover_intersection_s",
        "hit_rate_pct",
        "hit_count",
        "miss_count",
        "avg_commit",
        "avg_commit_selected_only",
        "regular_cover_selected_sum",
        "regular_cover_selected_count",
        "regular_cover_no_selection",
        "parallel_commit_success_rate_pct",
        "lexing_calls",
        "lexing_misses",
        "decode_intersection_calls",
        "regular_cover_exact_calls",
        "instance_count_from_log",
    ]
    out = {k: float("nan") for k in keys}
    out["profile_log_found"] = False
    for k in ("hit_count", "miss_count", "lexing_calls", "lexing_misses", "decode_intersection_calls", "regular_cover_exact_calls", "instance_count_from_log"):
        out[k] = 0
    return out


def summarize_profile_object(obj: dict[str, Any]) -> dict[str, Any]:
    counts = obj.get("counts", {}) if isinstance(obj.get("counts"), dict) else {}
    values = obj.get("values", {}) if isinstance(obj.get("values"), dict) else {}

    lex_rust_s = timer_total(obj, "lex.rust_lex_string")
    lex_materialize_s = timer_total(obj, "lex.materialize_result")
    lex_matching_s = timer_total_matching(obj, include_any=("lex", "lexer", "lexing"), exclude_any=("hit", "miss"))
    lexing_time_s = sum_finite([lex_rust_s, lex_materialize_s])
    if not math.isfinite(lexing_time_s):
        lexing_time_s = lex_matching_s

    dfa_min_s = timer_total(obj, "generated_language.minimize", "dfa.minimize", "dfa_minimize")
    if not math.isfinite(dfa_min_s):
        dfa_min_s = timer_total_matching(obj, include_any=("minimize", "minimization"), exclude_any=("intersection",))

    dfa_det_s = timer_total_matching(
        obj,
        include_any=("determin", "detrmin"),
        exclude_any=("intersection",),
    )
    dfa_build_s = sum_finite([dfa_min_s, dfa_det_s])

    decode_inter_s = timer_total(obj, "decode.intersection")
    decode_graph_inter_s = timer_total(obj, "decode.graph_intersection")
    rc_inter_s = timer_total(obj, "regular_cover.intersection")
    inter_matching_s = timer_total_matching(obj, include_any=("intersection",), exclude_any=("example_word",))
    intersection_time_s = sum_finite([decode_inter_s, decode_graph_inter_s, rc_inter_s])
    if not math.isfinite(intersection_time_s):
        intersection_time_s = inter_matching_s

    hit_rate_pct = float("nan")
    for key in (
        "hit_rate",
        "cache.hit_rate",
        "fragment_cache.hit_rate",
        "lexing.hit_rate",
        "regular_cover.cache.hit_rate",
    ):
        for stat in ("avg", "mean", "value"):
            v = value_stat(obj, key, stat)
            if math.isfinite(v):
                hit_rate_pct = 100.0 * v if v <= 1.0 else v
                break
        if math.isfinite(hit_rate_pct):
            break

    hit_count = 0.0
    miss_count = 0.0
    for k, v in counts.items():
        kl = str(k).lower()
        fv = safe_float(v, default=0.0)
        if "hit" in kl and not any(x in kl for x in ("rate", "no_hit")):
            hit_count += fv
        if "miss" in kl or "slow_path" in kl or "no_witness" in kl:
            miss_count += fv
    if not math.isfinite(hit_rate_pct) and hit_count + miss_count > 0:
        hit_rate_pct = 100.0 * hit_count / (hit_count + miss_count)

    lexing_calls = count_value(obj, "inject_lexings.calls") or count_value(obj, "lex.calls")
    lexing_misses = count_value(obj, "inject_lexings.slow_path") or count_value(obj, "lex.misses")

    selected_sum = value_stat(obj, "regular_cover.batch.selected_size", "sum")
    selected_count = value_stat(obj, "regular_cover.batch.selected_size", "count")
    selected_avg = value_stat(obj, "regular_cover.batch.selected_size", "avg")
    no_selection = count_value(obj, "regular_cover.batch.no_selection")
    if not math.isfinite(no_selection):
        no_selection = 0.0
    parallel_success_rate = parallel_commit_success_rate_pct(selected_count, no_selection)

    if math.isfinite(selected_sum) and math.isfinite(selected_count) and selected_count > 0:
        avg_commit_selected_only = selected_sum / selected_count
        denom = selected_count + no_selection
        avg_commit = selected_sum / denom if denom > 0 else float("nan")
    elif math.isfinite(selected_avg):
        avg_commit_selected_only = selected_avg
        avg_commit = selected_avg
    else:
        avg_commit = float("nan")
        avg_commit_selected_only = float("nan")
        for k in values:
            kl = str(k).lower()
            if ("commit" in kl or "selected_size" in kl) and isinstance(values[k], dict):
                v = safe_float(values[k].get("avg"), float("nan"))
                if math.isfinite(v):
                    avg_commit = v
                    avg_commit_selected_only = v
                    break

    return {
        "profile_log_found": True,
        "decoding_time_s": top_level_wall_s(obj),
        "lexing_time_s": lexing_time_s,
        "lex_rust_s": lex_rust_s,
        "lex_materialize_s": lex_materialize_s,
        "dfa_minimization_time_s": dfa_min_s,
        "dfa_determinization_time_s": dfa_det_s,
        "dfa_build_s": dfa_build_s,
        "intersection_time_s": intersection_time_s,
        "decode_intersection_s": decode_inter_s,
        "decode_graph_intersection_s": decode_graph_inter_s,
        "regular_cover_intersection_s": rc_inter_s,
        "hit_rate_pct": hit_rate_pct,
        "hit_count": int(hit_count),
        "miss_count": int(miss_count),
        "avg_commit": avg_commit,
        "avg_commit_selected_only": avg_commit_selected_only,
        "regular_cover_selected_sum": selected_sum,
        "regular_cover_selected_count": selected_count,
        "regular_cover_no_selection": no_selection,
        "parallel_commit_success_rate_pct": parallel_success_rate,
        "lexing_calls": int(lexing_calls),
        "lexing_misses": int(lexing_misses),
        "decode_intersection_calls": safe_int(counts.get("decode.intersection.calls")),
        "regular_cover_exact_calls": safe_int(counts.get("regular_cover.exact.calls")),
        "instance_count_from_log": safe_int(counts.get("instance.count")),
    }


def summarize_result_logging(path: Path | None, autocomplete: bool = False) -> dict[str, Any]:
    if path is None or not path.exists():
        return empty_profile_summary()

    try:
        if path.suffix == ".json":
            obj = read_json_object(path)
            if isinstance(obj, dict) and ("timers" in obj or "counts" in obj or "values" in obj or "wall_s" in obj or "metadata" in obj):
                out = summarize_profile_object(obj)
                if autocomplete:
                    auto_t = safe_float(obj.get("time_taken_autocompletion"), float("nan"))
                    if not math.isfinite(auto_t):
                        auto_t = safe_float(nested_get(obj, "metadata.time_taken_autocompletion"), float("nan"))
                    if math.isfinite(out["decoding_time_s"]) and math.isfinite(auto_t):
                        out["decoding_time_s"] -= auto_t
                return out
    except Exception:
        pass

    rows = read_records(path)
    per_row = [summarize_profile_object(r) for r in rows]
    out = empty_profile_summary()
    out["profile_log_found"] = bool(rows)
    if not rows:
        return out

    metric_cols = [k for k in out.keys() if k != "profile_log_found"]
    for col in metric_cols:
        vals = [r.get(col) for r in per_row]
        if col.endswith("_count") or col in {"hit_count", "miss_count", "lexing_calls", "lexing_misses", "decode_intersection_calls", "regular_cover_exact_calls", "instance_count_from_log"}:
            fv = finite_values(vals)
            out[col] = int(sum(fv)) if fv else 0
        else:
            m, _ = mean_std(vals)
            out[col] = m
    return out

def make_meta_from_eval(path: Path) -> dict[str, Any]:
    dataset = infer_task_from_path(path)
    seed, step = parse_seed_step(path)
    return {
        "task": dataset,
        "dataset": dataset,
        "model": parse_model(path, dataset),
        "condition_key": parse_condition_key(path) or "unknown",
        "condition": parse_condition_label(path) or "unknown",
        "seed": seed if seed is not None else "",
        "step": step if step is not None else "",
        "autocompleted": is_autocompleted_eval(path),
    }


def build_log_fallback_index(log_root: Path) -> dict[tuple[str, str, str, str, str], list[Path]]:
    idx: dict[tuple[str, str, str, str, str], list[Path]] = defaultdict(list)
    for p in log_root.rglob("*.json"):
        dataset = infer_task_from_path(p)
        seed, step = parse_seed_step(p)
        cond = parse_condition_key(p) or "unknown"
        model = parse_model(p, dataset)
        key = (dataset, model, cond, str(seed or ""), str(step or ""))
        idx[key].append(p)
    return idx


def collect_per_seed(eval_root: Path, log_root: Path, seeds: set[int] | None, steps: set[int] | None) -> tuple[list[dict[str, Any]], dict[str, int], list[Path]]:
    eval_files = collect_eval_files(eval_root)
    log_fallback = build_log_fallback_index(log_root)
    used_logs: set[Path] = set()
    rows = []
    skipped: dict[str, int] = defaultdict(int)

    for eval_path in eval_files:
        meta = make_meta_from_eval(eval_path)
        seed = meta["seed"]
        step = meta["step"]

        if seed == "":
            skipped["missing_seed"] += 1
            continue
        if step == "":
            skipped["missing_step"] += 1
            continue
        if seeds is not None and int(seed) not in seeds:
            skipped["seed_filter"] += 1
            continue
        if steps is not None and int(step) not in steps:
            skipped["step_filter"] += 1
            continue
        if meta["condition_key"] == "unknown":
            skipped["missing_condition_key"] += 1
            continue

        if meta["autocompleted"]:
            eval_summary = summarize_autocompleted_accuracy(eval_path)
        else:
            eval_summary = summarize_compiled_rows(read_records(eval_path))

        log_path = eval_to_log_path(eval_path, log_root, str(meta["dataset"]))
        if not log_path.exists():
            k = (str(meta["dataset"]), str(meta["model"]), str(meta["condition_key"]), str(seed), str(step))
            cands = log_fallback.get(k, [])
            log_path = cands[0] if len(cands) == 1 else log_path

        profile_summary = summarize_result_logging(log_path if log_path.exists() else None, autocomplete=bool(meta["autocompleted"]))
        if log_path.exists():
            used_logs.add(log_path.resolve())

        rows.append({
            **meta,
            **eval_summary,
            **profile_summary,
            "eval_file": str(eval_path),
            "profile_log_file": str(log_path) if log_path.exists() else "",
        })

    orphan_logs = []
    for p in log_root.rglob("*.json"):
        if p.resolve() not in used_logs:
            orphan_logs.append(p)

    rows.sort(key=lambda r: (
        str(r.get("dataset", "")), str(r.get("model", "")), str(r.get("step", "")),
        str(r.get("condition", "")), str(r.get("seed", "")), str(r.get("eval_file", "")),
    ))
    return rows, skipped, sorted(orphan_logs)


def add_relative_time(per_seed: list[dict[str, Any]], base_condition_key: str) -> None:
    base: dict[tuple[Any, ...], float] = {}
    for r in per_seed:
        if r.get("condition_key") == base_condition_key and not r.get("autocompleted"):
            k = (r.get("dataset"), r.get("model"), r.get("step"), r.get("seed"))
            t = safe_float(r.get("decoding_time_s"))
            if math.isfinite(t):
                base[k] = t
    for r in per_seed:
        k = (r.get("dataset"), r.get("model"), r.get("step"), r.get("seed"))
        b = base.get(k)
        t = safe_float(r.get("decoding_time_s"))
        if b is None or not math.isfinite(b) or b == 0 or not math.isfinite(t):
            r["relative_time_pct"] = float("nan")
        else:
            r["relative_time_pct"] = 100.0 * (t - b) / b


def aggregate(per_seed: list[dict[str, Any]]) -> list[dict[str, Any]]:
    group_keys = ["task", "dataset", "model", "step", "condition_key", "condition", "autocompleted"]
    groups: dict[tuple[Any, ...], list[dict[str, Any]]] = defaultdict(list)
    for r in per_seed:
        groups[tuple(r.get(k, "") for k in group_keys)].append(r)

    metric_cols = [
        "n_instances", "syntax_acc", "functional_acc", "decoding_time_s", "relative_time_pct",
        "lexing_time_s", "lex_rust_s", "lex_materialize_s",
        "dfa_minimization_time_s", "dfa_determinization_time_s", "dfa_build_s",
        "intersection_time_s", "decode_intersection_s", "decode_graph_intersection_s", "regular_cover_intersection_s",
        "hit_rate_pct", "hit_count", "miss_count", "avg_commit", "avg_commit_selected_only",
        "regular_cover_selected_sum", "regular_cover_selected_count", "regular_cover_no_selection",
        "parallel_commit_success_rate_pct",
        "lexing_calls", "lexing_misses", "decode_intersection_calls", "regular_cover_exact_calls",
    ]

    out_rows = []
    for key, rows in sorted(groups.items(), key=lambda kv: tuple(str(x) for x in kv[0])):
        out = dict(zip(group_keys, key))
        seeds = sorted({str(r.get("seed", "")) for r in rows if str(r.get("seed", ""))})
        out["seeds"] = ";".join(seeds)
        out["n_seeds"] = len(seeds)
        out["eval_file_found"] = sum(1 for r in rows if r.get("eval_file_found"))
        out["profile_log_found"] = sum(1 for r in rows if r.get("profile_log_found"))
        for col in metric_cols:
            m, s = mean_std([r.get(col) for r in rows])
            out[f"{col}_mean"] = m
            out[f"{col}_std"] = s
        out_rows.append(out)
    return out_rows


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return

    preferred = [
        "task", "dataset", "model", "step", "seed", "condition_key", "condition", "autocompleted",
        "n_seeds", "seeds", "eval_file_found", "profile_log_found",
        "n_instances", "syntax_acc", "functional_acc", "syntax_ok_count", "passed_tests_count",
        "decoding_time_s", "relative_time_pct",
        "lexing_time_s", "dfa_minimization_time_s", "intersection_time_s", "hit_rate_pct", "avg_commit",
        "parallel_commit_success_rate_pct",
        "lex_rust_s", "lex_materialize_s", "dfa_determinization_time_s", "dfa_build_s",
        "decode_intersection_s", "decode_graph_intersection_s", "regular_cover_intersection_s", "avg_commit_selected_only",
        "hit_count", "miss_count", "lexing_calls", "lexing_misses",
        "eval_file", "profile_log_file",
    ]
    keys = []
    seen = set()
    for k in preferred:
        if any(k in r for r in rows) and k not in seen:
            keys.append(k); seen.add(k)
    for r in rows:
        for k in r:
            if k not in seen:
                keys.append(k); seen.add(k)

    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=keys, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)


def parse_int_set(s: str | None) -> set[int] | None:
    if s is None or s.strip() == "" or s.strip().lower() == "all":
        return None
    return {int(x) for x in s.split(",") if x.strip()}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--eval-root", default="results", help="Root containing results/{cpp,json,smiles}/*.compiled.jsonl")
    ap.add_argument("--log-root", default="./result_logging", help="Root containing result_logging/{cpp,json,smiles}/*.json")
    ap.add_argument("--output-dir", default="eval_results")
    ap.add_argument("--seeds", default="42,43,44", help="Comma-separated seeds, or all")
    ap.add_argument("--steps", default="16,32,64,128,256", help="Comma-separated steps, or all")
    ap.add_argument("--base-condition-key", default="unconstrained")
    ap.add_argument("--report-orphans", action="store_true", help="Print examples of log files that have no eval row. They are not written as rows.")
    args = ap.parse_args()

    per_seed, skipped, orphan_logs = collect_per_seed(
        Path(args.eval_root), Path(args.log_root), parse_int_set(args.seeds), parse_int_set(args.steps)
    )
    add_relative_time(per_seed, args.base_condition_key)
    summary = aggregate(per_seed)

    out_dir = Path(args.output_dir)
    detail_path = out_dir / "analysis_per_seed_detail.csv"
    summary_path = out_dir / "analysis_summary.csv"
    write_csv(detail_path, per_seed)
    write_csv(summary_path, summary)

    no_log = [r for r in per_seed if r.get("eval_file") and not r.get("profile_log_file")]
    print(f"Eval root: {Path(args.eval_root)}")
    print(f"Log root: {Path(args.log_root)}")
    print(f"Wrote {detail_path} ({len(per_seed)} rows)")
    print(f"Wrote {summary_path} ({len(summary)} rows)")
    print(f"Rows with eval but no log: {len(no_log)}")
    print(f"Orphan log files not included as rows: {len(orphan_logs)}")

    if skipped:
        print("Skipped eval files:")
        for k in sorted(skipped):
            print(f"  {k}: {skipped[k]}")
    if no_log:
        print("\nExamples with eval but no log:")
        for r in no_log[:10]:
            print("  ", r.get("dataset"), r.get("model"), r.get("condition_key"), "seed=", r.get("seed"), "step=", r.get("step"), "eval=", r.get("eval_file"))
    if args.report_orphans and orphan_logs:
        print("\nExamples of orphan logs:")
        for p in orphan_logs[:10]:
            print("  ", p)


if __name__ == "__main__":
    main()
