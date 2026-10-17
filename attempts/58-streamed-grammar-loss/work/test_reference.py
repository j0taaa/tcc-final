"""Independent scalar dual arithmetic and dense full-head autodiff audits."""

import itertools
import json
import unittest
from dataclasses import dataclass
from fractions import Fraction as F
from functools import lru_cache
from math import prod

from .reference import CLASSES, EMISSIONS, EOS, MAPPING, gradients, transition


@lru_cache(None)
def accepted(n, fixed_tuple):
    out, fixed = [], dict(fixed_tuple)
    for size in range(1, n + 1):
        for body in itertools.product(range(EOS), repeat=size - 1):
            word = (*body, EOS)
            if any(i >= size or word[i] != v for i, v in fixed.items()):
                continue
            try:
                obj = json.loads("".join(EMISSIONS[v] for v in body))
            except ValueError:
                continue
            while isinstance(obj, list) and len(obj) == 1:
                obj = obj[0]
            if type(obj) is int and obj in (0, 1):
                out.append(word)
    return tuple(out)


@dataclass(frozen=True)
class Dual:
    value: F
    derivative: F = F()

    def __add__(self, other):
        other = other if isinstance(other, Dual) else Dual(F(other))
        return Dual(self.value + other.value, self.derivative + other.derivative)

    __radd__ = __add__

    def __mul__(self, other):
        other = other if isinstance(other, Dual) else Dual(F(other))
        return Dual(
            self.value * other.value, self.derivative * other.value + self.value * other.derivative
        )

    __rmul__ = __mul__

    def __truediv__(self, other):
        other = other if isinstance(other, Dual) else Dual(F(other))
        return Dual(
            self.value / other.value,
            (self.derivative * other.value - self.value * other.derivative) / other.value**2,
        )


class GrammarLossTests(unittest.TestCase):
    def test_exact_all_logits_against_independent_dual_enumeration(self):
        checked = 0
        for fixed in ({}, {2: EOS}, {2: 0}):
            n = 4
            raw = tuple(
                tuple(F(1 + (i + 3 * v) % 5) if v != 1 else F() for v in range(7)) for i in range(n)
            )
            words = accepted(n, tuple(sorted(fixed.items())))
            target = words[0]
            targets = (*target, *(0 for _ in range(n - len(target))))
            weights = tuple(
                F(i + 1, 3) if i < len(target) and i not in fixed else F() for i in range(n)
            )
            for lam in (F(), F(1, 2), F(2)):
                result = gradients(raw, fixed, targets, weights, lam)
                for a in range(n):
                    for b in range(7):
                        dual = tuple(
                            tuple(Dual(x, x * (i == a and v == b)) for v, x in enumerate(row))
                            for i, row in enumerate(raw)
                        )
                        p = tuple(tuple(x / sum(row, Dual(F())) for x in row) for row in dual)
                        mass = sum(
                            (
                                prod(
                                    (p[i][v] for i, v in enumerate(word) if i not in fixed),
                                    start=Dual(F(1)),
                                )
                                for word in words
                            ),
                            Dual(F()),
                        )
                        answer = -lam * mass.derivative / mass.value
                        for i, w in enumerate(weights):
                            if w:
                                value = p[i][targets[i]]
                                answer -= w * value.derivative / value.value
                        self.assertEqual(result["gradient"][a][b], answer)
                        checked += 1
                self.assertTrue(all(sum(row, F()) == 0 for row in result["gradient"]))
                self.assertEqual(result["mass"], mass.value)
        print(json.dumps({"exact_logit_derivatives": checked}))

    def test_prefix_occupancy_counterexample_and_refusals(self):
        raw = ((F(1),) * 7,) * 4
        r = gradients(raw, {}, (0, EOS, 0, 0), (F(),) * 4, F(1))
        self.assertTrue(any(0 < a < 1 for a in r["occupancy"]))
        # Wrong replacement a_i=1 breaks the row-shift invariance.
        for i, a in enumerate(r["occupancy"]):
            wrong_sum = 1 - a
            if a < 1:
                self.assertGreater(wrong_sum, 0)
                self.assertEqual(sum(r["gradient"][i], F()), 0)
        for fixed in ({0: 4}, {4: 0}):
            with self.assertRaises(ValueError):
                gradients(raw, fixed, (0,) * 4, (F(),) * 4, F(1))
        zero = ((F(),) * 7,) * 4
        with self.assertRaises(ValueError):
            gradients(zero, {}, (0,) * 4, (F(),) * 4, F(1))

    def test_tiny_global_probability_can_have_large_grammar_gradient(self):
        # A required rare atom class has two original aliases, not a CE target.
        # At two slots, only atom/EOS prefixes are grammatical.
        tiny = F(1, 10**20)
        raw = ((tiny, tiny, F(), F(), F(), F(), F(1)), (F(), F(), F(), F(), F(), F(), F(1)))
        r = gradients(raw, {}, (0, EOS), (F(), F()), F(1))
        self.assertLess(r["p"][0][0], F(1, 4096))
        self.assertLess(r["gradient"][0][0], F(-49, 100))
        self.assertEqual(r["gradient"][0][0], r["gradient"][0][1])
        self.assertEqual(r["gradient"][0][6], -2 * r["gradient"][0][0])

    def test_grouped_head_full_neural_chain_against_dense_autodiff(self):
        import torch

        from .torch_head import grouped_head

        previous_threads = torch.get_num_threads()
        torch.set_num_threads(1)
        self.addCleanup(torch.set_num_threads, previous_threads)
        generator = torch.Generator().manual_seed(5801)
        mapping = (3, 0, 2, 0, 1, 3, 2, 2, 4, 4, 1)
        inputs = (
            torch.randn(7, 5, generator=generator, dtype=torch.float64),
            torch.randn(11, 5, generator=generator, dtype=torch.float64),
            torch.randn(11, generator=generator, dtype=torch.float64),
        )
        targets = torch.tensor([0, 1, 3, 6, 9, 10, 0])
        coefficient = torch.randn(7, 5, generator=generator, dtype=torch.float64)

        def run(panel):
            h, w, b = [x.clone().requires_grad_() for x in inputs]
            if panel is None:
                logits = h @ w.T + b
                z = torch.stack(
                    [
                        torch.logsumexp(
                            logits[:, [v for v, c in enumerate(mapping) if c == cls]], dim=1
                        )
                        for cls in range(5)
                    ],
                    dim=1,
                )
                t = logits.gather(1, targets[:, None]).squeeze(1)
            else:
                z, t = grouped_head(h, w, b, targets, mapping, panel)
            # Actual non-linear downstream composition, not only constant dLSE.
            loss = (coefficient * z.sin()).sum() + (t.square() / 7).sum()
            loss.backward()
            return loss.detach(), z.detach(), t.detach(), *(x.grad for x in (h, w, b))

        expected = run(None)
        maximum = 0.0
        for panel in (1, 2, 4, 16):
            for actual, wanted in zip(run(panel), expected, strict=True):
                maximum = max(maximum, float((actual - wanted).abs().max()))
                torch.testing.assert_close(actual, wanted, atol=3e-12, rtol=3e-12)
        print(
            json.dumps(
                {
                    "CPU_full_head_max_abs_error": maximum,
                    "panel_widths": [1, 2, 4, 16],
                    "neural_model_forwards": 0,
                }
            )
        )

    def test_combined_consumer_against_original_id_dense_enumeration(self):
        import torch

        from .torch_head import grouped_head

        generator = torch.Generator().manual_seed(5802)
        inputs = (
            torch.randn(4, 3, generator=generator, dtype=torch.float64),
            torch.randn(7, 3, generator=generator, dtype=torch.float64),
            torch.randn(7, generator=generator, dtype=torch.float64),
        )
        checks = 0
        for fixed in ({}, {2: EOS}, {2: 0}):
            words = accepted(4, tuple(sorted(fixed.items())))
            target = words[0]
            targets = torch.tensor([*target, *(0 for _ in range(4 - len(target)))])
            weight = torch.tensor(
                [0.0 if i in fixed or i >= len(target) else (i + 1) / 3 for i in range(4)],
                dtype=torch.float64,
            )
            for lam in (0.0, 0.7):
                answers = []
                for dense in (True, False):
                    h, w, b = [x.clone().requires_grad_() for x in inputs]
                    if dense:
                        logits = h @ w.T + b
                        p = logits.softmax(dim=1)
                        mass = sum(
                            prod(
                                (p[i, v] for i, v in enumerate(word) if i not in fixed),
                                start=p.new_ones(()),
                            )
                            for word in words
                        )
                        ce = (
                            weight
                            * (
                                torch.logsumexp(logits, dim=1)
                                - logits.gather(1, targets[:, None]).squeeze(1)
                            )
                        ).sum()
                    else:
                        z, t = grouped_head(h, w, b, targets, MAPPING, panel=2)
                        pi = z.softmax(dim=1)
                        # Differentiable class DP; dense side instead enumerates
                        # independently JSON-validated ORIGINAL ID words above.
                        messages, mass = {(0, False): pi.new_ones(())}, pi.new_zeros(())
                        for i in range(4):
                            nxt = {}
                            for state, val in messages.items():
                                for c, emission in enumerate(CLASSES):
                                    factor = (
                                        pi.new_tensor(float(c == MAPPING[fixed[i]]))
                                        if i in fixed
                                        else pi[i, c]
                                    )
                                    if emission == "<EOS>":
                                        if state == (0, True) and i >= max(fixed, default=-1):
                                            mass = mass + val * factor
                                    else:
                                        dst = transition(state, emission)
                                        if dst is not None:
                                            nxt[dst] = nxt.get(dst, pi.new_zeros(())) + val * factor
                            messages = nxt
                        ce = (weight * (torch.logsumexp(z, dim=1) - t)).sum()
                    loss = ce - lam * mass.log()
                    loss.backward()
                    answers.append((loss.detach(), mass.detach(), *(x.grad for x in (h, w, b))))
                for actual, wanted in zip(*answers, strict=True):
                    torch.testing.assert_close(actual, wanted, rtol=4e-12, atol=4e-12)
                    checks += actual.numel()
        print(json.dumps({"combined_loss_mass_full_gradient_checks": checks}))


if __name__ == "__main__":
    unittest.main()
