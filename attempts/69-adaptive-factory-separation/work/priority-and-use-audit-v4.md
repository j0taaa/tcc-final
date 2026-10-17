# V4 — Original-source audit and decision on use

2026-10-17, AFTER all V1/V3 finite audits. Written deductions and literature
reading only. No new implementation, experiment, head, timing or human review.
V1/V2/V3 and their freeze deviation remain unchanged. This note does not
relabel their tests as validation of these later arguments.

## 1. What the original Mendo algorithm actually consumes

Luis Mendo, *An asymptotically optimal Bernoulli factory for certain functions
that can be expressed as power series*, arXiv1612.08923v5, Sections1/2,
Algorithm1, Theorems1/2 and their complete proofs7.2/7.3 were read from the
original PDF. Its source-input cost is a STOPPING TIME depending on observed
bits. In particular, for f(p)=p^a, 0<a<1, the algorithm's expected consumed
input is p^(a-1), finite at each p in(0,1), and diverging near0. Its auxiliary
uniforms are cost-free in that paper's accounting; do not transfer that
convention into A69's complete bit-work contract.

The paper explicitly contrasts a preselected random power with stopping as
soon as its product is determined. Selecting an independent potential maximum
is therefore different from consuming it fully. A69 already makes this
distinction in theory-v1 Section1, but generic novelty language about
adaptivity must respect this antecedent. Section1 also explicitly records
that the square-root construction answers Nacu--Peres Question1; that question
must NOT be presented as currently open or as solved by A69.

Koskela et al.2510.01941v2 Introduction calls a Mendo power-series factory
non-adaptive. A full-consumption power-series version indeed fits their
interface; this does not change the actual consumed-work rule in Mendo's
Algorithm1. Do not infer which implementation those authors intended, or
claim a contradiction with their theorem from this terminology.

Originals:
- https://arxiv.org/pdf/1612.08923
- https://arxiv.org/html/2510.01941v2

## 2. Elementary classical controls already give generic separations

Here and below a preselected/full batch has EXACTLY A69's restricted contract:
N independent of p and the input sequence, all N consumed, any randomized
output kernel. Conditional on N=m its response is

    h_m(p)=sum_(k=0)^m b_(m,k) B_(m,k)(p),  0<=b_(m,k)<=1.

Classical Bernstein differentiation gives

    h_m'(p)=m sum_(k=0)^(m-1) (b_(m,k+1)-b_(m,k)) B_(m-1,k)(p),
    |h_m'(p)|<=m on[0,1].

Consequently, by the triangle inequality and Tonelli,

    |f(v)-f(u)|<= E[N] |v-u|.                             (1)

This does not require exchanging derivatives of an infinite mixture. A
finite-mean preselected/full factory must be globally Lipschitz. Arbitrary
ordering-dependent kernels are included by averaging over order conditional
on the number of ones, as in V1. These are elementary classical tools, not
a new lower-bound principle.

### Pointwise finite versus infinite work was already available

For fixed rational a=1/2, Mendo's original algorithm has finite consumed mean
at every p in(0,1). Equation1 excludes EVERY finite-mean preselected/full
factory for p^a, since its difference quotient at0 is unbounded. Even if the
contract only specifies equality on(0,1), a finite-mean mixture would extend
Lipschitz-continuously to[0,1], giving the same contradiction.

The output can be moved away from both endpoints without repairing this
objection: H_a(p)=1/4+p^a/4 has range[1/4,1/2]. Use the independent two-bit
mixture ticket of V1 and, only with probability1/4, invoke the classical
power factory. Its expected consumed work is p^(a-1)/4. All preselected/full
factories still have infinite mean by1.

This classical controller can also have finite complete BIT work for each
fixed p>0: when a=1/2, Mendo's stage-i hazard is1/(2i), simulated with exact
fair-bit uniform-integer rejection and O(log(i+1)) expected bit work. The
stage counter/denominator and source bookkeeping have polynomial cost in
log(i+1). Its survival probability is at most(1-p)^(i-1), so the total
expected internal work is finite at every fixed p>0. Ordinary iid source
calls with finite mean cost can be charged by Wald. No physical latency,
constant bit budget or finite expectation at p=0 is asserted.

Thus neither pointwise finite-versus-infinite capability nor a bounded output
range suffices as A69's specific difference from the classical literature.

### A growing finite-family gap was also already elementary

For integer K>=1, simulate p^K by stopping at the first0 or after K ones.
Its expected input work is

    E_p tau_K=sum_(i=0)^(K-1) p^i=(1-p^K)/(1-p), p<1,
    E_1 tau_K=K.                                         (2)

Every preselected/full factory for p^K has mean at least K by1 and its
endpoint slope K. The deterministic batch N=K attains this lower bound.
For the bounded-range response H_K=1/4+p^K/4, the lower bound is K/4,
attained by preselecting the same mixture ticket and consuming K only on
its1/4 branch. The adaptive cost is(1-p^K)/(4(1-p)) for p<1, but K/4 at1.

When K is supplied in binary, a simple prefix counter charges O(log(K+1))
work per consumed input plus reading K. At each FIXED p<1, total adaptive
work is O_p(log(K+1)) under the same finite-mean ordinary additive-cost
source contract; the full batch costs Omega_p(K). Therefore even a
pointwise full-work ratio Omega_p(K/log(K+1)) is an elementary classical
phenomenon. This is not credited as A69 novelty or a measured benchmark.

## 3. What remains different, and what is NOT established

The precise stronger candidate in A69 is the COMBINATION of:

- a single explicit response with an INTERIOR non-C2 accumulation and
  uniformly bounded adaptive input mean over ALL p in[0,1];
- pointwise finite complete internal bit work;
- all preselected/full kernels needing infinite mean; and finite polynomial
  truncations with a uniform input bound<2 versus batch optimum Theta(R).

The elementary powers above do not establish this combination: their
adaptive costs are unbounded near0 or grow at1. They DO defeat the more
generic priority framings. A69's possible more specific priority remains
UNCONFIRMED, including regularity/approximation antecedents; this audit is
not an absence-of-prior-art certificate or an independent validation of
all infinite proofs.

Mendo's construction also does not imply that A69 is faster than other
adaptive controllers. Classical lazy evaluation of A69's supplied predicate
is permitted and is the same stopping operation. A statically selected cap
with early termination belongs with adaptive consumed-work controls.

## 4. Natural-use audit: no application selected

Exactness is independently meaningful in computational statistics, but that
fact does not supply a consumer for the particular constructed f or f_R.
The following routes do NOT currently justify another implementation:

1. Population-genetic ancestry before colours. The published 2024 consumer
   requires a colour-independent potential ancestral graph. A69's stopping
   rule inspects source colours. Finite adaptive evaluation therefore does
   not itself provide that required graph. The infinite-mean full-batch
   obstruction is a limitation in that interface, not a demonstrated
   positive replacement. Do not reopen A68's failed numerical application.
2. An arbitrary acceptance gate in MCMC. A target's acceptance rule cannot
   simply be replaced by f_R and presumed invariant. Symmetric thinning of
   an existing reversible kernel is a valid classical alternative, but
   choosing that artificial slowdown does not supply a useful new target.
   No independent posterior/model needing A69's response has been identified.
3. A probabilistic-program runtime. Lazy short-circuit evaluation already
   implements the supplied sequential predicate. A69 lower-bounds only the
   full-consumption interface, not all exact runtimes. No real external
   program needing these narrowly spaced rare predicates has been found.
4. A finite-tolerance probability gate. The already-preserved V3 control
   approximates ALL f_R to error<1e-8 at full-batch mean1/2. Requiring exactness
   only to exclude that control is not a useful application argument.

The first route is checked against the ORIGINAL2024 Section2/Remark2 read
in A68, not a newly executed genealogy. The remaining objections are direct
contract checks, not reported experiments or a comprehensive application
survey. No claim that useful consumers cannot exist is made.

## 5. Decision and eight-criterion reassessment

1. Real operation: exact probability simulation exists, but an external
   consumer for this constructed response is still absent.
2. Own relevance: only the uniform/interior/all-kernel COMBINATION remains
   a possible own theorem; its priority and publication significance are open.
3. Choice: the written batch separation survives within its exact interface;
   classical adaptive and fixed-tolerance controls prohibit a broad win.
4. Proof: V1/V3 remain written candidates with finite exact checks; Section2
   above supplies additional classical objections, not new test results.
5. Experiment: no campaign is selected; no need to rerun finite audits.
6. Full cost: V3's pointwise bit/oracle model remains scoped. Mendo's free
   auxiliary convention is not imported. GPU batching/known p remain allowed
   alternative contracts and receive no false lower bound.
7. Fatal objection: mere adaptivity, pointwise finiteness and growing finite
   gaps are classical; tiny-feature tolerances and the absent consumer remain.
8. Article gap: independently justify specific priority AND a useful own
   consequence before further development. Do not promote A69 as a practical
   contribution or mark the user goal complete from this capacity theorem.

A69 is preserved as a theory candidate, but its PRESENT application route is
not selected for expansion. The user's positive goal requires another
independently justified operation or a substantive new useful consequence;
more finite oracle counts would not fix the missing evidence.

## 6. Exact reading scope and provenance

- Mendo original PDF264352 bytes, SHA256
  33051c8dfb4c4d40f351c3c8f59856a9c34e48318a4491a39e8c7c1fcf304605.
  Read Sections1/2 including Algorithm1, Theorems1/2 and proofs7.2/7.3;
  Section3's displayed statements and reference list inspected. Theorem3's
  sequential information proof and ALL other sections were NOT fully audited.
- Wastlund original *Functions arising by coin flipping*, May1999 author PDF,
  SHA256 df27b6b358c3faf680a392fc3c827cca1151eb2016f8af0cf8b91dfcd70b13cb.
  Read Introduction, definitions and Section2 Theorems2.6/2.7 with proofs
  (composition and convex mixtures). General existence proof/Section4 NOT
  audited here. The author footnote explicitly credits prior Keane--O'Brien;
  do not present Wastlund's general existence theorem as independent novelty.
  https://www.math.chalmers.se/~wastlund/coinFlip.pdf
- Keane--O'Brien1994 original DOI10.1145/175007.175019 was NOT obtained/read.
  Publisher access returned403/internal error in the bounded retrievals.
  Later authors' accounts and metadata do not substitute for original reading;
  no unverified statement about its expected-cost details is used here.
- Koskela et al.2510.01941v2 Introduction reread; the original2024 Section2/
  Remark2 and Holtz--Nazarov--Peres Section7 retain their earlier recorded
  reading scopes. No new claim to having read either complete paper.

No source PDF or third-party code is added to the maintained implementation.
