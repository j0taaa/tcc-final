"""Classical conditional moment estimators and a pre-state semantic certificate."""

import numpy as np

from .llada_suffix_v10 import PREFIX, parsed_text

BLOCKS = {
    "total": slice(0, 9),
    "gate": slice(0, 5),
    "anchor": slice(5, 8),
    "confidence": slice(8, 9),
}


def select_family(candidates, controls):
    """Frozen positive-only zero-overhead NECESSITY rule, not confirmation."""
    valid = [e for e in candidates if np.isfinite(e["estimate"]) and e["estimate"] > 0]
    if not valid:
        return {"status": "INCONCLUSIVE_NONPOSITIVE_CANDIDATES", "selected": None}
    best = min(
        valid,
        key=lambda e: (
            e["estimate"],
            len(e["query_types"]),
            e["draw_count"],
            e["method"],
            e["baseline"],
            tuple(e["coefficients"]),
        ),
    )
    result = {"selected": best, "candidate_count": len(candidates), "control_count": len(controls)}
    if not controls or any(not np.isfinite(e["estimate"]) or e["estimate"] <= 0 for e in controls):
        return {**result, "status": "INCONCLUSIVE_NONPOSITIVE_CONTROL"}
    minimum = min(e["estimate"] for e in controls)
    ratio = best["estimate"] / minimum
    return {
        **result,
        "best_control_estimate": minimum,
        "ratio_to_best_control": ratio,
        "status": "ZERO_OVERHEAD_NECESSITY_PASS" if ratio <= 0.8 else "NECESSITY_NEGATIVE",
    }


def certified_fixed_answer(language, fixed):
    """Requires a viable old state. Incomplete prefixes give no certificate.

    Valid numeric-JSON continuations after a complete fixed object are whitespace/
    epsilon/EOS only. Resource failures are outside this ideal semantic claim.
    """
    pieces, i = [], 0
    while i in fixed:
        v = fixed[i]
        if v == language.eos:
            break
        pieces.append(language.emissions[v])
        i += 1
    try:
        text = (PREFIX + b"".join(pieces)).decode("utf8")
        parsed_text(text)
    except (ValueError, UnicodeError):
        return False, None
    return True, text


def paired_conditional_trace(
    iid_first, iid_second, stratified_first, stratified_second, batch_size=8
):
    a, b, x, y = (
        np.asarray(v, dtype=np.float64)
        for v in (iid_first, iid_second, stratified_first, stratified_second)
    )
    if a.shape != b.shape or a.ndim != 2 or a.shape[1] != 9 or len(a) < 2 or len(a) % 2:
        raise ValueError("even independent iid replica arrays with nine coordinates required")
    if x.shape != y.shape or x.ndim != 2 or x.shape[1] != 9 or len(x) < 2:
        raise ValueError("independent stratified BATCH MEANS required")
    if (
        type(batch_size) is not int
        or batch_size < 1
        or not all(np.isfinite(v).all() for v in (a, b, x, y))
    ):
        raise ValueError("finite moments and positive batch size required")
    half = len(a) // 2
    cross = 0.5 * (a[:half].mean(0) - b[:half].mean(0)) * (a[half:].mean(0) - b[half:].mean(0))
    hidden_iid = 0.5 * (a.var(0, ddof=1) + b.var(0, ddof=1))
    hidden_stratified = 0.5 * (x.var(0, ddof=1) + y.var(0, ddof=1))
    all_pair_gap = 0.5 * (a.mean(0) - b.mean(0)) ** 2 - hidden_iid / len(a)
    result = {}
    for block, indices in BLOCKS.items():
        d, w, s = (float(v[indices].sum()) for v in (cross, hidden_iid, hidden_stratified))
        u = float(all_pair_gap[indices].sum())
        result[block] = {
            "mean_gap_cross_estimate": d,
            "mean_gap_u_estimate": u,
            "hidden_iid1": w,
            "hidden_stratified_batch": s,
            "iid1": u + w,
            "iid_batch": u + w / batch_size,
            "stratified_batch": u + s,
            "cross_half_iid1": d + w,
            "cross_half_stratified_batch": d + s,
        }
    return result
