"""Small rational projected proposal control. Standard conditional expectation.

Policy coordinates are independent gate logits and log anchor weights. Head
weights are FROZEN. A caller must prove the proxy language is a subset of the
base language; this small reference does not solve language containment.
"""

from fractions import Fraction as F

from .prefix_anchor import PrefixAnchor


def policy_score(score):
    _, gates, anchor = score
    return tuple(value for row in gates for value in row) + tuple(anchor)


class ProposalControl:
    def __init__(self, base, proxy_language):
        if (proxy_language.emissions, proxy_language.eos) != (
            base.language.emissions,
            base.language.eos,
        ):
            raise ValueError("proxy must preserve every original ID and EOS")
        self.base = base
        self.zero = (F(),) * (base.n * base.v + base.n)
        try:
            self.proxy = PrefixAnchor(
                proxy_language, base.rows, base.gates, base.u, base.fixed
            )
        except ValueError as error:
            if str(error) != "zero compatible prefix mass":
                raise
            self.proxy = None

    def __call__(self, action):
        probability, *_ = self.base.action_statistics(action)
        if not probability:
            raise ValueError("positive visible action required")
        if self.proxy is None:
            return F(), self.zero
        restricted, *score = self.proxy.action_statistics(action)
        if not restricted:
            return F(), self.zero
        posterior = self.proxy.mass / self.base.mass * restricted / probability
        if not 0 <= posterior <= 1:
            raise ValueError("proxy subset/normalization contract violated")
        return posterior, tuple(posterior * value for value in policy_score(score))
