"""Classical FP64 joint(T,action) readout; not native exact coupling ratios."""

import numpy as np

from .numeric_json import TAIL, NumericJSON


class NumericSuffix(NumericJSON):
    def __post_init__(self):
        if not 0 <= self.eos < len(self.emissions) or self.eos != self.pad:
            raise ValueError("explicit first EOS=PAD grammar required")

    def step(self, state, token):
        return TAIL if state == TAIL else super().step(10 if state == 0 else state, token)


def readout(planner, action, length):
    n, plan = planner.n, planner.plan
    positions = [i for i, _ in action]
    if not action or positions != sorted(set(positions)):
        raise ValueError("sorted nonempty observed action required")
    minimum = max((*planner.fixed, *positions), default=-1)
    if type(length) is not int or not minimum < length <= n:
        return None
    fixed_stops = [i + 1 for i, v in planner.fixed.items() if v == plan.language.eos]
    if fixed_stops and fixed_stops != [length]:
        return None
    factors, terms = planner.u.copy(), np.zeros(n)
    for i, v in action:
        if not planner.active[i]:
            raise ValueError("action retains an already fixed position")
        factors[i] = 0
        factors[i, plan.mapping[v]] = planner.weights[i, v] * planner.gates[i, v]
        terms[i] = 1 / planner.gates[i, v]
    rho = terms / terms.sum()
    matrices = np.einsum("nc,cst->nst", factors, plan.lexical_routes, optimize=True)
    scale = np.zeros(n)
    if not planner.counts[length - 1] > 0:
        return None
    scale[length - 1] = 1 / planner.counts[length - 1]
    matrices[:, 20, TAIL] *= scale
    matrices[:, TAIL, TAIL] = 1
    reachable = np.zeros(len(matrices[0]), dtype=bool)
    reachable[0] = True
    for matrix in matrices:
        reachable = (reachable[:, None] & (matrix > 0)).any(0)
    if not reachable[TAIL]:
        return None  # structural zero, not a fabricated tiny positive mass
    logq, alpha = plan.forwards(matrices)
    beta = plan.backwards(matrices)
    denominator = np.einsum("ns,nst,nt->n", alpha[:-1], matrices, beta[1:], optimize=True)
    coefficient = np.einsum(
        "ns,cst,nt->nc", alpha[:-1], plan.lexical_routes, beta[1:], optimize=True
    )
    coefficient[:, plan.eos_class] *= scale
    aa = np.sum(coefficient * planner.da, axis=1) / denominator
    bb = np.sum(coefficient * planner.db, axis=1) / denominator
    for i, v in action:
        aa[i] = (1 - rho[i]) * (1 - planner.gates[i, v])
        bb[i] = aa[i] * planner.logc[i, v]
    result = {
        "log_probability": float(logq - planner.base["logz"] + np.log(terms.sum())),
        "alpha": aa,
        "beta": float(bb.sum()),
        "anchor": rho - planner.pi[length - 1],
    }
    if not all(np.isfinite(v).all() for v in result.values()):
        raise ValueError("nonfinite numerical joint-length readout")
    return result
