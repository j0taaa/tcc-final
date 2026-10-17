"""Classical right quadratic-reproducing control, not a complete factory."""

from fractions import Fraction as F
from math import isqrt

from coefficients import Coefficients, stencil


class QuasiControl(Coefficients):
    @property
    def c(self):
        return self.lipschitz

    @property
    def initial_degree(self):
        n = 16
        while (
            self.curvature / (8 * (n - 1)) + 17 * self.lipschitz / (15 * n * isqrt(n))
            > self.epsilon
        ):
            n *= 4
        return n

    def coefficient(self, n, k):
        args = stencil(n, k)
        f0, f1, f2 = (F(self.function(x)) for x in args)
        dd = n * (f0 - 2 * f1 + f2)
        center = f0 - args[0] * (1 - args[0]) * dd / (2 * (n - 1))
        delta = self.lipschitz / (n * isqrt(n))
        return center - delta, center + delta, dd

    def mixture_coefficient(self, n, k):
        if not self.lipschitz:
            raise ValueError("H=0 uses its finite polynomial factory")
        return super().mixture_coefficient(n, k)
