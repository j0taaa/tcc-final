"""Predeclared necessary-condition audit: negative conclusion only on partial methods."""

from statistics import median

FIRST_METHODS = (
    "handoff_cpu",
    "closed_cpu",
    "exact_stack_cpu",
    "sparse_fa_fp32",
    "sparse_fa_fp64",
    "layered_fa_fp32",
    "layered_fa_fp64",
)


def audit(rows, cases, protocol):
    indexed = {(r["case"], r["repetition"], r["method"]): r for r in rows}
    if len(indexed) != len(rows):
        raise ValueError("duplicate development records")
    expected = {
        (case, rep, method)
        for case in cases
        for rep in range(protocol["repetitions"])
        for method in FIRST_METHODS
    }
    if set(indexed) != expected:
        raise ValueError("partial FIRST stage cannot support a futility decision")
    possible, rejected = {}, {}
    for candidate in protocol["candidate_family"]:
        possible[candidate], rejected[candidate] = [], {}
        for case in cases:
            cold = [indexed[case, rep, candidate]["cold"] for rep in range(protocol["repetitions"])]
            candidates = [
                indexed[case, rep, candidate]["warm"] for rep in range(protocol["repetitions"])
            ]
            if any(r["status"] != "complete" or not r.get("correctness_gate") for r in cold) or any(
                r["status"] != "complete" or not r.get("correctness_gate") for r in candidates
            ):
                rejected[candidate][case] = dict(
                    reason="candidate did not complete correctly in every repetition"
                )
                continue
            witnesses = {}
            for control in FIRST_METHODS[2:]:
                controls = [
                    indexed[case, rep, control]["warm"] for rep in range(protocol["repetitions"])
                ]
                if any(
                    r["status"] != "complete" or not r.get("correctness_gate") for r in controls
                ):
                    continue
                ratios = {
                    metric: [
                        a["projected"][metric] / b["projected"][metric]
                        for a, b in zip(candidates, controls, strict=True)
                    ]
                    for metric in ("wall", "cpu")
                }
                passed = all(
                    median(values) <= 0.8 and max(values) < 1 for values in ratios.values()
                )
                if not passed:
                    witnesses[control] = dict(
                        ratios=ratios, median_ratios={k: median(v) for k, v in ratios.items()}
                    )
            if witnesses:
                rejected[candidate][case] = dict(
                    reason="failed a necessary comparison", controls=witnesses
                )
            else:
                possible[candidate].append(case)
    futile = all(len(remaining) < 3 for remaining in possible.values())
    return dict(
        first_stage_complete=True,
        records=len(rows),
        expected_records=len(expected),
        possible_states=possible,
        rejected_states=rejected,
        negative_gate_proved=futile,
        remaining_methods_required=not futile,
        positive_gate_claim=False,
        new_model_forwards=0,
        user_scientific_goal_met=False,
    )
