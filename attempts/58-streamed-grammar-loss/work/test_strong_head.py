"""Literal original-ID full-gradient/tied-layout checks independent of controls."""

import unittest

import torch

from .strong_head import SortedHeadPlan


class StrongHeadTests(unittest.TestCase):
    def test_original_ids_and_tied_full_gradient(self):
        previous = torch.get_num_threads()
        torch.set_num_threads(1)
        self.addCleanup(torch.set_num_threads, previous)
        gen = torch.Generator().manual_seed(58501)
        mapping = (3, 0, 2, 0, 1, 3, 2, 2, 4, 4, 1, 2, 2, 2, 2)
        w0 = torch.randn(len(mapping), 4, dtype=torch.float64, generator=gen)
        b0 = torch.randn(len(mapping), dtype=torch.float64, generator=gen)
        inputs, targets = torch.tensor([1, 3, 5, 9, 2, 1]), torch.tensor([2, 0, 14, 8, 7, 11])
        coef = torch.randn(6, 5, dtype=torch.float64, generator=gen)

        def run(plan):
            w = (w0 if plan is None else w0[plan.perm]).clone().requires_grad_()
            b = (b0 if plan is None else b0[plan.perm]).clone().requires_grad_()
            ids = inputs if plan is None else plan.inv[inputs]
            h = w[ids]  # REAL shared parameter in BOTH input and output branches.
            if plan is None:
                logits = h @ w.T + b
                z = torch.stack(
                    [
                        torch.logsumexp(
                            logits[:, [v for v, c in enumerate(mapping) if c == cls]], 1
                        )
                        for cls in range(5)
                    ],
                    1,
                )
                t = logits.gather(1, targets[:, None]).squeeze(1)
            else:
                z, t = plan(h, w, b, targets)
            loss = (coef * z.sin()).sum() + t.square().sum() / 5
            loss.backward()
            inverse = torch.arange(len(mapping)) if plan is None else plan.inv
            return loss.detach(), z.detach(), t.detach(), w.grad[inverse], b.grad[inverse]

        reference = run(None)
        for backend in ("dense", "checkpoint"):
            for threshold in (0, 1, 8, 32, 128):
                plan = SortedHeadPlan(mapping, threshold=threshold, panel=2, backend=backend)
                if threshold in (0, 32):
                    plan.blocked_classes = frozenset()  # All fixture biases are finite.
                for actual, wanted in zip(run(plan), reference, strict=True):
                    torch.testing.assert_close(actual, wanted, rtol=5e-12, atol=5e-12)

    def test_optimizer_state_commutes_with_permutation(self):
        gen = torch.Generator().manual_seed(58502)
        plan = SortedHeadPlan((2, 0, 2, 1, 0, 3, 3), threshold=1)
        theta, grad, m, v = [
            torch.randn(7, 3, dtype=torch.float64, generator=gen) for _ in range(4)
        ]
        v = v.square() + 0.01

        def update(t, g, mm, vv):
            mm = 0.9 * mm + 0.1 * g
            vv = 0.999 * vv + 0.001 * g.square()
            t = t * 0.999 - 1e-3 * mm / (vv.sqrt() + 1e-8)
            return t, mm, vv

        expected = update(theta, grad, m, v)
        actual = update(*(x[plan.perm] for x in (theta, grad, m, v)))
        for a, b in zip(actual, expected, strict=True):
            torch.testing.assert_close(a[plan.inv], b, rtol=0, atol=0)


if __name__ == "__main__":
    unittest.main()
