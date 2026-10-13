# V8 — Competent scalar common-submeasure residual control

2026-10-13. Written BEFORE implementation/measurement. This strengthens the
comparison; it does not change V5 evidence or claim that coupling is new.
The candidate/controls must receive this control before any speed claim.
The same eight-criterion residual operation remains in the README.

## 1. Compact exact common submeasure

Use the same deterministic decomposable forest and its exact positive P/Q
root normalizers. At each node v, normalize each alternative's ordinary
A-inside/B-inside weight, giving p_(v,t),q_(v,t). If a node's normalizer is
zero, its corresponding row is zero; such a row cannot be selected by that
law in a positive root event. Let m_(v,t)=min(p_(v,t),q_(v,t)).

For a complete ORIGINAL word, its unique derivation selects a bounded
sequence of alternatives in depth-first order. Define

    C(y)=product_(selected v,t) m_(v,t).

The normalized grammar sampler laws are products of their corresponding
p/q kernels, so C(y)<=min(P(y),Q(y)). This uses uniqueness; ambiguous
derivation agreement is not the same as original-word agreement.

Compute c_v=sum_t m_(v,t)*product_child c_child, taking an empty product1.
This needs ordinary scalar operations in O(H) arithmetic steps. At the
root, c=sum_y C(y) and r=1-c is a certified upper bound on delta=TV(P,Q).
It is the classical synchronous local-coupling overlap, not invented here.
The better control is its RESIDUAL PROPOSAL, not just its upper certificate.

## 2. Sample P-C without subtracting nearly equal approximations

All scalars are exact. For a binary alternative with P children L,R,

    p_t P_L P_R - m_t C_L C_R
      = (p_t-m_t) P_L P_R
        + m_t (P_L-C_L) P_R
        + m_t C_L (P_R-C_R).

The three component masses are nonnegative:

    p_t-m_t, m_t*(1-c_L), m_t*c_L*(1-c_R).

Choose among all alternatives/components proportionally to these masses,
then descend the P/common/difference channels accordingly. A common channel
uses alternative masses m_t*product c_child and recurses common. A P channel
uses p_t and recurses P. A leaf difference is p_t-m_t. Exact zero-normalizer
children use totalP0 and c0, so unavailable channels receive zero rather
than an incorrect1-c. Empty deterministic nodes are handled explicitly.

These are weighted mixture channels; their auxiliary descriptions can
overlap in original y, but their SUM is exactly P(y)-C(y). Do not pretend
they are disjoint original events. The first-failure labels are disjoint
auxiliary descriptions. The produced proposal is

    s(y)=(P(y)-C(y))/r.

Retain the sampled derivation and multiply its p,q,m kernels to evaluate
P(y),Q(y),C(y). Accept with (P(y)-Q(y))_+/(P(y)-C(y)). Accepted words have
law (P-Q)_+/delta, and acceptance probability delta/r. Maximal coupling
therefore remains exact without knowing delta or a TV FPTAS.

## 3. A general polynomial conditional attempt bound

Let D bound the number of alternatives selected in a complete derivation,
padding shorter traces by deterministic dummy choices. Word-faithfulness
gives a bijection between words and these choice traces; their TV is delta.
The synchronous coupling follows matching prefixes until the first differing
choice. At a matched prefix h, its probability a_h is at most each of the
P/Q prefix probabilities. Its disagreement probability at that next choice
is TV(P_next|h,Q_next|h).

For arbitrary joint laws A(h,z),B(h,z), the triangle inequality gives

    sum_h A(h)*TV(A_next|h,B_next|h)
      <= TV(A_joint,B_joint)+TV(A_prefix,B_prefix)
      <= 2*delta.

The first inequality follows by inserting B(h,z) and bounding the extra
mass difference |A(h)-B(h)| after normalization; zero B-prefixes contribute
at most A(h), and can be bounded the same way. Using a_h<=A(h), summing
the disjoint first-disagreement events over at most D choices yields

    r <= 2*D*delta.

Consequently the EXACT residual sampler above has

    E[attempts]=r/delta<=2*D,
    Pr[N>k] <= exp(-k/(2*D)).

This removes the1/delta factor with scalar preparation. It invalidates any
A50 novelty defense that merely contrasts polynomial residual work with
Thorisson2020's repeated original-law proposals. For independent product
coordinates the stronger familiar bound r<=n*delta follows from data
processing and1-product(1-delta_i)<=sum delta_i.

## 4. Costs and zero/equality cases

At a positive node, each kernel denominator divides the local exact A/B
inside normalizer. Across H nodes and at most D occurrences, a common
denominator bounded by product_v(Z_A(v)*Z_B(v))^D suffices for every complete
kernel path. Its BIT length is O(H*D*W), polynomial, not an exponentially
large representation. Exact sums/minima/CDFs have polynomial bit operands;
all these costs are paid. Scalar arithmetic O(H) is not a unit-bit claim.

Channel CDF preparation requires O(H) entries. One draw traces at most D
occurrences with binary-search selection, evaluates the three kernel products
and uses exact rational Bernoulli correction. Conditional expected draw
work is bounded by O(D^2*log(H+2)) arithmetic steps, plus polynomial bits
and input/grammar/head/normalizer costs. Cumulative probabilities and random
bits are charged. No neural forward is saved by this primitive.

If r=0, C has total1 and C<=P,Q, so P=Q and the residual is undefined.
Conversely, if P=Q on words, their unique derivation laws agree. Every
reachable conditional kernel agrees, so c_root=1 and r=0. Unreachable
zero-weight nodes cannot invalidate this conclusion. Do not replace refusal
or a finite attempt cap with a supposedly exact original target draw.

## 5. Mandatory validation and changed scientific comparison

Reconstruct C and P-C for every original word independently. Check all
channel output laws, not just the scalar root bound. Compare r/delta with
2D and cover equal laws, zero-support children, aliases, prefixes, fixed
positions and tiny differences. Preserve failures. The control is new to
this audit, not automatically new to the literature; read Feng/Guo/Jerrum/
Wang2023's product coupling original and the2025 circuit transport contract.

V5 still has <2 ATTEMPTS after more expensive preparation and stored profile
provenance. This need not beat a scalar control with r/delta close to1.
The exact generic operation/bit extension may have value, but its novelty
and useful full-cost advantage are OPEN. Passing another small oracle is
not the scientific objective; the comparison must now include this method.
