# Additional prior found DURING V5 capture, not before its freeze

2026-10-16, around17:40UTC. This note does not change the frozen protocol.

[GRAS2608.26585v1](https://arxiv.org/html/2608.26585v1), Section3.1/Algorithms1--2,
already reduces reveal-gradient noise without extra denoiser calls using
conditional Gumbel averages for a straight-through surrogate, or RLOO for
non-differentiable rewards. Our discrete exact visible-action score has another
contract; neither Rao--Blackwellization nor avoiding another neural call is
novel. RLOO was ALREADY included before our capture. No claim that a
straight-through surrogate is an unbiased discrete-reward gradient is adopted.

[Liu et al.2019](https://proceedings.mlr.press/v97/liu19c/liu19c.pdf), Section3
as returned by the primary PDF search excerpt, gives partial enumeration,
conditional-variance bounds and comparison to minibatching. Those general
benefits are prior. The rest of that PDF was not read here; no whole-paper
audit or priority conclusion is asserted.
