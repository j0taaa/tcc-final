"""Small rational conditional-word reference, not a neural/production sampler.

Conditional Monte Carlo and stratified CDF intervals are classical. Enumeration
is intentionally explicit here and is also a stronger exact-mean control.
"""

from fractions import Fraction as F

from .numeric_json import TAIL


def conditional_prefix_law(policy, action):
    if policy.n > 4 or policy.v > 12:
        raise ValueError("conditional enumeration is restricted to the small oracle")
    _, rho = policy._action(action)
    retained = dict(action)
    minimum = max((*policy.fixed, *retained), default=-1)
    law = {}

    def visit(i, state, prefix, weight):
        if i == policy.n:
            return
        tokens = (
            (policy.fixed[i],)
            if i in policy.fixed
            else ((retained[i],) if i in retained else range(policy.v))
        )
        for v in tokens:
            target = policy.language.step(state, v)
            if target < 0:
                continue
            factor = (
                F(1)
                if i in policy.fixed
                else policy.rows[i][v]
                * (policy.gates[i][v] if i in retained else 1 - policy.gates[i][v])
            )
            if not factor:
                continue
            word = (*prefix, v)
            if target == TAIL:
                if i >= minimum and policy.h[i]:
                    law[word] = weight * factor / policy.h[i]
            else:
                visit(i + 1, target, word, weight * factor)

    visit(0, 0, (), F(1))
    mass = sum(law.values(), F())
    if not mass:
        raise ValueError("zero conditional action mass")
    return {word: value / mass for word, value in law.items()}, rho


def stratified_laws(law, count):
    """Conditional law in each uniform CDF stratum; all original words kept."""
    if type(count) is not int or not 1 <= count <= 16:
        raise ValueError("small positive stratum count required")
    if (
        not law
        or any(type(p) is not F or p <= 0 for p in law.values())
        or sum(law.values(), F()) != 1
    ):
        raise ValueError("positive normalized rational law required")
    result = [{} for _ in range(count)]
    start = F()
    for word, mass in sorted(law.items()):
        end = start + mass
        for j, row in enumerate(result):
            overlap = min(end, F(j + 1, count)) - max(start, F(j, count))
            if overlap > 0:
                row[word] = count * overlap
        start = end
    return tuple(result)
