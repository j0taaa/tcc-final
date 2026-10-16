"""Optional independent autodiff for V7 prefix terminal potentials, frozen head."""

import numpy as np

from .floating import TorchPlan
from .numeric_json import STATE_COUNT, TAIL


class PrefixTorch(TorchPlan):
    def __init__(self, plan, device="cuda"):
        super().__init__(plan, device)
        self.routes = self.torch.as_tensor(plan.lexical_routes, device=device)

    def partition(self, weights, minimum, eos_factor=None):
        t, n = self.torch, len(weights)
        masses = t.zeros(
            (n, self.plan.class_count), dtype=weights.dtype, device=weights.device
        ).scatter_add(1, self.mapping[None].expand(n, -1), weights)
        matrices = t.einsum("nc,cst->nst", masses, self.routes)
        terminal = t.nn.functional.one_hot(t.tensor(TAIL, device=weights.device), STATE_COUNT).to(
            weights.dtype
        )
        row = t.arange(STATE_COUNT, device=weights.device) == TAIL
        matrices = t.where(row[None, :, None], terminal[None, None, :], matrices)
        factor = (
            t.ones(n, dtype=weights.dtype, device=weights.device)
            if eos_factor is None
            else eos_factor
        )
        factor = factor * (t.arange(n, device=weights.device) >= minimum)
        multiplier = t.ones_like(matrices)
        multiplier[:, 20, TAIL] = factor
        matrices = self._safe_log(matrices * multiplier)
        while len(matrices) > 1:
            pairs = len(matrices) // 2
            products = self._log_product(matrices[: 2 * pairs : 2], matrices[1 : 2 * pairs : 2])
            matrices = t.cat((products, matrices[-1:]), dim=0) if len(matrices) % 2 else products
        return matrices[0, 0, TAIL]

    def statistics(self, weights, fixed, feature, action):
        t, n = self.torch, len(weights)
        if weights.dtype != t.float64 or weights.ndim != 2 or weights.shape[1] != len(self.mapping):
            raise ValueError("original full-V float64 prefix matrix required")
        active = t.as_tensor([i not in fixed for i in range(n)], device=weights.device)
        if (
            not bool(active.any())
            or not bool((weights[active] > 0).all())
            or not bool(t.isfinite(weights).all())
        ):
            raise ValueError("finite positive original active weights required")
        if not t.allclose(
            weights.sum(dim=1),
            t.ones(n, dtype=weights.dtype, device=weights.device),
            atol=1e-12,
            rtol=1e-12,
        ):
            raise ValueError("normalized active/fixed original rows required")
        positions_list = [i for i, _ in action]
        if (
            not action
            or positions_list != sorted(set(positions_list))
            or any(
                not 0 <= i < n or not bool(active[i]) or not 0 <= v < weights.shape[1]
                for i, v in action
            )
        ):
            raise ValueError("nonempty distinct original active action required")
        for i, v in fixed.items():
            if float(weights[i, v]) != 1 or int(t.count_nonzero(weights[i])) != 1:
                raise ValueError("fixed original ID must have singleton weight1")
        logc = t.zeros_like(weights)
        logc[active] = weights[active].log()
        alpha = t.zeros(n, dtype=weights.dtype, device=weights.device, requires_grad=True)
        beta = t.ones((), dtype=weights.dtype, device=weights.device, requires_grad=True)
        r = t.zeros(n, dtype=weights.dtype, device=weights.device, requires_grad=True)
        gates = t.sigmoid(feature + alpha[:, None] + beta * logc - np.log(0.01))
        if not bool(((gates[active] > 0) & (gates[active] < 1)).all()):
            raise ValueError("active gates outside smooth numeric domain")
        positions = t.as_tensor(positions_list, device=weights.device)
        tokens = t.as_tensor([v for _, v in action], device=weights.device)
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
            raise ValueError("positive original filtered factor underflow")
        cumulative = t.cumsum(r.exp() * active, dim=0)
        positive = cumulative > 0
        factor = t.where(
            positive,
            1 / t.where(positive, cumulative, t.ones_like(cumulative)),
            t.zeros_like(cumulative),
        )
        minimum = max((*fixed, *positions_list), default=-1)
        logq = self.partition(filtered, minimum, factor)
        logbase = self.partition(weights, max(fixed, default=-1))
        logs = t.logsumexp(r[positions] - gates[positions, tokens].log(), dim=0)
        logp = logq - logbase + logs
        if not bool(t.isfinite(logp)) or float(logp.detach()) > 1e-7:
            raise ValueError("nonfinite or out-of-range prefix action probability")
        grads = t.autograd.grad(logp, (alpha, beta, r))
        result = {"log_probability": float(logp.detach().cpu())}
        for name, value in zip(("alpha", "beta", "anchor"), grads, strict=True):
            result[name] = value.detach().cpu().numpy()
        return result
