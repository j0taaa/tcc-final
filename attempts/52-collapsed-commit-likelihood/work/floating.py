"""Classical grouped-DFA NumPy reference and optional log-semiring Torch adapter.

Finite floating approximation, NOT an exact native-RNG sampler certificate.
"""

import numpy as np

from .numeric_json import STATE_COUNT, TAIL


class FloatPlan:
    def __init__(self, language):
        self.language = language
        effects, members, mapping = language.classes()
        self.effects = np.asarray(effects, dtype=np.int64)
        self.members = tuple(np.asarray(m, dtype=np.int64) for m in members)
        self.mapping = np.asarray(mapping, dtype=np.int64)
        self.class_count = len(members)
        self.routes = np.zeros((self.class_count, STATE_COUNT, STATE_COUNT), dtype=np.float64)
        for c, effect in enumerate(effects):
            for s, target in enumerate(effect):
                if target >= 0:
                    self.routes[c, s, target] = 1

    def class_sums(self, weights):
        return np.stack(
            [np.bincount(self.mapping, weights=row, minlength=self.class_count) for row in weights]
        )

    def matrices(self, weights):
        a = self.class_sums(weights)
        return np.einsum("nc,cst->nst", a, self.routes, optimize=True), a

    @staticmethod
    def forwards(matrices):
        alpha = np.zeros(STATE_COUNT)
        alpha[0] = 1
        history, logscale = [alpha.copy()], 0.0
        for matrix in matrices:
            alpha = alpha @ matrix
            scale = alpha.max()
            if not scale > 0 or not np.isfinite(scale):
                raise ValueError("nonpositive/nonfinite CPU forward scale")
            logscale += np.log(scale)
            alpha /= scale
            history.append(alpha.copy())
        if not alpha[TAIL] > 0:
            raise ValueError("zero/underflow accepting CPU mass")
        return np.log(alpha[TAIL]) + logscale, np.asarray(history)

    @staticmethod
    def backwards(matrices):
        beta = np.zeros(STATE_COUNT)
        beta[TAIL] = 1
        history = [beta.copy()]
        for matrix in reversed(matrices):
            beta = matrix @ beta
            scale = beta.max()
            if not scale > 0 or not np.isfinite(scale):
                raise ValueError("nonpositive/nonfinite CPU suffix scale")
            beta /= scale
            history.append(beta.copy())
        return np.asarray(history[::-1])

    def posterior(self, weights):
        matrices, masses = self.matrices(weights)
        logz, alpha = self.forwards(matrices)
        beta = self.backwards(matrices)
        rows = []
        for i, row in enumerate(weights):
            coefficient = np.einsum("s,cst,t->c", alpha[i], self.routes, beta[i + 1], optimize=True)
            denominator = np.dot(masses[i], coefficient)
            rows.append(row * coefficient[self.mapping] / denominator)
        return logz, np.stack(rows)

    def sample(self, weights, rng):
        matrices, masses = self.matrices(weights)
        beta = self.backwards(matrices)
        state, word = 0, []
        for i, row in enumerate(weights):
            targets = self.effects[:, state]
            valid = np.flatnonzero(targets >= 0)
            probabilities = masses[i, valid] * beta[i + 1, targets[valid]]
            probabilities /= probabilities.sum()
            c = int(rng.choice(valid, p=probabilities))
            members = self.members[c]
            p = row[members] / row[members].sum()
            token = int(rng.choice(members, p=p))
            word.append(token)
            state = int(targets[c])
        if state != TAIL:
            raise AssertionError("floating sampler failed its accepting suffix")
        return tuple(word)

    def action_statistics(self, weights, action, threshold=0.01):
        """Initial uniform-anchor, alpha=0/beta=1 V4 readout, CPU control."""
        confidence = weights / weights.sum(axis=1, keepdims=True)
        gates = confidence / (confidence + threshold)
        n = len(weights)
        pi = np.full(n, 1 / n)
        filtered = weights * (1 - gates)
        retained = dict(action)
        terms = np.zeros(n)
        for i, v in action:
            filtered[i] = 0
            filtered[i, v] = weights[i, v] * gates[i, v]
            terms[i] = pi[i] / gates[i, v]
        scalar = terms.sum()
        rho = terms / scalar
        logbase, _ = self.forwards(self.matrices(weights)[0])
        logevent, posterior = self.posterior(filtered)
        keep = np.asarray([i in retained for i in range(n)], dtype=np.float64)
        gate_score = posterior * (1 - rho[:, None]) * (keep[:, None] - gates)
        return {
            "log_probability": logevent - logbase + np.log(scalar),
            "alpha": gate_score.sum(axis=1),
            "beta": np.sum(gate_score * np.log(confidence)),
            "anchor": rho - pi,
        }


class TorchPlan:
    def __init__(self, plan, device="cuda"):
        import torch

        self.torch, self.plan = torch, plan
        self.mapping = torch.as_tensor(plan.mapping, device=device)
        self.routes = torch.as_tensor(plan.routes, device=device)

    def _safe_log(self, values):
        t = self.torch
        positive = values > 0
        return t.where(positive, values, t.ones_like(values)).log().masked_fill(~positive, -t.inf)

    def _log_product(self, left, right):
        t = self.torch
        values = left[:, :, :, None] + right[:, None, :, :]
        possible = t.isfinite(values).any(dim=2)
        # Avoid undefined derivatives of logsumexp(-inf,...,-inf), INCLUDING
        # on impossible subpaths that never influence the accepting result.
        safe = t.where(possible[:, :, None, :], values, t.zeros_like(values))
        return t.logsumexp(safe, dim=2).masked_fill(~possible, -t.inf)

    def log_partition(self, weights):
        t = self.torch
        masses = t.zeros(
            (len(weights), self.plan.class_count), dtype=weights.dtype, device=weights.device
        ).scatter_add(1, self.mapping[None].expand(len(weights), -1), weights)
        matrices = self._safe_log(t.einsum("nc,cst->nst", masses, self.routes))
        while len(matrices) > 1:
            pairs = len(matrices) // 2
            products = self._log_product(matrices[: 2 * pairs : 2], matrices[1 : 2 * pairs : 2])
            matrices = t.cat((products, matrices[-1:]), dim=0) if len(matrices) % 2 else products
        return matrices[0, 0, TAIL]

    def action_statistics(self, weights, action, threshold=0.01):
        """Autodiff wrt planner alpha, beta and anchor logits; model is frozen."""
        t, n = self.torch, len(weights)
        if weights.ndim != 2 or weights.shape[1] != len(self.mapping) or n < 1:
            raise ValueError("nonempty original-V weight matrix required")
        if (
            weights.dtype != t.float64
            or not bool(t.isfinite(weights).all())
            or not bool((weights > 0).all())
        ):
            raise ValueError("finite positive float64 original weights required")
        positions_list = [i for i, _ in action]
        if not action or positions_list != sorted(set(positions_list)):
            raise ValueError("sorted distinct nonempty observed action required")
        if any(not 0 <= i < n or not 0 <= v < weights.shape[1] for i, v in action):
            raise ValueError("observed action outside the original-ID canvas")
        confidence = weights / weights.sum(dim=1, keepdim=True)
        if not bool((confidence > 0).all()):
            raise ValueError("positive original model probabilities required in V4")
        alpha = t.zeros(n, dtype=weights.dtype, device=weights.device, requires_grad=True)
        beta = t.ones((), dtype=weights.dtype, device=weights.device, requires_grad=True)
        r = t.zeros(n, dtype=weights.dtype, device=weights.device, requires_grad=True)
        h = alpha[:, None] + beta * confidence.log() - np.log(threshold)
        gates = t.sigmoid(h)
        if not bool(((gates > 0) & (gates < 1)).all()):
            raise ValueError("rounded gate outside the smooth policy domain")
        keep = t.zeros_like(weights, dtype=t.bool)
        selected_rows = t.zeros(n, dtype=t.bool, device=weights.device)
        positions = t.as_tensor([i for i, _ in action], device=weights.device)
        tokens = t.as_tensor([v for _, v in action], device=weights.device)
        keep[positions, tokens] = True
        selected_rows[positions] = True
        filtered = weights * t.where(selected_rows[:, None], gates * keep, 1 - gates)
        if not bool((filtered[~selected_rows] > 0).all()) or not bool(
            (filtered[positions, tokens] > 0).all()
        ):
            raise ValueError("positive original target factor underflow")
        log_scalar = t.logsumexp(
            t.log_softmax(r, dim=0)[positions] - gates[positions, tokens].log(), dim=0
        )
        logp = self.log_partition(filtered) - self.log_partition(weights) + log_scalar
        if not bool(t.isfinite(logp)) or float(logp.detach()) > 1e-7:
            raise ValueError("nonfinite/out-of-range floating action log probability")
        gradients = t.autograd.grad(logp, (alpha, beta, r))
        result = {"log_probability": float(logp.detach().cpu())}
        for name, value in zip(("alpha", "beta", "anchor"), gradients, strict=True):
            result[name] = value.detach().cpu().numpy()
        return result
