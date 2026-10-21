"""Frozen A87 development diagnostic; no neural calls and no online probe.

Read heads only after this source, inputs and star_certificates.py are in HEAD.
Reconstruct rational J, root caps/products, global four-cut unit-cost OPT and
exact mandatory vertices. CLOSED certificates are used for every case, without
giving a policy positivity information about future heads. Observed boundary
and zeros are reported separately; zero caps remain UNSUPPORTED, without edits.

Strong lazy control starts by querying BOTH root-proposal endpoints. At each
step its incumbent is the best fully queried edge (original category order
breaks ties). If its real transcript is not a certificate, choose the unknown
competitor with largest cap upper bound (edge ID breaks ties), then query only
its unknown endpoint with largest cap (vertex ID breaks ties). No free winner.

Predeclared necessary development criterion: in at least 2 of the fixed 8 cases,
lazy_calls - global_OPT >= 2 AND 10*lazy_calls >= 11*global_OPT. All 8 must be
complete and supported, otherwise INCONCLUSIVE. FAIL ends V1 without expanding
cases/partitions to rescue it. PASS only justifies considering a native probe:
it establishes neither a gain of that method nor central-theme suitability.
The gaps are upper bounds on possible query savings, not speed measurements.
No policy is tuned on this replay. Partial captures/refusals stay inconclusive.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path

from star_certificates import F, Instance, bounds, certificate, optimal_certificate

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
INPUTS = HERE / "native-inputs-v1.json"


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def lazy(inst, proposal):
    """Acquisitions/stopping use only actual queried values and public caps."""
    queried, order = set(), []

    def acquire(z):
        if z not in queried:
            queried.add(z)
            order.append(z)

    for z in sorted(inst.edges[proposal][:2]):
        acquire(z)
    while True:
        known = [i for i, edge in enumerate(inst.edges) if set(edge[:2]) <= queried]
        incumbent = min(known, key=lambda i: (-sum(inst.edges[i][2:]), inst.priority[i]))
        if certificate(inst, frozenset(queried), incumbent):
            return incumbent, order
        _, upper = bounds(inst, frozenset(queried))
        unknown = [i for i, edge in enumerate(inst.edges) if not set(edge[:2]) <= queried]
        if not unknown:
            raise ValueError("fully queried transcript does not certify an incumbent")
        rival = max(unknown, key=lambda i: (upper[i], -inst.priority[i]))
        acquire(max(set(inst.edges[rival][:2]) - queried, key=lambda z: (inst.caps[z], -z)))


def diagnose(data, case, root, stars):
    na, nb = len(data["a_words"]), len(data["b_words"])
    n, k = na + nb, len(data["edges"])
    caps = tuple(F(*x) for x in root["caps"])
    ra, rb = [F(*x) for x in root["root_a"]], [F(*x) for x in root["root_b"]]
    products = [ra[a] * rb[b - na] for a, b in data["edges"]]
    proposal = max(range(k), key=lambda e: (products[e], -e))
    if (
        root["row"] != data["cases"][case]["row"]
        or caps != tuple(x / 2 for x in ra + rb)
        or len(caps) != n
        or products != [F(*x) for x in root["root_products"]]
        or root["proposal"] != proposal
        or set(stars) != set(range(n))
        or any(not 0 <= x <= 1 for x in [*ra, *rb])
        or sum(ra) > 1
        or sum(rb) > 1
    ):
        raise ValueError("invalid root probabilities or star coverage")
    for z, star in stars.items():
        incident = {i for i, edge in enumerate(data["edges"]) if z in edge}
        if set(map(int, star["components"])) != incident or star["block"] != (
            "A" if z < na else "B"
        ):
            raise ValueError("invalid incident components/block")
    edges = tuple(
        (a, b, F(*stars[a]["components"][str(i)]), F(*stars[b]["components"][str(i)]))
        for i, (a, b) in enumerate(data["edges"])
    )
    scores = [u + v for _, _, u, v in edges]
    winner = max(range(k), key=lambda e: (scores[e], -e))
    facts = [root, *stars.values()]
    observed = "CLOSED" if any(x["boundary"] == "CLOSED" for x in facts) else "INTERIOR"
    item = data["cases"][case]
    report = {
        "case": case,
        "row": item["row"],
        "all_star_calls": n,
        "all_forward_calls": n + 1,
        "certificate_contract": "CLOSED",
        "observed_boundary": observed,
        "zero_entries_across_captured_heads": sum(sum(x["zero_counts_clean_vocab"]) for x in facts),
        "zero_components": sum(value == 0 for edge in edges for value in edge[2:]),
        "zero_caps": sum(x == 0 for x in caps),
        "minimum_cap": min(caps),
        "root_outside_candidates": 1 - sum(products),
        "J_outside_candidates": 1 - sum(scores),
        "J_winner_score": scores[winner],
        "winner": winner,
        "winner_category": data["categories"][winner],
        "winner_text": data["label_texts"][winner],
        "gold": item["gold"],
        "winner_gold_correct": data["categories"][winner] == item["gold"],
        "winning_score_ties": [i for i, v in enumerate(scores) if v == scores[winner]],
        "proposal": proposal,
        "proposal_category": data["categories"][proposal],
        "proposal_equals_J_winner": proposal == winner,
        "proposal_gold_correct": data["categories"][proposal] == item["gold"],
    }
    try:
        inst = Instance(na, caps, edges, (F(1),) * n, interior=False)
    except ValueError as error:
        return {**report, "status": "UNSUPPORTED", "reason": str(error)}
    if not 0 <= sum(scores) <= 1 or not 0 <= sum(products) <= 1:
        raise ValueError("candidate mass outside [0,1]")
    opt = optimal_certificate(inst)
    if opt is None or not certificate(inst, opt, winner):
        raise ValueError("four-cut reference did not return a valid global certificate")
    found, order = lazy(inst, proposal)
    valid = certificate(inst, frozenset(order), found)
    if not valid or found != winner or len(order) < len(opt):
        raise ValueError("invalid lazy transcript or inconsistent optimum")
    all_vertices = frozenset(range(n))
    mandatory = [z for z in range(n) if not certificate(inst, all_vertices - {z}, winner)]
    cap_test = {
        z
        for i, edge in enumerate(edges)
        if i != winner
        for z in edge[:2]
        if caps[z] >= scores[winner]
    }
    gap = len(order) - len(opt)
    return {
        **report,
        "status": "COMPLETE",
        "global_OPT": len(opt),
        "global_certificate": sorted(opt),
        "mandatory_count": len(mandatory),
        "cap_ge_w_rival_count": len(cap_test),
        "cap_test_not_actually_mandatory": sorted(cap_test - set(mandatory)),
        "lazy_calls": len(order),
        "lazy_order": order,
        "lazy_certificate_valid": valid,
        "savings_upper_bound_from_all_stars": n - len(opt),
        "savings_upper_bound_from_lazy": gap,
        "necessary_development_case": gap >= 2 and 10 * len(order) >= 11 * len(opt),
    }


def run(path):
    names = (Path(__file__).name, "star_certificates.py", INPUTS.name)
    hashes = {name: digest(HERE / name) for name in names}
    for name in names:
        frozen = subprocess.check_output(
            ["git", "show", f"HEAD:{(HERE / name).relative_to(ROOT)}"], cwd=ROOT
        )
        if hashlib.sha256(frozen).hexdigest() != hashes[name]:
            raise ValueError(f"freeze before reading any capture: {name}")
    data = json.loads(INPUTS.read_text())
    rows = [json.loads(line) for line in path.read_text().splitlines() if line.strip()]
    producers = [r for r in rows if r["type"] == "producer"]
    if len(producers) != 1 or producers[0]["hashes"][INPUTS.name] != hashes[INPUTS.name]:
        raise ValueError("capture/input provenance mismatch")
    results = []
    for case in range(8):
        roots = [r for r in rows if r["type"] == "root" and r["case"] == case]
        stars = [r for r in rows if r["type"] == "star" and r["case"] == case]
        complete = any(r["type"] == "case_complete" and r["case"] == case for r in rows)
        if not complete:
            results.append({"case": case, "status": "INCONCLUSIVE", "reason": "partial capture"})
            continue
        if len(roots) != 1 or len({r["vertex"] for r in stars}) != len(stars):
            raise ValueError("duplicate/missing complete-case root or star")
        results.append(diagnose(data, case, roots[0], {r["vertex"]: r for r in stars}))
    terminal = [r for r in rows if r["type"] == "terminal"]
    supported = all(r["status"] == "COMPLETE" for r in results)
    complete = len(terminal) == 1 and terminal[0]["status"] == "COMPLETE"
    passing = sum(r.get("necessary_development_case", False) for r in results)
    return {
        "source_hashes": hashes,
        "capture_sha256": digest(path),
        "cases": results,
        "capture_terminal": terminal,
        "qualifying_cases": passing,
        "development_criterion": ("PASS" if passing >= 2 else "FAIL")
        if supported and complete
        else "INCONCLUSIVE",
        "scope": "necessary development condition only; no method gain or speed evidence",
    }


def main():
    # Trusted local rational data; sums may exceed Python's 4300-digit default.
    # Integer arithmetic, serialization and output size remain paid costs.
    sys.set_int_max_str_digits(0)
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("capture", type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    with args.output.open("x") as stream:
        try:
            result = run(args.capture)
        except Exception as error:
            json.dump({"status": "ERROR", "reason": repr(error)}, stream)
            raise
        json.dump(result, stream, indent=2, default=lambda x: [x.numerator, x.denominator])
        stream.write("\n")


if __name__ == "__main__":
    main()
