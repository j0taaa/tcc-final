# V9 — Position-only fixed-reference limitation, BEFORE its oracle

2026-10-16. Classical variational factorization, not a new impossibility.
The first four small V9 oracles pass, without neural work. This addendum is
written before extending them to this important counter-control.

Consider the fixed-length subcase, frozen denoiser and position-only mask law
M_phi(B|s) independent of the proposed tokens. Its transition factorizes as

    K_phi(B,y_B|s) = M_phi(B|s) P_s(X_B=y_B).

The fixed-reference bound therefore has phi-dependent part ONLY
E_R sum_t log M_phi(B_t|s_t). If M can represent the reference mask law R,
its unrestricted optimum at each reference state is M=R, regardless of
the denoiser's error pattern. At that point its expected bound gradient is0.
This is true even if changing the mask order would improve final target
probability, since the true decoder's future head depends on committed IDs.
The reference bound does not automatically teach semantic ordering.

The actual token-dependent/variable-prefix policy can fall outside this
factorization, so this is NOT a proof that all V9 gradients vanish or that
every supervised objective fails. It IS a concrete reason that computability
and an ELBO alone cannot justify a large new training campaign. Adaptive
Order Policies' weighted CE is a competent DIFFERENT objective, not an
incorrect approximation to be defeated just by stating this bound.

The small oracle must exhibit a state-dependent fake denoiser with zero
fixed-reference bound gradient at M=R but nonzero exact final-likelihood
derivative. Preserve that result alongside the correct bound/gradient checks.
No Tiny-A2D rescue, pretrained call or update follows. Until an own useful
consequence is supported, V9 is only a candidate supervised CONTROL, not an
established replacement for the reward-gradient application or a protagonist.
