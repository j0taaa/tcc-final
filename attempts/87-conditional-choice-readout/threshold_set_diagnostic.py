"""Exploratory threshold-set structure on immutable A87 training captures.

Freeze this source and dependencies before reading inputs/capture. All eight
complete INTERIOR cases and all forty thresholds 2**(-j), j=1..40, are required.
This different operation neither rescues V1 nor validates conformal coverage.
No policy replay, new forwards, threshold selection, speed or test-set claim.
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import subprocess
from pathlib import Path

from matching_probe import F, Problem, min_cover, prepare
from star_certificates import Instance

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
INPUTS = HERE / "native-inputs-v1.json"
CAPTURE = ROOT / "docs/artifacts/raw/a87_native_v1.jsonl.gz"
EXPECTED = "c828867d81991ee26f8887858839471e2c3fdbdac6a677993d47cdd024675f04"


def filtered(p, values):
    return frozenset(
        (source, target)
        for (a, b), (u, v) in zip(p.edges, values, strict=True)
        for source, target, x in ((a, b, u), (b, a, v))
        if p.tau - p.caps[target] < x < p.tau
    )


def run():
    hashes = {}
    paths = [
        Path(__file__).resolve(),
        INPUTS,
        HERE / "matching_probe.py",
        HERE / "online_probe.py",
        HERE / "star_certificates.py",
        CAPTURE,
    ]
    for path in paths:
        name = str(path.relative_to(ROOT))
        frozen = subprocess.check_output(["git", "show", f"HEAD:{name}"], cwd=ROOT)
        hashes[name] = hashlib.sha256(path.read_bytes()).hexdigest()
        if hashlib.sha256(frozen).hexdigest() != hashes[name]:
            raise ValueError(f"freeze exact source/input/capture before reading: {name}")
    raw = gzip.decompress(CAPTURE.read_bytes())
    if hashlib.sha256(raw).hexdigest() != EXPECTED:
        raise ValueError("uncompressed capture SHA256 mismatch")
    data = json.loads(INPUTS.read_text())
    records = [json.loads(line) for line in raw.splitlines() if line.strip()]
    producers = [r for r in records if r["type"] == "producer"]
    terminals = [r for r in records if r["type"] == "terminal"]
    if (
        len(data["cases"]) != 8
        or len(data["edges"]) != 77
        or len(producers) != 1
        or producers[0]["hashes"][INPUTS.name] != hashes[str(INPUTS.relative_to(ROOT))]
        or len(terminals) != 1
        or terminals[0]["status"] != "COMPLETE"
    ):
        raise ValueError("incomplete or incompatible capture/input provenance")
    edges, na = tuple(map(tuple, data["edges"])), len(data["a_words"])
    n = na + len(data["b_words"])
    reports = []
    for case in range(8):
        roots = [r for r in records if r["type"] == "root" and r["case"] == case]
        stars = [r for r in records if r["type"] == "star" and r["case"] == case]
        done = [r for r in records if r["type"] == "case_complete" and r["case"] == case]
        if (
            len(roots) != 1
            or len(stars) != n
            or len(done) != 1
            or {r["vertex"] for r in stars} != set(range(n))
            or any(
                r["boundary"] != "INTERIOR" or any(r["zero_counts_clean_vocab"])
                for r in roots + stars
            )
        ):
            raise ValueError("all eight cases must be complete and strictly INTERIOR")
        root, stars = roots[0], {r["vertex"]: r for r in stars}
        caps = tuple(F(*x) for x in root["caps"])
        values = tuple(
            (F(*stars[a]["components"][str(i)]), F(*stars[b]["components"][str(i)]))
            for i, (a, b) in enumerate(edges)
        )
        if (
            len(caps) != n
            or root["row"] != data["cases"][case]["row"]
            or caps != tuple(F(*x) / 2 for x in root["root_a"] + root["root_b"])
        ):
            raise ValueError("invalid root row/caps")
        Instance(
            na,
            caps,
            tuple((*ends, *parts) for ends, parts in zip(edges, values, strict=True)),
            (F(1),) * n,
            interior=True,
        )
        for j in range(1, 41):
            p = Problem(na, caps, edges, F(1, 1 << j))
            actual = filtered(p, values)
            forecast = filtered(p, tuple((2 * caps[a] * caps[b],) * 2 for a, b in edges))
            plan, mandatory = prepare(p, forecast), frozenset(b for _, b in actual)
            good = sum(
                (min(a for a, b in forecast if b == target), target) in actual
                for target in plan.unmatched
            )
            reports.append(
                {
                    "case": case,
                    "j": j,
                    "Hsize": len(p.graph()),
                    "Msize": len(mandatory),
                    "M_eq_C0": mandatory == plan.base,
                    "OPTexact": len(mandatory) + len(min_cover(p, mandatory)),
                    "C0_union_Mcost": len(plan.base | mandatory),
                    "Rsize": len(plan.unmatched),
                    "headcount": len(plan.heads),
                    "forecastfalse": len(plan.heads - mandatory),
                    "forecastmissed": len(mandatory - plan.heads),
                    "selectedwitnessgoodcount": good,
                    "actualsetsize": sum(u + v >= p.tau for u, v in values),
                }
            )
    return {
        "status": "EXPLORATORY_COMPLETE",
        "source_hashes": hashes,
        "uncompressed_capture_sha256": EXPECTED,
        "rows": reports,
        "scope": "structural training-case diagnostic; no coverage/policy/neural/speed claim",
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    with args.output.open("x") as stream:
        try:
            json.dump(run(), stream, indent=2)
        except Exception as error:
            json.dump({"status": "ERROR", "reason": repr(error)}, stream)
            raise
        stream.write("\n")
