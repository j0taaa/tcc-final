"""Lightweight profiler for ENFA construction experiments.

Enable with:
    CONSTRAINED_DIFFUSION_PROFILE_ENFA=1

Optional outputs:
    CONSTRAINED_DIFFUSION_PROFILE_ENFA_OUTPUT=/path/profile.json
    CONSTRAINED_DIFFUSION_PROFILE_ENFA_PRINT=1

The profiler is intentionally dependency-free and cheap when disabled.
"""

from __future__ import annotations

import atexit
import json
import os
import threading
import time
from collections import defaultdict
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Any, Dict

_ENABLED = os.environ.get("CONSTRAINED_DIFFUSION_PROFILE_ENFA", "0") == "1"
_OUTPUT = os.environ.get("CONSTRAINED_DIFFUSION_PROFILE_ENFA_OUTPUT")
_PRINT = os.environ.get("CONSTRAINED_DIFFUSION_PROFILE_ENFA_PRINT", "0") == "1"

_lock = threading.RLock()
_times: Dict[str, float] = defaultdict(float)
_counts: Dict[str, int] = defaultdict(int)
_values_sum: Dict[str, float] = defaultdict(float)
_values_count: Dict[str, int] = defaultdict(int)
_values_min: Dict[str, float] = {}
_values_max: Dict[str, float] = {}
_metadata: Dict[str, Any] = {}
_started_at = time.time()
_instance_seq = 0
_current_instance = None


def enabled() -> bool:
    return _ENABLED


@dataclass
class _Timer:
    name: str
    t0: float = 0.0

    def __enter__(self):
        if _ENABLED:
            self.t0 = time.perf_counter()
        return self

    def __exit__(self, exc_type, exc, tb):
        if _ENABLED:
            dt = time.perf_counter() - self.t0
            with _lock:
                _times[self.name] += dt
                _counts[self.name] += 1
        return False


def timer(name: str):
    if not _ENABLED:
        return _NoopTimer()
    return _Timer(name)


def now() -> float:
    return time.perf_counter()


def add_time(name: str, dt: float, n: int = 1) -> None:
    if not _ENABLED:
        return
    with _lock:
        _times[name] += float(dt)
        _counts[name] += int(n)


class _NoopTimer:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


def count(name: str, n: int = 1) -> None:
    if not _ENABLED:
        return
    with _lock:
        _counts[name] += int(n)


def value(name: str, x: float) -> None:
    if not _ENABLED:
        return
    x = float(x)
    with _lock:
        _values_sum[name] += x
        _values_count[name] += 1
        _values_min[name] = min(_values_min.get(name, x), x)
        _values_max[name] = max(_values_max.get(name, x), x)


def set_metadata(**kwargs: Any) -> None:
    if not _ENABLED:
        return
    with _lock:
        _metadata.update(kwargs)


def begin_instance(instance_id: Any = None, **metadata: Any) -> None:
    """Record the start of a new decoding instance.

    This does not reset totals. It only increments counters and records the latest
    instance id for profiles collected over a whole benchmark run.
    """
    if not _ENABLED:
        return
    global _instance_seq, _current_instance
    with _lock:
        _instance_seq += 1
        _current_instance = instance_id
        _counts["instance.count"] += 1
        if metadata:
            _metadata.update({f"last_instance.{k}": v for k, v in metadata.items()})


def reset() -> None:
    if not _ENABLED:
        return
    with _lock:
        _times.clear()
        _counts.clear()
        _values_sum.clear()
        _values_count.clear()
        _values_min.clear()
        _values_max.clear()
        _metadata.clear()


def snapshot() -> dict[str, Any]:
    with _lock:
        times = dict(_times)
        counts = dict(_counts)
        values = {}
        for k, total in _values_sum.items():
            c = _values_count.get(k, 0)
            values[k] = {
                "count": c,
                "sum": total,
                "avg": total / c if c else 0.0,
                "min": _values_min.get(k),
                "max": _values_max.get(k),
            }
        timer_stats = {}
        for k, total in times.items():
            c = counts.get(k, 0)
            timer_stats[k] = {
                "count": c,
                "total": total,
                "avg": total / c if c else 0.0,
            }
        return {
            "metadata": {
                **_metadata,
                "enabled": _ENABLED,
                "pid": os.getpid(),
                "started_at": _started_at,
                "elapsed_wall_s": time.time() - _started_at,
                "current_instance": repr(_current_instance),
                "instance_seq": _instance_seq,
            },
            "timers": timer_stats,
            "counts": counts,
            "values": values,
        }


def print_report(prefix: str = "[ENFA-PROFILE]") -> None:
    if not _ENABLED:
        return
    snap = snapshot()
    print(prefix, "metadata", snap["metadata"])
    for name, stat in sorted(snap["timers"].items()):
        print(
            f"{prefix} timer {name}: total={stat['total']:.6f}s "
            f"count={stat['count']} avg={stat['avg']:.6f}s"
        )
    for name, val in sorted(snap["values"].items()):
        print(
            f"{prefix} value {name}: count={val['count']} avg={val['avg']:.3f} "
            f"min={val['min']:.3f} max={val['max']:.3f} sum={val['sum']:.3f}"
        )
    for name, c in sorted(snap["counts"].items()):
        if name in snap["timers"]:
            continue
        print(f"{prefix} count {name}: {c}")


def dump(path: str | None = None) -> None:
    if not _ENABLED:
        return
    path = path or _OUTPUT
    if not path:
        return
    snap = snapshot()
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    # .jsonl appends one snapshot per process; .json overwrites by default.
    if path.endswith(".jsonl"):
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps(snap, ensure_ascii=False) + "\n")
    else:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(snap, f, indent=2, ensure_ascii=False, sort_keys=True)


def _atexit_report() -> None:
    if not _ENABLED:
        return
    if _OUTPUT:
        dump(_OUTPUT)
    if _PRINT:
        print_report()


atexit.register(_atexit_report)
