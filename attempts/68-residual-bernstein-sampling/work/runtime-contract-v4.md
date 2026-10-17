# V4 exact runtime contract, before code or stochastic execution

2026-10-17. Previous goal turn was PROGRESS: V3 certificates and consumer
source changed authoritative state, synced7509d33. Goal remains open. This
stage implements an executable exact-bit/reference runtime, not a competitive
timing campaign, new biological model or neural application.

## Interface and exactness

Use the SAME V3 H-gap coefficients, quartic envelope and source-count law.
f:[0,1]->[epsilon,1-epsilon], |f''|<=M, Lip(f'')<=H are supplied contracts,
not inferred from finite samples. Inputs are exact rationals. Floats are
refused rather than silently converted to probabilities. GMP-backed integer/
rational arithmetic and explicitly balanced products implement known weights.
No cross-attempt runtime import or mutation of frozen V1/V2/V3 files.

The public operation takes a sampling-only iid p-coin callable and independent
auxiliary random bits. Its probability p is never passed to the factory.
Preselect J before querying the input coins: P(J>=1)=2H/n0^1.5 and, after
entering the tail, use independent three-bit tickets to continue with1/8.
Draw exactly N=n0*4^J p-coins and compute k. At J=0 sample the base coefficient;
otherwise use V3's three-component coin, deferred function-free rejection
proposal and at most six f-value requests. H=0 uses the finite polynomial
guard, not a zero-weight mixture. Known cheap polynomial factories remain
strong separate comparators; the generic guard is not claimed optimal.

Every scalar Bernoulli uses exact binary threshold comparisons, with no float
uniform. Uniform integers use bit rejection. A geometric tail uses inversion
against ONE lazily revealed uniform, with shared prefix across all CDF queries;
fresh independent Bernoulli comparisons during inversion would be incorrect.
No fixed geometric/rejection cap is part of the exact factory. Pseudorandom
seeded test streams are demonstrations, not proofs of iid physical entropy.
The theorem assumes the supplied bit oracle is iid fair, as usual.

A caller may explicitly request a maximum input-coin resource limit. If N
exceeds it, return/raise a distinct RESOURCE_FAIL before consuming input
coins; do not resample J or count only conditional successes as exact. The
default mathematical algorithm is uncapped. All consumed bits/input calls,
callback requests/evaluations/cache hits and proposal work are observable.

## Arithmetic and equally informed controls

Use isolated Python3.11 plus gmpy2==2.2.1, wheel SHA256
b7131231fc96f57272066295c81cbf11b3233a9471659bca29ddc90a7bde9bfa,
from PyPI's original metadata. Do not modify the maintained .venv. Record
actual backend/GMP versions. Discovery/install is not a mathematical test.
GMP uses FFT multiplication for sufficiently large operands; balanced
product trees are specified rather than attributing the bit theorem to an
unspecified Python integer implementation. No full wall-clock bound follows
from a backend name alone; charge conversion, gcd, recursion and RNG.

For binomials, use balanced products and exact division on GMP integers.
For the dense SAME-kernel control, use balanced weighted hypergeometric sums,
not an intentionally naive repeated Fraction loop. A singleton coefficient
c_i/d_i has P=Q=d_i,T=c_i. Join across ratio a/b by

    P=P_L*a*P_R; Q=Q_L*b*Q_R;
    T=T_L*b*Q_R+P_L*a*T_R.

Then T/Q is the weighted sum relative to the first hypergeometric weight.
This supports varying rational denominators without artificially weakening
the dense comparator. All methods may cache f-values at identical rational
points; warm controls may also memoize scalar coefficients. Sparse methods
may cache their deterministic proposals/values, never reuse random outcomes.

BEFORE any competitive performance gate, also implement/review formula-aware
piecewise-polynomial moment integration, analytic-derivative alternatives,
direct cheap polynomial factories, and first-vote versus global-grid/scalar
cache reuse. For a rational cubic spline, b_m is piecewise polynomial of
degree at most5 after known stencil shifts; truncated factorial HG moments
give a competent exact formula-aware control. Its operation is not excluded
by an arbitrary value-only interface for functions whose formulas are known.
Lazy/retrospective and other coefficient-free approaches remain obligations.

The published genealogy consumer requires building parent branches before
colours, then voting from k; the new runtime must expose conditional votes
as well as complete factory draws. No full genealogy application or speed
claim is credited until executed and compared with appropriate controls.

## Prospective correctness stage only

1. Freeze this contract and README criterion update, then freeze runtime and
   auditor BEFORE one execution. Preserve any failed source/run separately.
2. Compare balanced GMP binomials with independent integer comb for all
   n0..128/k0..n, plus larger central/endpoint cases. Compare generic balanced
   weighted sums against independent rational sums, including non-common
   denominators. Compare GMP proposals with frozen V3 Fraction values.
3. Exhaust binary prefixes for Bernoulli and shared-uniform geometric
   primitives. Preserve unresolved prefix mass and bound exact target
   probabilities; empirical output frequencies cannot establish exactness.
4. Audit conditional probabilities/kernels against the independent Fraction
   references on ALL original six functions and small degrees. Check actual
   callback limits for sparse branches, source/kernel matching and cache law.
5. Execute complete calls for ALL original six functions, p in{1/4,1/2,3/4},
   seeds0..31 and BOTH sparse/dense. Separate level/source/auxiliary streams
   so methods get matched J,N,k; record outputs without requiring literal
   equality of different couplings. The p value is only in the external coin
   callable. Test resource limit65536; retain every RESOURCE_FAIL distinctly.
   Test an intentionally over-limit preselected level without consuming coins.
6. No competitive times, benchmark selection or success gate in this stage.
   Diagnostic execution duration is not performance evidence. Formula-aware
   controls/full-cost protocol and independent use evidence remain required.

Specific priority, adequate novelty, useful complete-cost advantage and the
positive user goal remain OPEN even if this full-runtime preflight passes.
