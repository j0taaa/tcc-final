# V8 — Conditional-mean contract for the combined path control

2026-10-16, written after the V8 runner freeze, before its pretrained calls.
This is a classical conditional-expectation clarification, not a new theorem,
an implementation change or authorization for training/competitive timings.
V7 correctly warns that mixing unbiased coordinate blocks does not BY ITSELF
prove a covariance order. The stronger property below does prove that order
for the particular declared controls with a COMMON baseline.

## Finite path and sufficient visible state

At state s, let q_theta(z,a|s) be the declared joint law of auxiliary proposal,
anchor and visible original-ID release a. Its marginal is

    K_theta(a|s) = sum_z q_theta(z,a|s).

State transitions and any future neural kernel must depend on these draws
ONLY through s and a. The V8 explicit fixed-ID canvas and fixed exogenous
root feature obey this requirement. Hidden proposal length/IDs and anchor
are not passed to the next head. Assume differentiability and square
integrability at the point considered. This is the ideal declared law;
finite-precision/RNG approximations are not certified by the identity.
For the implemented floating controls, theta contains only policy offsets,
the confidence slope and anchor logits; head/root features are frozen. This
note does not assert a software implementation of full neural-weight training.

Given a complete visible path O=(s_0,a_0,...,s_m), its latent posterior factors
into q_theta(z_t,a_t|s_t)/K_theta(a_t|s_t). Therefore Fisher's standard
conditional-score identity gives

    E[grad log q_theta(Z_t,a_t|s_t) | O]
        = grad log K_theta(a_t|s_t).

The statement includes stopped paths, by adding an absorbing transition of
probability1 after termination up to the fixed finite horizon. It does not
condition only on successful resource-managed paths.

## Why the specific combined control qualifies

For each coordinate j, the class-integrated control is a conditional mean
of the full score given the visible action and the full proposal class path.
The length-integrated anchor block is a conditional mean given the visible
action (and fixed state); its actual readout uses the action's posterior of T.
Both conditioning fields include the visible action. Applying the tower
property separately to each coordinate proves the VECTOR identity

    E[C_t | s_t,a_t] = grad log K_theta(a_t|s_t).

Using different intermediate conditioning fields for the blocks does not
invalidate this vector identity. The same reasoning applies to full-triple,
anchor-only, class-only, length-only and known-anchor controls defined in V7.
Mere unconditional unbiasedness would have been insufficient. This does not
establish any ordering BETWEEN the different partial controls.

## Common reward/baseline covariance

Let R be a function of the visible path and, optionally, external reward
randomness conditionally independent of its discarded auxiliaries. Let
b_t(s_t;D) use independent fit data D, and use the SAME b_t for both methods.
Conditional on D, define

    G_C = sum_t (R-b_t(s_t;D)) C_t,
    G_K = sum_t (R-b_t(s_t;D)) grad log K_theta(a_t|s_t).

The path factorization and tower property prove E[G_C|O,D]=G_K. Consequently

    Cov(G_C|D) - Cov(G_K|D) = E[Cov(G_C|O,D)|D] >= 0.

This establishes a Loewner order for THIS common-baseline comparison, even
for the coordinate-combined partial control. It is a standard RB consequence,
not adequate scientific originality or a cost/semantic improvement.

Separately fitted finite-pilot baselines need their own measured comparison;
this identity does not order arbitrary choices of them. A resource refusal,
timeout or censored-success set cannot be dropped to claim unbiasedness.
Rewards using actual hidden proposal work or wall-clock noise need additional
conditions and are not automatically visible-path measurable. Counting NFEs
from the visible stopped path is different from using such hidden costs.
Full measured runtime remains necessary for an efficiency comparison, and
supervised/behavioral policies have different laws outside this ordering.
