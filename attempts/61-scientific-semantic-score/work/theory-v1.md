# Written scientific-value score, before reference implementation

2026-10-17. README8d6b560's eight criteria apply. This specializes classical
proper scores/conditional decomposition/rational kernels; no new general score
theory or established practical advantage is claimed.

## 1. What the unrestricted CRPS extension would get wrong

For y=1 and a point forecast x=10^E, ordinary value-space CRPS is10^E-1.
An exponent E=10^r has only r+1 decimal digits in the input numeral1eE, but
that loss has Theta(10^r)binary bits as an expanded integer/rational. Thus
A60's compact unrestricted-order QUANTILE result cannot imply polynomial
expanded-rational cost for exact ordinary CRPS or its value-scale gradients.
This is an OUTPUT-REPRESENTATION obstruction, not a lower bound on symbolic
power expressions, approximate CRPS, or all useful numerical scoring rules.

On a fixed positive finite band away from zero, significant-digit bounds do
give O(L)bits per exact value. Ordinary CRPS can then be computed by classical
min-kernel composition. That is a valid control, not our generic invention.

## 2. Semantics, target and score

The source has n fixed ORIGINAL token slots, independent positive weights
w_i,v=exp(theta_i,v), fixed supports/visible IDs, and byte strings. G accepts
exact JSON numerical documents (JSON whitespace is allowed around the numeral).
Each trace has weight prod_i w_i,v_i, and valid original traces are counted ONCE.
Original aliases and different spellings may denote the same mathematical value.
This is ONE frozen mean-field numerical prediction, not the final iterative
decoder's distribution, action likelihood, native RNG, or calibrated posterior.

Let Z be its valid source mass. Condition on G to define a law P of numerical
VALUES. Zero, including negative-zero spellings, has category c=ZERO. For a
nonzero value x, let

    c(x)=(sign(x),k),  k=floor(log10(abs(x))),
    m(x)=abs(x)*10^(-k),  1<=m(x)<10.

Both k and the rational m are computed from coefficient/exponent text without
expanding10^k. This representation is one-to-one apart from the zero category.
For a fixed positive constant lambda=1/9, define a loss (smaller is better):

    L(P,y) = -log P(C=c(y))
             + lambda*CRPS(P(M | C=c(y)), m(y))   if y!=0;
    L(P,0) = -log P(C=ZERO).

Here CRPS has the usual loss orientation E|M-m_y| - .5 E|M-M'|. If Z=0 the
source is EMPTY; if target-category mass is0, loss is+infinity/UNSUPPORTED,
and the implementation must not fabricate a zero loss/finite gradient. Formulae
for finite logit derivatives below assume Z and that category mass are positive.
The tiny rational reference can return an exact log ARGUMENT and a rational
offset; it does not represent irrational logarithms as exact binary floats.

## 3. Classical strict-propriety identity and its limits

For a finite semantic truth law Q supported by the stated domain, subtraction
of its own expected score gives

    E_Q L(P,Y) - E_Q L(Q,Y)
      = KL(Q_C || P_C)
        + lambda * sum_(c!=ZERO) Q_C(c)
          integral_1^10 [F_(P_M|c)(t)-F_(Q_M|c)(t)]^2 dt.

The log-score identity and CRPS divergence identity prove this directly by
conditioning on the observed category. All terms are nonnegative. Equality
implies identical category masses, then identical conditional laws wherever
Q_C(c)>0, and hence the SAME numerical law. Thus the score is strictly proper
on that finite-law domain. Countably infinite truth laws require the usual
finite expected-score/entropy assumptions; no broader automatic claim.

This is a specialization of established conditional scoring principles, not
new CRPS, a new proper-loss theorem or a claim of calibrated SGD outputs.
Strict propriety concerns optimization over distributions. Parameter-family
misspecification, optimization, finite data and domain shift can prevent it.

If a forecast and target are BOTH pushed through x ->10^r*x for integer r,
their nonzero categories shift k ->k+r and their conditional m laws stay the
same. The score is unchanged. This is DECIMAL-rescaling invariance of the
scorer, not arbitrary physical-unit invariance or invariance of a real model
after changing its textual input/output/tokenization.

If original path probabilities are redistributed among spellings of identical
values while P stays fixed, the loss stays fixed. This is semantic invariance
of a pushforward score; latent-variable likelihood and value-aware kernels are
antecedents. It does not say that arbitrary head perturbations preserve P.

## 4. Exact selected-category computation and the classical min kernel

Let B be raw mass in the observed category, excluding ZERO in this paragraph,
and let

    R = sum_(valid paths a in category) w(a) min(m(a),m_y),
    S = sum_(valid paths a,b in category) w(a)w(b) min(m(a),m(b)).

For nonnegative normalized mantissas, the elementary identity is

    CRPS = m_y - 2R/B + S/B^2.

Thus L=log(Z/B)+(m_y-2R/B+S/B^2)/9. Only the observed category is compiled;
the enormous space of possible scientific orders is not enumerated. The total
Z comes from the ordinary lexical JSON-number grammar. B/R/S use exact sign/
order evidence E=k-d. There are O(L)possible mantissa orders d. Each target
exponent k-d has O(L+digits(k))digits, so separate exact-target suffix machines
already give polynomial size without claiming a new bound or universal NFT.
For a supported category, digits(k)=O(L); otherwise support may simply be empty.

The selected-order significand normalizer emits m's canonical digits. Choose
a decimal precision D covering the source/label significant digits, and pad
to a fixed-width integer encoding of m*10^D. Every m is in[1,10), so all encoded
values and edge weights have O(L+label-length)bits, independent of the enormous
represented x. Epsilon padding/composition must have unique ownership.

A small CLASSICAL rational kernel computes min of two such digit words. Its
state tracks position, first lexical comparison (left/equal/right), and whether
one digit contribution has been selected. At each position, branch to select
its digit from the already smaller word (either if equal), weighted by that
digit's decimal place; all later edges have weight1. Accept iff selected once.
Summing these position contributions gives min(m,m'). This intentional additive
kernel path sum is distinct from spurious input-normalizer multiplicity.
The kernel has O(D)states/constant-alphabet edges. Composing it with both
weighted numeric automata and summing paths is the established rational-kernel
algorithm of Cortes/Haffner/Mohri2004, not an own generic inference advance.

If the complete selected-category output graph has size M, a coarse bound is
O(D*M^2)arithmetic/space for this kernel, plus all original-source/normalizer
construction, Z/B/R computation, and reverse differentiation. Use proper
epsilon filters, trimming and sparse fronts equally for complete controls.
Direct digit-DP and explicit sorted enumeration on small supports may be faster.
This document does not implement or benchmark the polynomial compiler.

For source rational weights with numerator/denominator bit bound b and E
expanded source edges, common-denominator path sums have O(E(b+1))bits;
the paired source doubles this order and fixed mantissa weights add O(D)bits.
All rational components and logit derivatives have polynomial bit length.
Log values require either symbolic log arguments or explicitly charged numeric
precision; no claim of exact binary representation of log(Z/B).

## 5. Bounded head-logit gradients, irrespective of numerical magnitude

Let P_G denote the original-trace posterior under G and P_c its posterior under
the target-category evidence. For original slot i/token v, the categorical
term's derivative is

    d_i,v log(Z/B) = P_G(X_i=v) - P_c(X_i=v).

Its per-row L1 norm is<=2. For a nonzero category define

    phi(a)=2 E_(b~P_c) min(m(a),m(b)) - 2 min(m(a),m_y).

Classical differentiation of the two-copy kernel expectation gives

    d_i,v CRPS = Cov_(P_c)(phi(A), 1{X_i=v}).

Each min lies in[1,10), so |phi|<=18 and its range is<=36. A bounded variable
in an interval of width36 has mean absolute deviation<=18; its covariance
with any event indicator has absolute value<=36/4=9. Conditioning phi on each
token category preserves this range. Therefore, conservatively,

    sum_v |d_i,v L| <=2 +18/9=4,     |d_i,v L|<=1+9/9=2.

This holds for ONE token per fixed original row, not arbitrary unbounded visit
counts. Fixed singleton slots have zero derivative; a row-wise common weight
rescaling also has zero derivative. These are source-LOGIT bounds, not bounds
on backbone/weight gradients, floating-point underflow or optimizer behavior.

For comparison of DIFFERENT objectives: for two values a<b and target a,
ordinary value CRPS is(1-p)^2(b-a). Its derivative w.r.t. the Bernoulli logit
of p at p=1/2 has magnitude(b-a)/4. It can grow with represented magnitude;
the scientific score's logit bound does not. This is a modeling/stability
property, NOT equal-quality superiority, the same score, or a latency win.

## 6. Full-vocabulary normalizers: a useful CLASSICAL cancellation and a trap

For fixed n slots, replacing w_i,v=exp(theta_i,v) by full-row softmax weights
multiplies Z,B,R by the SAME product of row normalizers, and S by its square.
They cancel in the score. Its gradient on IDs absent from ALL admitted G paths
is exactly0. A per-row projection to the union of admitted IDs can be exact
for this CONDITIONAL objective, with all token/grammar preparation charged.
This is classical conditional-model normalization cancellation and indexed
projection (already acknowledged in A36/GPIO), not an invented head algorithm.
Normalizing separately at each PARSER STATE is different and may change P.

Variable-EOT semantics with arbitrary marginalized latent suffix IDs can still
require FULL vocabulary sums: in unnormalized coordinates, unused suffixes
contribute their row partition functions, which vary with stopping length.
The union of admitted original full traces can then contain every suffix ID.
Do not infer a sparse native-EOT head from fixed-n cancellation, omit that cost,
or resurrect A52's rejected forced-PAD objective as if it were the stopped law.

## 7. An instructive alias example, and the control that ALREADY repairs it

Two independent token rows emit prefixes{1,10} and suffixes{e0,e-1}. Suppose
training words are1e0 or10e-1 with equal probability; BOTH have value1. Native
independent-token CE is minimized by1/2 at both choices. Its frozen product
law assigns1/4 to.1,1/2 to1,1/4 to10. Ordinary CRPS at the true value1 is99/160;
a semantic point mass at1 has0. Full-value proper objectives can attain that
point law by choosing either canonical alias. These are constructed laws,
not real-head uncertainty, final iterative-decoder errors or measured training.

Canonicalize the training words to ONE consistent representative, and ordinary
CE already gives the same point law. With fixed visible IDs, a competent
canonical-completion control may select a valid representative retaining them.
Full semantic NLL also has the correct optimum and can be much cheaper than
the paired min kernel. Thus the example DOES NOT establish an own advantage
over strong controls or trigger a neural campaign. It only explains why raw
word-marginal CE and a semantic one-head objective are different contracts.

## 8. The actual open hypothesis

Whole-value, scale-stable proper training might improve useful numerical
predictions/calibration under native token constraints compared with raw AND
canonical CE, semantic NLL, NTL/NTIL/SMMD, scientific codecs and direct numeric
probabilistic heads. These alternatives must have equal information, tuning
and full costs, and real code/number data. A generic exact implementation of
THIS SAME score is an implementation control, not a different quality objective.
The principles above are classical, and sufficient own novelty/usefulness
remain OPEN. Only a tiny independent rational enumeration reference is justified
now; it will NOT count as the polynomial compiler, a model update or a quality
gate. No native training/model capture is triggered by passing its oracles.
