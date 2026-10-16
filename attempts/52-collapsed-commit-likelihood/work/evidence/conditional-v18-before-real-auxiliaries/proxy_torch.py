"""Optional independent log-space/autodiff check, not an optimized control."""

import numpy as np


def torch_control(proxy, weights, fixed, feature, action, logbase, base_statistics):
    t, n = proxy.torch, len(weights)
    zero = {"alpha": np.zeros(n), "beta": 0.0, "anchor": np.zeros(n)}
    logprior = proxy.partition(weights, max(fixed, default=-1))
    if bool(t.isneginf(logprior)):
        return {
            "status": "STRUCTURAL_ZERO_PRIOR",
            "posterior": 0.0,
            "log_prior": None,
            "correction": zero,
        }
    if not bool(t.isfinite(logprior)):
        raise ValueError("nonfinite positive Torch proxy mass")
    active = t.as_tensor([i not in fixed for i in range(n)], device=weights.device)
    positions = t.as_tensor([i for i, _ in action], device=weights.device)
    tokens = t.as_tensor([v for _, v in action], device=weights.device)
    logc = t.zeros_like(weights)
    logc[active] = weights[active].log()
    gates = t.sigmoid(feature + logc - np.log(0.01))
    selected = t.zeros(n, dtype=t.bool, device=weights.device)
    selected[positions] = True
    singletons = t.zeros_like(weights, dtype=t.bool)
    singletons[positions, tokens] = True
    filtered = weights * t.where(
        active[:, None],
        t.where(selected[:, None], gates * singletons, 1 - gates),
        t.ones_like(weights),
    )
    if not bool((filtered[active & ~selected] > 0).all()) or not bool(
        (filtered[positions, tokens] > 0).all()
    ):
        raise ValueError("positive original Torch proxy factor underflow")
    counts = t.cumsum(active, dim=0).to(weights.dtype)
    factor = t.where(counts > 0, 1 / counts.clamp_min(1), t.zeros_like(counts))
    logevent = proxy.partition(filtered, max((*fixed, *[i for i, _ in action]), default=-1), factor)
    prior = float((logprior - logbase).detach().cpu())
    if bool(t.isneginf(logevent)):
        return {
            "status": "STRUCTURAL_ZERO_ACTION",
            "posterior": 0.0,
            "log_prior": prior,
            "correction": zero,
        }
    if not bool(t.isfinite(logevent)):
        raise ValueError("nonfinite positive Torch proxy action mass")
    score = proxy.statistics(weights, fixed, feature, action)
    logz = prior + score["log_probability"] - base_statistics["log_probability"]
    z = float(np.exp(logz))
    if not 0 < z <= 1 + 1e-7 or not np.isfinite(z):
        raise ValueError("positive Torch proxy posterior underflow/subset failure")
    return {
        "status": "POSITIVE",
        "posterior": z,
        "log_prior": prior,
        "log_posterior": float(logz),
        "correction": {k: z * score[k] for k in zero},
    }
