"""Classical class-sum derivative preparation; floating V3 planner only.

No token-weight/head gradient is provided and no new compiler is claimed.
"""

import numpy as np


class CompactPlanner:
    def __init__(self, plan, weights):
        self.plan, self.weights = plan, weights
        if weights.ndim != 2 or weights.shape[1] != len(plan.mapping):
            raise ValueError("original-V two-dimensional weights required")
        if not np.isfinite(weights).all() or not (weights > 0).all():
            raise ValueError("finite positive original weights required")
        self.n = len(weights)
        self.confidence = weights / weights.sum(axis=1, keepdims=True)
        self.gates = self.confidence / (self.confidence + 0.01)
        self.logc = np.log(self.confidence)
        self.pi = np.full(self.n, 1 / self.n)
        if not ((self.gates > 0) & (self.gates < 1)).all():
            raise ValueError("gates outside open smooth domain")
        unretained = weights * (1 - self.gates)
        if not (unretained > 0).all():
            raise ValueError("positive unretained factor underflow")
        self.u = plan.class_sums(unretained)
        derivative = -weights * self.gates * (1 - self.gates)
        self.da = plan.class_sums(derivative)
        self.db = plan.class_sums(derivative * self.logc)
        self.base_logz = plan.forwards(plan.matrices(weights)[0])[0]

    def action_terms(self, action):
        positions = [i for i, _ in action]
        if not action or positions != sorted(set(positions)):
            raise ValueError("sorted distinct nonempty action required")
        if any(not 0 <= i < self.n or not 0 <= v < self.weights.shape[1] for i, v in action):
            raise ValueError("action outside original canvas")
        terms = np.zeros(self.n)
        for i, v in action:
            terms[i] = self.pi[i] / self.gates[i, v]
        return terms.sum(), terms / terms.sum()

    def statistics(self, action):
        plan = self.plan
        scalar, rho = self.action_terms(action)
        factors = self.u.copy()
        for i, v in action:
            factors[i] = 0
            factors[i, plan.mapping[v]] = self.weights[i, v] * self.gates[i, v]
        matrices = np.einsum("nc,cst->nst", factors, plan.routes, optimize=True)
        logz, alpha = plan.forwards(matrices)
        beta = plan.backwards(matrices)
        coefficient = np.einsum("ns,cst,nt->nc", alpha[:-1], plan.routes, beta[1:], optimize=True)
        denominator = np.sum(factors * coefficient, axis=1)
        if not (denominator > 0).all():
            raise ValueError("zero/underflow observed action mass")
        aa = np.sum(coefficient * self.da, axis=1) / denominator
        bb = np.sum(coefficient * self.db, axis=1) / denominator
        for i, v in action:
            aa[i] = (1 - rho[i]) * (1 - self.gates[i, v])
            bb[i] = aa[i] * self.logc[i, v]
        result = {
            "log_probability": logz - self.base_logz + np.log(scalar),
            "alpha": aa,
            "beta": np.sum(bb),
            "anchor": rho - self.pi,
        }
        if not all(np.isfinite(v).all() for v in result.values()):
            raise ValueError("nonfinite compact observed score")
        return result

    def cheap_scores(self, word, anchor, action):
        _, rho = self.action_terms(action)
        retained = dict(action)
        if retained.get(anchor) != word[anchor]:
            raise ValueError("the original anchor ID must be retained")
        selected = np.asarray([i in retained for i in range(self.n)], dtype=np.float64)
        g = self.gates[np.arange(self.n), word]
        logc = self.logc[np.arange(self.n), word]
        aa = selected - g
        reverse = (1 - rho) * aa
        aa[anchor] = 0
        return {
            "full_triple": {
                "alpha": aa,
                "beta": np.dot(aa, logc),
                "anchor": np.eye(self.n)[anchor] - self.pi,
            },
            "anchor_integrated": {
                "alpha": reverse,
                "beta": np.dot(reverse, logc),
                "anchor": rho - self.pi,
            },
        }

    def known_anchor(self, collapsed, anchor, action):
        """Conditional hidden-word law is independent of A given the action."""
        _, rho = self.action_terms(action)
        aa, bb = collapsed["alpha"].copy(), float(collapsed["beta"])
        for i, v in action:
            correction = (rho[i] - (i == anchor)) * (1 - self.gates[i, v])
            aa[i] += correction
            bb += correction * self.logc[i, v]
        return {"alpha": aa, "beta": bb, "anchor": np.eye(self.n)[anchor] - self.pi}


def score_vector(score):
    return np.concatenate(
        (np.asarray(score["alpha"]), [score["beta"]], np.asarray(score["anchor"]))
    )
