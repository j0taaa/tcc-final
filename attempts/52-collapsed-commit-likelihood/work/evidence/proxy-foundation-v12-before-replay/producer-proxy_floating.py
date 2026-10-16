"""Floating reference for the classical V11 policy-only projected control."""

import numpy as np

from .numeric_json import STATE_COUNT, TAIL
from .prefix_floating import PrefixPlanner


def accepting_support(matrices):
    """Positive-weight Boolean reachability, separate from floating total mass."""
    if matrices.ndim != 3 or matrices.shape[1:] != (STATE_COUNT, STATE_COUNT):
        raise ValueError("layered DFA matrices required")
    if not np.isfinite(matrices).all() or (matrices < 0).any():
        raise ValueError("finite nonnegative transition weights required")
    possible = np.zeros(STATE_COUNT, dtype=bool)
    possible[0] = True
    for matrix in matrices:
        possible = np.any(possible[:, None] & (matrix > 0), axis=0)
    return bool(possible[TAIL])


class ProxyPlanner:
    def __init__(self, base, proxy_plan):
        if (base.plan.language.emissions, base.plan.language.eos) != (
            proxy_plan.language.emissions,
            proxy_plan.language.eos,
        ):
            raise ValueError("proxy must preserve original IDs/EOS; subset proof is required")
        self.base, self.plan = base, proxy_plan
        self.zero = {"alpha": np.zeros(base.n), "beta": 0.0, "anchor": np.zeros(base.n)}
        self.proxy = None
        self.log_prior = -np.inf
        filtered = base.weights[base.active] * (1 - base.gates[base.active])
        if not (filtered > 0).all():
            raise ValueError("positive original unretained proxy factor underflow")
        matrices = proxy_plan.matrices(base.weights, minimum=max(base.fixed, default=-1))[0]
        if accepting_support(matrices):
            self.proxy = PrefixPlanner(proxy_plan, base.weights, base.fixed, base.feature)
            self.log_prior = self.proxy.base["logz"] - base.base["logz"]
            if not np.isfinite(self.log_prior) or self.log_prior > 1e-7:
                raise ValueError("invalid positive proxy prior/subset contract")

    def statistics(self, action, base_statistics=None):
        observed = self.base.statistics(action) if base_statistics is None else base_statistics
        if self.proxy is None:
            return {
                "status": "STRUCTURAL_ZERO_PRIOR",
                "posterior": 0.0,
                "log_prior": None,
                "correction": self.zero,
            }
        p = self.proxy
        factors = p.u.copy()
        positions = [i for i, _ in action]
        for i, v in action:
            factors[i] = 0
            factor = p.weights[i, v] * p.gates[i, v]
            if not factor > 0:
                raise ValueError("positive original retained proxy factor underflow")
            factors[i, p.plan.mapping[v]] = factor
        matrices = np.einsum("nc,cst->nst", factors, p.plan.lexical_routes, optimize=True)
        # Positive reciprocal anchor normalizers do not affect support.
        matrices[np.arange(p.n) < max((*p.fixed, *positions), default=-1), 20, TAIL] = 0
        matrices[p.counts == 0, 20, TAIL] = 0
        matrices[:, TAIL, TAIL] = 1
        if not accepting_support(matrices):
            return {
                "status": "STRUCTURAL_ZERO_ACTION",
                "posterior": 0.0,
                "log_prior": float(self.log_prior),
                "correction": self.zero,
            }
        restricted = p.statistics(action)
        log_posterior = self.log_prior + restricted["log_probability"] - observed["log_probability"]
        posterior = float(np.exp(log_posterior))
        if not 0 < posterior <= 1 + 1e-7 or not np.isfinite(posterior):
            raise ValueError("positive proxy posterior underflow/subset failure")
        return {
            "status": "POSITIVE",
            "posterior": posterior,
            "log_prior": float(self.log_prior),
            "log_posterior": float(log_posterior),
            "correction": {k: posterior * restricted[k] for k in self.zero},
        }
