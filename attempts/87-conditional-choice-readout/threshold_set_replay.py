"""Exploratory threshold-set query replay; freeze before executing.

All eight existing training cases x forty thresholds; unchanged root-product
forecasts. Exact uniform enumeration of unmatched audit targets; four controls
share pruning/forced completion and the same revealed-star oracle. Report all
320 rows and comparisons, never select a threshold. No new forwards, timing,
conformal coverage, train/test performance or central-theme claim.
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import subprocess
from collections import Counter
from pathlib import Path

import threshold_set_diagnostic as diagnostic
from matching_probe import F, Problem, prepare

CONTROLS = ("mvc", "advice", "lazy_cap", "degree")


def execute(p, forecast, query, method, selected=None):
    """Only callback responses and public data enter acquisition decisions."""
    plan, known, order = prepare(p, forecast), {}, []
    if (
        method not in (*CONTROLS, "matching")
        or (
            method == "matching"
            and (
                (plan.unmatched and selected not in plan.unmatched)
                or (not plan.unmatched and selected is not None)
            )
        )
        or (method != "matching" and selected is not None)
    ):
        raise ValueError("invalid method or uniform audit target")

    def acquire(z):
        if z in known:
            return
        vector = dict(query(z))
        if (
            set(vector) != {i for i, ends in enumerate(p.edges) if z in ends}
            or any(not isinstance(x, F) or not 0 < x < p.caps[z] for x in vector.values())
            or sum(vector.values(), F(0)) >= p.caps[z]
        ):
            raise ValueError("invalid interior star response")
        known[z] = vector
        order.append(z)

    def active():
        result = []
        for i, ends in enumerate(p.edges):
            observed = [known[z][i] for z in ends if z in known]
            unknown = [z for z in ends if z not in known]
            if (len(unknown) == 2 and sum(p.caps[z] for z in unknown) > p.tau) or (
                len(unknown) == 1 and p.tau - p.caps[unknown[0]] < observed[0] < p.tau
            ):
                result.append(i)
        return result

    def force():
        while True:
            pending = [set(p.edges[i]) - known.keys() for i in active()]
            target = next((next(iter(s)) for s in pending if len(s) == 1), None)
            if target is None:
                return
            acquire(target)

    accepted = None
    if method == "matching" and selected is not None:
        source = min(a for a, b in forecast if b == selected)
        assert source in plan.base
        acquire(source)
        edge = next(i for i, ends in enumerate(p.edges) if {source, selected} == set(ends))
        accepted = p.tau - p.caps[selected] < known[source][edge] < p.tau
    force()
    if method in ("matching", "mvc", "advice"):
        chosen = plan.base if method == "mvc" or accepted is False else plan.prediction
        for z in sorted(chosen):
            if z not in known and any(z in p.edges[i] for i in active()):
                acquire(z)
                force()
    else:
        while remaining := active():
            if method == "lazy_cap":
                edge = max(
                    remaining,
                    key=lambda i: (sum(p.caps[z] for z in p.edges[i] if z not in known), -i),
                )
                target = max(set(p.edges[edge]) - known.keys(), key=lambda z: (p.caps[z], -z))
            else:
                degrees = Counter(z for i in remaining for z in p.edges[i] if z not in known)
                target = max(degrees, key=lambda z: (degrees[z], p.caps[z], -z))
            acquire(target)
            force()
    if active():
        raise ValueError("unfinished threshold certificate")
    positives = frozenset(
        i
        for i, ends in enumerate(p.edges)
        if sum((known[z][i] for z in ends if z in known), F(0)) >= p.tau
    )
    return tuple(order), accepted, positives


def replay(p, forecast, values, method, selected=None):
    calls = []

    def query(z):
        assert z not in calls
        calls.append(z)
        return {i: values[i][int(z == b)] for i, (a, b) in enumerate(p.edges) if z in (a, b)}

    order, accepted, positives = execute(p, forecast, query, method, selected)
    assert order == tuple(calls) and len(order) == len(set(order))
    queried = set(order)
    for i, ((a, b), (u, v)) in enumerate(zip(p.edges, values, strict=True)):
        low = (u if a in queried else F(0)) + (v if b in queried else F(0))
        high = (u if a in queried else p.caps[a]) + (v if b in queried else p.caps[b])
        assert {a, b} <= queried or low >= p.tau or high <= p.tau
        assert (i in positives) == (low >= p.tau) == (u + v >= p.tau)
    return len(order), accepted


def run():
    own_hashes = {}
    for path in (Path(__file__).resolve(), Path(diagnostic.__file__).resolve()):
        name = str(path.relative_to(diagnostic.ROOT))
        frozen = subprocess.check_output(["git", "show", f"HEAD:{name}"], cwd=diagnostic.ROOT)
        own_hashes[name] = hashlib.sha256(path.read_bytes()).hexdigest()
        if hashlib.sha256(frozen).hexdigest() != own_hashes[name]:
            raise ValueError(f"freeze exact source before reading capture: {name}")
    structural = diagnostic.run()
    assert structural["status"] == "EXPLORATORY_COMPLETE"
    expected = {(case, j) for case in range(8) for j in range(1, 41)}
    assert len(structural["rows"]) == 320
    assert {(r["case"], r["j"]) for r in structural["rows"]} == expected
    data = json.loads(diagnostic.INPUTS.read_text())
    raw = gzip.decompress(diagnostic.CAPTURE.read_bytes())
    if hashlib.sha256(raw).hexdigest() != diagnostic.EXPECTED:
        raise ValueError("capture changed after structural validation")
    records = [json.loads(line) for line in raw.splitlines() if line.strip()]
    edges, na = tuple(map(tuple, data["edges"])), len(data["a_words"])
    cases = {}
    for case in range(8):
        root = next(r for r in records if r["type"] == "root" and r["case"] == case)
        stars = {r["vertex"]: r for r in records if r["type"] == "star" and r["case"] == case}
        caps = tuple(F(*x) for x in root["caps"])
        values = tuple(
            (F(*stars[a]["components"][str(i)]), F(*stars[b]["components"][str(i)]))
            for i, (a, b) in enumerate(edges)
        )
        cases[case] = caps, values
    rows, sums = [], {name: 0 for name in (*CONTROLS, "best_control")}
    comparisons = {name: Counter(gains=0, losses=0, ties=0) for name in sums}
    own_sum = F(0)
    for facts in structural["rows"]:
        case, j, optimum = facts["case"], facts["j"], facts["OPTexact"]
        caps, values = cases[case]
        p = Problem(na, caps, edges, F(1, 1 << j))
        forecast = diagnostic.filtered(p, tuple((2 * caps[a] * caps[b],) * 2 for a, b in edges))
        plan, actual = prepare(p, forecast), diagnostic.filtered(p, values)
        runs = [
            replay(p, forecast, values, "matching", target)
            for target in sorted(plan.unmatched) or [None]
        ]
        mean = F(sum(cost for cost, _ in runs), len(runs))
        assert mean <= 2 * optimum and all(cost >= optimum for cost, _ in runs)
        if forecast == actual:
            assert all(cost <= optimum + bool(plan.unmatched) for cost, _ in runs)
        passing = sum(accepted is True for _, accepted in runs)
        assert passing == facts["selectedwitnessgoodcount"]
        controls = {name: replay(p, forecast, values, name)[0] for name in CONTROLS}
        assert all(cost >= optimum for cost in controls.values())
        all_controls = {**controls, "best_control": min(controls.values())}
        for name, cost in all_controls.items():
            comparisons[name]["gains" if mean < cost else "losses" if mean > cost else "ties"] += 1
            sums[name] += cost
        own_sum += mean
        rows.append(
            {
                "case": case,
                "j": j,
                "OPT": optimum,
                "root_calls": 1,
                "own_mean_star_calls": mean,
                "own_runs": len(runs),
                "control_star_calls": controls,
                "best_control_star_calls": min(controls.values()),
            }
        )
    return {
        "status": "EXPLORATORY_COMPLETE",
        "source_hashes": {**structural["source_hashes"], **own_hashes},
        "uncompressed_capture_sha256": diagnostic.EXPECTED,
        "rows": rows,
        "aggregate": {
            "own_star_call_sum": own_sum,
            "root_call_sum": 320,
            "control_star_call_sums": sums,
            "comparisons": comparisons,
        },
        "scope": "all 320 fixed training-case/threshold rows; query replay only; no latency, "
        "coverage, neural gain or full-cost claim; planning/RNG/rational costs unmeasured",
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    with args.output.open("x") as stream:
        try:
            json.dump(run(), stream, indent=2, default=lambda x: [x.numerator, x.denominator])
        except Exception as error:
            json.dump({"status": "ERROR", "reason": repr(error)}, stream)
            raise
        stream.write("\n")
