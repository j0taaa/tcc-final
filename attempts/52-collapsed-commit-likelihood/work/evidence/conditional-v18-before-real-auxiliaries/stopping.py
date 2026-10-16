"""CLASSICAL absorbing termination and independent first-EOT length mixture."""

import numpy as np

from .numeric_json import STATE_COUNT, TAIL, NumericJSON


class StoppedNumericJSON(NumericJSON):
    def step(self, state, token):
        return TAIL if state == TAIL else super().step(state, token)


def logsum(values):
    maximum = np.max(values)
    return (
        float(maximum + np.log(np.exp(values - maximum).sum())) if np.isfinite(maximum) else -np.inf
    )


def first_eot_logs(plan, weights):
    """Remove already-stopped flow; independently scale each surviving layer."""
    if weights.ndim != 2 or weights.shape[1] != len(plan.mapping):
        raise ValueError("original-V matrix required")
    if not np.isfinite(weights).all() or (weights < 0).any() or not (weights.sum(axis=1) > 0).all():
        raise ValueError("finite nonnegative rows with positive normalizers required")
    confidence = weights / weights.sum(axis=1, keepdims=True)
    matrices, _ = plan.matrices(confidence)
    alpha = np.zeros(STATE_COUNT)
    alpha[0] = 1
    logs = np.full(len(weights), -np.inf)
    scale = 0.0
    for i, matrix in enumerate(matrices):
        alpha = alpha @ matrix
        if alpha[TAIL] > 0:
            logs[i] = scale + np.log(alpha[TAIL])
        alpha[TAIL] = 0
        maximum = alpha.max()
        if not maximum > 0:
            break
        scale += np.log(maximum)
        alpha /= maximum
    return logs


def length_statistics(logs, pad_probabilities):
    if len(logs) != len(pad_probabilities):
        raise ValueError("one PAD weight per length layer required")
    if (
        not np.isfinite(pad_probabilities).all()
        or ((pad_probabilities < 0) | (pad_probabilities > 1)).any()
    ):
        raise ValueError("original PAD probabilities must be in[0,1]")
    stop_logz = logsum(logs)
    if not np.isfinite(stop_logz):
        raise ValueError("zero or nonfinite stopped mass")
    suffix = np.zeros(len(logs))
    accumulated = 0.0
    for i in range(len(logs) - 1, -1, -1):
        suffix[i] = accumulated
        accumulated += np.log(pad_probabilities[i]) if pad_probabilities[i] > 0 else -np.inf
    pad_logs = logs + suffix
    pad_logz = logsum(pad_logs)
    stop = np.exp(logs - stop_logz)
    lengths = np.arange(1, len(logs) + 1)
    result = {
        "log_z_stop": stop_logz,
        "stop_lengths": stop,
        "mean_stop_length": float(np.dot(lengths, stop)),
        "log_z_pad": pad_logz,
    }
    if not np.isfinite(pad_logz):
        return {
            **result,
            "pad_lengths": None,
            "tv": None,
            "mean_pad_length": None,
            "mean_length_gap": None,
            "pad_target_status": "ZERO_MASS",
        }
    pad = np.exp(pad_logs - pad_logz)
    return {
        **result,
        "pad_lengths": pad,
        "tv": float(np.abs(stop - pad).sum() / 2),
        "mean_pad_length": float(np.dot(lengths, pad)),
        "mean_length_gap": float(np.dot(lengths, pad - stop)),
        "stop_survival": np.cumsum(stop[::-1])[::-1],
        "pad_survival": np.cumsum(pad[::-1])[::-1],
        "pad_target_status": "DEFINED",
    }
