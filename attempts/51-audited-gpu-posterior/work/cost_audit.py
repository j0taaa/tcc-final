"""Negative-only necessary condition; unknown errors never become latency evidence."""

from statistics import median

METHODS = ("ticket_scalar", "interval_exact")


def audit(rows, cases, protocol):
    expected = {
        (case, rep, method)
        for case in cases
        for rep in range(protocol["repetitions"])
        for method in METHODS
    }
    index = {}
    for row in rows:
        key = (row["case"], row["rep"], row["method"])
        if key not in expected or key in index:
            raise ValueError("unexpected/duplicate cost record")
        index[key] = row
    if set(index) != expected:
        raise ValueError("negative-only audit requires ALL90 expected records")
    rejected, possible = {}, []
    for case in cases:
        pairs = []
        for rep in range(protocol["repetitions"]):
            a, b = (index[case, rep, m]["warm"] for m in METHODS)
            if not all(r.get("status") == "complete" and r.get("correctness") for r in (a, b)):
                pairs = []
                break
            pairs.append(
                {clock: a["projected"][clock] / b["projected"][clock] for clock in ("wall", "cpu")}
            )
        if not pairs:
            possible.append(case)
            continue
        med = {clock: median(p[clock] for p in pairs) for clock in ("wall", "cpu")}
        if any(med[c] > protocol["primary_gate"][c + "_ratio"] for c in med) or any(
            p[c] >= 1 for p in pairs for c in med
        ):
            rejected[case] = dict(
                median_ratios=med, all_paired_ratios=pairs, completed_control="interval_exact"
            )
        else:
            possible.append(case)
    return dict(
        negative_gate_proved=len(possible) < protocol["primary_gate"]["minimum_states"],
        possible_states=possible,
        rejected_states=rejected,
        remaining_methods_required=len(possible) >= protocol["primary_gate"]["minimum_states"],
        positive_result_permitted=False,
        new_model_forwards=0,
        goal_met=False,
    )
