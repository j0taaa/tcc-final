"""Classical conditional moment estimators and a pre-state semantic certificate."""

import numpy as np

from .llada_suffix_v10 import PREFIX, parsed_text

BLOCKS = {
    "total": slice(0, 9),
    "gate": slice(0, 5),
    "anchor": slice(5, 8),
    "confidence": slice(8, 9),
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
    result = {}
    for block, indices in BLOCKS.items():
        d, w, s = (float(v[indices].sum()) for v in (cross, hidden_iid, hidden_stratified))
        result[block] = {
            "mean_gap_cross_estimate": d,
            "hidden_iid1": w,
            "hidden_stratified_batch": s,
            "iid1": d + w,
            "iid_batch": d + w / batch_size,
            "stratified_batch": d + s,
        }
    return result
