"""Classical stationary independence-Metropolis control, not an iid sampler.

An original on-policy latent proposal is required. Target-normalizer constants
cancel. The optional conditional average integrates the accept/reject coin;
this is ordinary Rao--Blackwellization, not a claimed new algorithm.
"""

from fractions import Fraction as Q

from resampling import deadline


def proposed_move(sampler, current, rng, end=None):
    deadline(end)
    proposed = sampler.base.sample(rng)
    a = min(Q(1), sampler.acceptance(proposed) / sampler.acceptance(current))
    return proposed, a


def transition(sampler, current, rng, end=None):
    proposed, a = proposed_move(sampler, current, rng, end)
    return proposed if rng.randrange(a.denominator) < a.numerator else current


def conditional_average(original_score, proposed_score, acceptance):
    return tuple(
        (1 - acceptance / 2) * x + acceptance * y / 2
        for x, y in zip(original_score, proposed_score, strict=True)
    )


def audit_transition(sampler, target, proposal):
    """Independently integrate every coin; rational detailed balance."""
    law = {}
    for x in target:
        row = {y: Q() for y in target}
        for y, q in proposal.items():
            a = min(Q(1), sampler.acceptance(y) / sampler.acceptance(x))
            row[y] += q * a
            row[x] += q * (1 - a)
        assert sum(row.values(), Q()) == 1
        law[x] = row
    for y in target:
        assert sum((target[x] * law[x][y] for x in target), Q()) == target[y]
        for x in target:
            assert target[x] * law[x][y] == target[y] * law[y][x]
    return law
