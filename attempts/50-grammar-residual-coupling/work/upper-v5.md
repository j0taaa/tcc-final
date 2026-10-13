# V5 — One preparation, upper-profile provenance, exact residual outputs

2026-10-13. Written BEFORE implementation/measurement. V4's simultaneous
outside oracle passed51,340 original-ID marginal enclosures,15 full laws,
240 valid samples and11 zero-mass refusals. These results remain separate.
The new refinement keeps the SAME residual operation; it does not open a
different research direction or retrospectively change those data.

## Eight criteria: what changes

1. The consumer is unchanged: exact correction of a frozen grammar-valid
   whole-completion draft, or exact maximal coupling of two such heads.
2. Sparsification, sum approximation, provenance, stochastic ordering and
   rejection are known. Gawrychowski/Markin/Weimann2018 Lemma6 already proves
   composition of sum approximations through convolution; its Section2
   gives compression and range queries. No claim to invent these. Candidate
   significance is the complete residual algorithm with ONE preparation
   and polynomial conditional runtime/second moment at arbitrarily small TV.
3. V1/V4 repeat profile analyses n*q/n times per correction attempt. V5 does
   ONE analysis and uses stored provenance to sample and exactly correct.
   Thorisson/Jacob2020 conditional attempts are1/TV. Competent ratio-envelope,
   enumerated categorical, counting/sampling and OS*/CARS controls remain;
   no theorem claims all are slower or that unconditional mean improves.
4. The upper-tail and provenance proofs below give the operational theorem
   without code; independent complete-law enumeration will attack them.
5. No favorable performance family, new forward, label or latency claim is
   introduced. First validate the exact accepted law and singular supports.
6. Pay all grammar/head/normalizer work and O(H*M^2) provenance storage.
   Model forward is not avoided. Random-bit cost is charged separately;
   unbounded exact integer rejection has finite expectation, not a deadline.
7. This may be a direct specialization of known counting-plus-rejection
   constructions. Retaining provenance is standard; it is not evidence of
   novelty by itself. A shallow grammar or cheap ratio envelope may win.
8. Primary comparison/full proof and an actual full-cost dLLM use remain
   open. Do not call this publishing success merely because it is faster
   than the deliberately simple repeated-query reference.

## 1. Upper tail compression

Use S1's SAME contiguous blocks and integer masses, but move every block
to its MAXIMUM ratio. A nonsingleton has mass at most eta times the mass
strictly above it; heavy singletons stay exact. For every threshold t>=0,

    T_true(t) <= T_upper(t) <= (1+eta)*T_true(t).

Proof: at most one block crosses t. The possible added mass is at most its
block mass, hence at most eta times the mass above the block. That latter
mass is included in T_true(t). Outside crossing blocks equality holds;
singletons introduce no change. In particular a zero true tail stays zero.
The size/bit bound and sorted scan from S1 are unchanged.

The Stieltjes argument and multiplicative convolution proof apply in the
upper direction. After composition, all nonnegative increasing payoffs f
with f(0)=0 satisfy exact_integral <= upper_integral <= c*exact_integral,
with c=(1+eta)^d. For f(r)=(r-t)_+ this is RELATIVE even for a tiny positive
residual; no subtraction of approximate large numbers occurs.

## 2. Keep provenance, not just representative ratios

Each compressed atom stores its exact integer B-mass and a list of its
constituents with exact integer masses. At a leaf a constituent is the
original-token closure mark or the empty event. An OR constituent records
the chosen alternative. An AND constituent records the two CHILD ATOM
indices and has mass equal to the product of their B-masses. After grouping,
all pre-group constituents remain selectable in proportion to their masses.

Compress only after combining all alternatives of a node. Product lists
can remain temporary constituents until that compression. The original
conservative d from V1 remains valid; the actual exponent can be smaller.
Retaining constituents costs O(H*M^2) entries, not V1's O(H*M+M^2) atoms.
Integer cumulative masses permit binary-search selection. Wide OR fan-in,
list construction/sorting, bit lengths and storage are fully charged.

**Pathwise envelope lemma.** Every B-positive original word y has exactly
one derivation and hence one deterministic final atom label g(y). Its
representative R_hat(y) is at least its true ratio A(y)/B(y). This follows
inductively: upper block compression increases a representative, and
multiplication of nonnegative child representatives preserves the order.
The atom's mass is exactly the sum of B(y) over the words that map to it.

**Reconstruction lemma.** Conditional on root atom g, descending stored
constituents and then the selected child atoms produces each word in that
atom with probability B(y)/B_g. Proof is induction at OR and at decomposable
AND, using disjoint alternatives and products of exact child masses.
Aliases remain different IDs; a multibyte token has one closure mark.

This is ordinary provenance/unranking. Its point here is that the upper
grouping supplies a tractable POINTWISE residual envelope, not just a scalar
TV approximation or an unknown approximate sampler output density.

## 3. Singular events stay exact

In parallel compute three scalar quantities at every node: A_total, B_total
and A_common (A-weight with ALL B-positive original choices). The singular
A-mass is S=A_total-A_common, an EXACT nonnegative integer.

For a binary alternative, partition singular events DISJOINTLY into

    left singular × right any,    left common × right singular.

Their masses are S_left*A_right and A_common_left*S_right. OR sums masses;
leaf B=0 gives singular A-weight. Sampling the chosen channel recursively
with its exact scalar masses gives A(y)/S on B(y)=0. It needs no approximation
or recursive subtraction of approximate quantities. Zero A leaves never
receive positive singular sampling mass. A root singular event is valid.

## 4. Single-preparation exact correction theorem

Let t=Z_A/Z_B. From the upper root profile compute

    U_raw = S_root + sum_g B_g*(R_g-t)_+.

The exact raw residual is

    D_raw = Z_A*TV(P,Q)
          = S_root + sum_{B(y)>0} B(y)*(R(y)-t)_+.

Then D_raw<=U_raw<=c*D_raw. U_raw=0 if and only if the residual is zero.
Choose eta=1/(2*max(1,d)); c<=exp(1/2)<2. A proposal chooses the singular
channel with mass S_root or a common root atom with mass B_g*(R_g-t)_+.
In the common channel reconstruct y using the atom provenance. Its proposal
probability is

    s(y)=B(y)*(R_hat(y)-t)_+/U_raw.

Accept it with (R(y)-t)_+/(R_hat(y)-t)_+. In the singular channel accept
with probability1. These are exact rational Bernoulli decisions. Accepted
unnormalized probabilities are precisely Z_A*(P(y)-Q(y))_+/U_raw. Thus
independent repeated proposals return the EXACT residual law, with

    Pr[accept] = D_raw/U_raw >= 1/c > 1/2,
    E[N] < 2,  Pr[N>k] < 2^-k for every integer k>=1.

The proof does not require computing D_raw exactly. Proposal acceptance can
be zero for an A-zero word that upper compression grouped upward; this is
charged and harmless. A finite cap returns explicit FAIL, never a biased
substitute. Equal laws never enter the residual branch of maximal coupling.

## 5. Full complexity and comparison boundary

Use M=O(1+W*d) at this constant overall accuracy, where W bounds integer
inside masses; ratio and cumulative-mass bit lengths remain polynomial.
Preparation costs O(H*M^2*log(H*M+2)) arithmetic operations and O(H*M^2)
provenance entries, plus grammar/input/scaling/normalizers. A draw descends
an expanded valid derivation of size D with binary searches, paying
O(D*log(H*M+2)) arithmetic steps plus exact rational density and RNG bits.
All finite arithmetic operands have polynomial bit size. Generating an
integer below a non-power-of-two bound can itself use rejection; its expected
fair-bit cost is polynomial but is not a deterministic per-attempt deadline.
The correction attempt count has uniformly bounded second moment, and the
combined random-bit work has polynomial expectation and second moment.

This removes the n/n*q number of complete profile recomputations per attempt
from V4/V1. It is not a lower bound against all known counting algorithms,
nor a measured speedup. The full compiler/provenance storage can dominate.

Classical maximal coupling uses this residual after its standard draft
acceptance and attains the SAME optimal agreement1-TV. The resulting method
keeps maximality while avoiding Thorisson's conditional1/TV runtime factor
on the admitted compact grammar forest. Coupled rejection samplers2022
already control runtime variance with nonmaximal couplings; their finite
ensemble maximality is asymptotic, so compare the exact contracts explicitly.
Categorical enumeration and special analytic couplings remain exact controls.
No claim of new maximality, universal mean latency or native EPIC law follows.

## 6. Required next adversarial checks

Before timing: upper-tail containment at every breakpoint, nontrivial merges,
all ORIGINAL words' envelope weights/proposal/accepted laws, B-zero channels,
equal laws, zero valid masses, aliases, prefixes, fixed slots and tiny ratios.
An upper norm certificate alone does not verify provenance or the sampler.
Read the closest counting/rejection originals before judging significance;
the operation can be useful without the construction being substantially new.
