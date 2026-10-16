# Coupled observed actions and shared-prefix neural work

2026-10-16, BEFORE implementation/real statistics. These are applications of
classical maximal coupling, projection contraction and faithful-chain bounds.
They are not new general theorems. See primary-v1.md for direct antecedents.

## Contracts

Two policies have finite kernels K_0(a|s),K_1(a|s), identical state-update
function s'=T(s,a), finite horizon and deterministic frozen-backbone output
for the SAME exact model inputs/configuration. The full state includes phase,
ordinal, EOS, root features and any rejection/control budget. No grouping of
insufficient states. Policies are fixed independently of the draft sample;
a policy fitted using that very exposed draft requires a different conditional
law and is NOT covered. History-indexed states may be used for non-Markov
policies. Terminal states do not incur another neural forward.

A faithful/co-adapted pair has, conditional on its COMPLETE JOINT past,
individual next-action marginals K_0 and K_1. First use prefix-only caching:
share a neural call while both full histories coincide, cease sharing after
first divergence. A later actual identical-input reunion can also be cached,
but is a separate full-cost obligation, outside this prefix comparison.

## Maximal action pair, classical

At a common state, write p(a)=K_0(a|s),q(a)=K_1(a|s),m(a)=min(p(a),q(a)),
d=1-sum m. Standard maximal coupling assigns diagonal m(a) and residual
joint (p(a)-m(a))(q(b)-m(b))/d for d>0. If d=0 use the identical draw. Marginals
are p/q, residual supports disjoint, agreement is sum m=1-TV(p,q).

Without enumerating all a, sample a~p; accept common a with probability
min(1,q(a)/p(a)). On rejection draw b~q until an independent uniform exceeds
min(1,p(b)/q(b)). The admitted b has the required residual law. Expected
residual draws conditional on rejection are1/d; rejection probability d,
so expected total draws are2 when d>0 (one if identical is known). This
EXACT algorithm and cost are already in Jacob/O'Leary/Atchade Algorithm2.
Variance diverges near d=0; no bounded wall-clock claim. After k residual
attempts, unconditional FAIL probability is d(1-d)^k if capped. Returning an
arbitrary independent sample after that cap generally changes q and is invalid.
Rational probability comparisons may use exact integer coins. Floating
messages are not automatically those exact probabilities or native RNG laws.

## Prefix-only shared-work consequence, explicitly restricted

For any common history h and action a, every faithful coupling has diagonal
C_h(a,a)<=m_h(a). Thus the mass of EVERY common history under sequential
maximal action coupling, product of the m factors, is at least the mass of
that common history under any faithful prefix coupler. Induct along the
finite history tree; multiply the conditional diagonal inequalities.

For any nonnegative model-work cost c(h) while histories coincide, summing
these pointwise common-history masses times c(h) proves maximal EXPECTED
shared-prefix model work among faithful couplers. The marginal expected model
work of each policy is unchanged, hence expected paired model work minus
prefix reuse is minimal in this restricted class. This does not optimize
coupling overhead, batching, reunion work or nonfaithful/look-ahead couplings.
MEXIT already demonstrates that whole-path agreement can exceed greedy
faithful coupling: fair/.4 Bernoulli at two steps has .81 versus .89 with
look-ahead. Do not call the restricted result global minimal inference.

## Why discarded proposals can matter; strong class control

Suppose L_j(z,a) is a normalized joint kernel with auxiliary z and observed
action a, and K_j(a)=sum_z L_j(z,a). A coupling constrained to match the
SAME auxiliary has common action diagonal at most

    D_aux(a)=sum_z min(L_0(z,a),L_1(z,a)) <= min(K_0(a),K_1(a)).

The inequality is the classical contraction of total variation by projection.
It can be strict when opposite-sign likelihood changes cancel among hidden
values. Do not compare only full proposal/anchor triples: integrating anchor
is cheap, and sharing only the proposal's lexical class path is an obligatory
stronger control. Sharing the word/class proposal is feasible here because
its marginal is independent of policy parameters. Conditional maximal action
coupling under each shared word/class achieves D_aux, already a competent
standard construction. Full observed coupling is not uniquely supplied by a
new compiler; classical weighted inference gives the same K.

A small grammar proof object may use parity-constrained bit words: bit0 and
bit1 have distinct complete grammar transitions, so a class path retains
those bits. This is a correctness/separation object, NOT a performance task
or a model benchmark. No claim of unbounded real latency gain follows.

## Infinitesimal opportunity, not a timing result

For a fixed smooth positive finite-support kernel family at theta and
parameter direction v, consider theta+-epsilon*v/2. Let F_z(a) be the joint
score projected along v and S(a)=E[F_z(a)|a] the observed score. Standard
finite Taylor expansion yields

    TV(L_minus,L_plus)=|epsilon|/2 * E|F_z| + o(|epsilon|),
    TV(K_minus,K_plus)=|epsilon|/2 * E|S| + o(|epsilon|).

The first-order difference is nonnegative by conditional Jensen. Use the
CLASS-INTEGRATED joint score for the strong class-conditioned comparator,
not an arbitrary mixed-coordinate control variate that is not a density score.
For prefix shared-work with unit per-forward cost, the difference in its
first-order loss is weighted by the baseline expected REMAINING work after
the current observed action. A fresh conditional suffix supplies an unbiased
sample of that quantity; conditioning on future rewards or using current
hidden words as uncorrected weights is not allowed. This local identity does
not fix finite-epsilon performance, population uncertainty or numerical law.
No OLD-data opportunity numbers have been computed before this document.
