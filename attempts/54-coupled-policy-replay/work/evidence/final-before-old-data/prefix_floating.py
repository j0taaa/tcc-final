"""Classical floating stopped-prefix matrices, occupancy and root feature.

No native finite-RNG exactness or new weighted compiler is claimed.
"""

import numpy as np

from .floating import FloatPlan
from .numeric_json import STATE_COUNT, TAIL


def sigmoid(values):
    return np.exp(-np.logaddexp(0, -values))


class PrefixFloatPlan(FloatPlan):
    def __init__(self, language):
        super().__init__(language)
        self.lexical_routes = self.routes.copy()
        self.lexical_routes[:, TAIL, :] = 0
        self.eos_class = int(self.mapping[language.eos])
        expected = np.zeros((STATE_COUNT, STATE_COUNT))
        expected[20, TAIL] = 1
        if not np.array_equal(self.lexical_routes[self.eos_class], expected):
            raise ValueError("the prefix compiler requires a distinct true EOT control class")

    def matrices(self, weights, minimum=-1, eos_factor=None):
        masses = self.class_sums(weights)
        matrices = np.einsum("nc,cst->nst", masses, self.lexical_routes, optimize=True)
        factor = (
            np.ones(len(weights))
            if eos_factor is None
            else np.asarray(eos_factor, dtype=np.float64).copy()
        )
        factor[np.arange(len(weights)) < minimum] = 0
        matrices[:, 20, TAIL] *= factor
        matrices[:, TAIL, TAIL] = 1
        return matrices, masses, factor

    def infer(self, weights, minimum=-1, eos_factor=None):
        matrices, masses, factor = self.matrices(weights, minimum, eos_factor)
        logz, alpha = self.forwards(matrices)
        beta = self.backwards(matrices)
        denominator = np.einsum("ns,nst,nt->n", alpha[:-1], matrices, beta[1:], optimize=True)
        coefficient = np.einsum(
            "ns,cst,nt->nc", alpha[:-1], self.lexical_routes, beta[1:], optimize=True
        )
        coefficient[:, self.eos_class] *= factor
        if not (denominator > 0).all():
            raise ValueError("positive prefix partition required")
        occupied = masses * coefficient / denominator[:, None]
        stops = alpha[:-1, 20] * matrices[:, 20, TAIL] * beta[1:, TAIL] / denominator
        if not np.isfinite(logz) or abs(stops.sum() - 1) > 1e-7:
            raise ValueError("invalid first-EOT occupancy distribution")
        return {
            "logz": logz,
            "coefficient": coefficient,
            "denominator": denominator,
            "classes": occupied,
            "stops": stops,
        }

    def sample_prefix(self, weights, rng, minimum=-1):
        matrices, masses, factor = self.matrices(weights, minimum)
        beta = self.backwards(matrices)
        state, word = 0, []
        for i, row in enumerate(weights):
            targets = self.effects[:, state]
            valid = np.flatnonzero(targets >= 0)
            probabilities = masses[i, valid] * beta[i + 1, targets[valid]]
            probabilities[valid == self.eos_class] *= factor[i]
            if not probabilities.sum() > 0:
                raise ValueError("zero floating prefix sampling mass")
            probabilities /= probabilities.sum()
            cls = int(rng.choice(valid, p=probabilities))
            members = self.members[cls]
            p = row[members] / row[members].sum()
            token = int(rng.choice(members, p=p))
            word.append(token)
            state = int(targets[cls])
            if state == TAIL:
                return tuple(word)
        raise AssertionError("prefix sampler exhausted its accepting horizon")

    def root_feature(self, weights):
        if not np.isfinite(weights).all() or not (weights > 0).all():
            raise ValueError("strict positive full-V root head required")
        if not np.allclose(weights.sum(axis=1), 1, atol=1e-12, rtol=1e-12):
            raise ValueError("normalized original root probabilities required")
        base = self.infer(weights)
        mean = float(np.dot(np.arange(1, len(weights) + 1), base["stops"]))
        if mean <= 1:
            return {
                "alpha": 0.0,
                "target": 1.0,
                "expected": 1.0,
                "mean_prefix": mean,
                "degenerate": True,
                "trials": [],
            }
        target = min(2.0, (1 + mean) / 2)
        factor = 1 - 1 / np.arange(1, len(weights) + 1)
        weighted = self.infer(weights, eos_factor=factor)
        occupancy = (
            weights * weighted["coefficient"][:, self.mapping] / weighted["denominator"][:, None]
        )
        occupancy *= np.exp(weighted["logz"] - base["logz"])
        logc = np.log(weights)
        trials = []

        def count(a):
            value = 1 + float(np.sum(occupancy * sigmoid(a + logc - np.log(0.01))))
            trials.append({"alpha": float(a), "expected": value})
            return value

        lo, hi = -64.0, 64.0
        if not count(lo) < target < count(hi):
            raise ValueError("fixed root-feature bracket failed")
        for _ in range(48):
            middle = (lo + hi) / 2
            if count(middle) < target:
                lo = middle
            else:
                hi = middle
        alpha = (lo + hi) / 2
        expected = count(alpha)
        gates = sigmoid(alpha + logc - np.log(0.01))
        if abs(expected - target) > 1e-8 or not ((gates > 0) & (gates < 1)).all():
            raise ValueError("root feature residual or final smooth gate domain failed")
        return {
            "alpha": alpha,
            "target": target,
            "expected": expected,
            "mean_prefix": mean,
            "degenerate": False,
            "trials": trials,
        }


class PrefixPlanner:
    def __init__(self, plan, weights, fixed, root_feature):
        self.plan, self.weights, self.fixed, self.feature = plan, weights, dict(fixed), root_feature
        self.n = len(weights)
        self.active = np.asarray([i not in self.fixed for i in range(self.n)])
        if weights.shape[1] != len(plan.mapping) or not self.active.any():
            raise ValueError("nonempty active original-V prefix head required")
        if not np.isfinite(weights).all() or not (weights[self.active] > 0).all():
            raise ValueError("finite positive original active probabilities required")
        if not np.allclose(weights.sum(axis=1), 1, atol=1e-12, rtol=1e-12):
            raise ValueError("normalized active/singleton rows required")
        for i, v in self.fixed.items():
            if weights[i, v] != 1 or np.count_nonzero(weights[i]) != 1:
                raise ValueError("fixed rows must be original-ID singletons of weight1")
        self.logc = np.zeros_like(weights)
        self.logc[self.active] = np.log(weights[self.active])
        self.gates = np.full_like(weights, 0.5)
        self.gates[self.active] = sigmoid(root_feature + self.logc[self.active] - np.log(0.01))
        if not ((self.gates[self.active] > 0) & (self.gates[self.active] < 1)).all():
            raise ValueError("active gates outside the smooth domain")
        filtered = weights * np.where(self.active[:, None], 1 - self.gates, 1)
        self.u = plan.class_sums(filtered)
        derivative = -weights * self.gates * (1 - self.gates) * self.active[:, None]
        self.da = plan.class_sums(derivative)
        self.db = plan.class_sums(derivative * self.logc)
        self.counts = np.cumsum(self.active)
        self.pi = np.divide(
            np.tril(np.broadcast_to(self.active, (self.n, self.n))),
            self.counts[:, None],
            out=np.zeros((self.n, self.n)),
            where=self.counts[:, None] > 0,
        )
        self.base = plan.infer(weights, minimum=max(self.fixed, default=-1))

    def statistics(self, action):
        positions = [i for i, _ in action]
        if (
            not action
            or positions != sorted(set(positions))
            or any(
                not 0 <= i < self.n or not self.active[i] or not 0 <= v < self.weights.shape[1]
                for i, v in action
            )
        ):
            raise ValueError("sorted nonempty original active action required")
        factors = self.u.copy()
        terms = np.zeros(self.n)
        for i, v in action:
            factors[i] = 0
            factors[i, self.plan.mapping[v]] = self.weights[i, v] * self.gates[i, v]
            terms[i] = 1 / self.gates[i, v]
        scalar = terms.sum()
        rho = terms / scalar
        # Class factors are already prepared; the inference helper below
        # deliberately avoids expanding them back into original token rows.
        matrices = np.einsum("nc,cst->nst", factors, self.plan.lexical_routes, optimize=True)
        scale = np.divide(1.0, self.counts, out=np.zeros(self.n), where=self.counts > 0)
        minimum = max((*self.fixed, *positions), default=-1)
        scale[np.arange(self.n) < minimum] = 0
        matrices[:, 20, TAIL] *= scale
        matrices[:, TAIL, TAIL] = 1
        logq, alpha = self.plan.forwards(matrices)
        beta = self.plan.backwards(matrices)
        denom = np.einsum("ns,nst,nt->n", alpha[:-1], matrices, beta[1:], optimize=True)
        coef = np.einsum(
            "ns,cst,nt->nc", alpha[:-1], self.plan.lexical_routes, beta[1:], optimize=True
        )
        coef[:, self.plan.eos_class] *= scale
        stops = alpha[:-1, 20] * matrices[:, 20, TAIL] * beta[1:, TAIL] / denom
        aa = np.sum(coef * self.da, axis=1) / denom
        bb = np.sum(coef * self.db, axis=1) / denom
        for i, v in action:
            aa[i] = (1 - rho[i]) * (1 - self.gates[i, v])
            bb[i] = aa[i] * self.logc[i, v]
        result = {
            "log_probability": logq - self.base["logz"] + np.log(scalar),
            "alpha": aa,
            "beta": float(bb.sum()),
            "anchor": rho - stops @ self.pi,
        }
        if not all(np.isfinite(v).all() for v in result.values()) or abs(stops.sum() - 1) > 1e-7:
            raise ValueError("invalid compact prefix likelihood or occupancy")
        return result

    def controls(self, word, anchor, action, collapsed=None):
        if not word or word[-1] != self.plan.language.eos or self.plan.language.eos in word[:-1]:
            raise ValueError("an original first-EOT proposal prefix is required")
        if any(i >= len(word) or word[i] != v for i, v in (*self.fixed.items(), *action)):
            raise ValueError("proposal must preserve the original fixed and retained IDs")
        if (anchor, word[anchor]) not in action or not self.active[anchor]:
            raise ValueError("eligible original anchor must be retained")
        collapsed = self.statistics(action) if collapsed is None else collapsed
        keep = np.asarray([i in dict(action) for i in range(self.n)])
        terms = np.zeros(self.n)
        for i, v in action:
            terms[i] = 1 / self.gates[i, v]
        rho = terms / terms.sum()
        aa = np.zeros(self.n)
        bb = np.zeros(self.n)
        ca = np.zeros(self.n)
        cb = np.zeros(self.n)
        for i, v in enumerate(word):
            if not self.active[i]:
                continue
            aa[i] = float(keep[i]) - self.gates[i, v]
            bb[i] = aa[i] * self.logc[i, v]
            if keep[i]:
                ca[i] = (1 - rho[i]) * aa[i]
                cb[i] = ca[i] * self.logc[i, v]
            else:
                cls = self.plan.mapping[v]
                ca[i] = self.da[i, cls] / self.u[i, cls]
                cb[i] = self.db[i, cls] / self.u[i, cls]
        ra = aa * (1 - rho)
        rb = bb * (1 - rho)
        aa[anchor] = 0
        bb[anchor] = 0
        pi = self.pi[len(word) - 1]
        one = np.eye(self.n)[anchor]
        known_a = collapsed["alpha"].copy()
        known_b = float(collapsed["beta"])
        for i, v in action:
            correction = (rho[i] - (i == anchor)) * (1 - self.gates[i, v])
            known_a[i] += correction
            known_b += correction * self.logc[i, v]

        def score(a, b, r):
            return {"alpha": a, "beta": float(np.sum(b)), "anchor": r}

        return {
            "full_triple": score(aa, bb, one - pi),
            "anchor_integrated": score(ra, rb, rho - pi),
            "class_integrated": score(ca, cb, rho - pi),
            "length_integrated": score(ra, rb, collapsed["anchor"]),
            "combined_partial": score(ca, cb, collapsed["anchor"]),
            "known_anchor": score(known_a, known_b, collapsed["anchor"] + one - rho),
        }
