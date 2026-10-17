# V2 proof audit: redundant odd pools, not the universal safety theorem

2026-10-16. This is a written refinement of A45's existing contract, not a
reopening of A44's rejected gradient application. The eight criteria in the
README continue to apply: no cheap useful neural source boundary, useful
full-cost advantage or sufficient priority has been established. No new
prototype, population screen, neural call, label or timing is performed.

## 1. Fixed-order identity for every label count

Let H_B(r) be the conditional half-shifted tower JOINT matrix of the original
contract, for a FIXED ordering of L label blocks and counts summing to B.
Keep zero blocks in that ordering. If B=2m+1>=3 and I is selected with
probability r_i/B, then

    H_B(r) = sum_i (r_i/B) H_(B-1)(r-e_i).                 (1)

This generalizes the familiar scalar Bernstein degree-elevation observation
already recorded in A44 to the ENTIRE finite joint matrix. It is a classical
degree-elevation calculation, not a claimed new sampling principle.

Proof. Write q(S)=sum_(i in S) r_i/B for any fixed subset of labels. Under
one uniformly deleted original slot, the new count on S is k-D, where
k=sum_(i in S)r_i and D is Bernoulli(k/B). Linear functions of q(S) preserve
their expectation. For h(x)=(x-1/2)_+, if k<=m both h(k/B) and every
h((k-D)/(B-1)) vanish. If k>=m+1, neither (k-D)/(B-1)-1/2 is negative,
and their expectation is

    k/(B-1) - (k/B)/(B-1) - 1/2 = k/B - 1/2.

Thus the same identity holds for h(q(S)), and for (1/2-q(S))_+ by adding
the preserved linear function 1/2-q(S).

Each H entry is the overlap length of two block intervals after a shift
by 1/2, including the possible wrap. For intervals [a,b),[c,d),

    length(intersection) = (b-c)_+-(a-c)_+-(b-d)_++(a-d)_+.

The interval endpoints are fixed prefix sums of q and their half-shifts.
Every difference of prefix sums is plus or minus a contiguous subset mass.
Each displayed term is therefore linear, zero, or a half-threshold hinge of
such a mass. The preceding identities apply term by term, including wrap
and zero-length blocks, proving (1).

Average (1) over the independent uniform label-block order; it remains true.
For IID population draws, deletion of a uniform original slot leaves B-1
IID draws. Consequently the UNCONDITIONAL joint matrices obey

    J_(2m+1)(p) = J_(2m)(p), for EVERY population p and finite L.             (2)

The payload lift also preserves this identity: conditioned on class labels,
the two different selected source indices have independent original P|class
laws. This holds even when the two classes coincide. Both separately
implemented even/odd methods can retain their own literal first draw.
Equation(2) promises equal JOINT DISTRIBUTIONS, not identical second payloads
or native RNG tapes on a fixed run. The proof's random deletion is an
averaging device; it is not an instruction to discard a required first draw.

B=2 has exactly the IID pair law. Thus B=3 has the IID pair law too. At B=4,
enumerating the five multiset shapes shows the same conditional law as the
A38 four-pool reference: 2+2 and2+1+1 pair opposite groups; the other shapes
have the ordinary second-index class law after averaging the block order.
Hence B=4 and B=5 inherit A38's already written all-score nonpositive
covariance result. This is a reduction to an existing control, not a new
competitor beating it. Only even B>=6 and at least four occupied labels
remain beyond the existing three-label proof and these reductions.

## 2. Why a tempting conditional induction cannot prove safety

The B=6 profile r=(2,2,1,1) already in the preserved V1 decision has

    H_12=H_21=2/9,
    H_34=H_43=1/18,
    H_ij=1/18 for one big and one small label,
    H_ii=0.

Take f=(1,1,-2,-2). Its empirical mean is zero, and direct rational
substitution gives f^T H f=0. Its empirical variance is2. Sampling two
distinct original pool slots uniformly would give conditional covariance
-2/5. Thus the desired profilewise inequality

    H_B(r)-q q^T <= -(diag(q)-q q^T)/(B-1)

is FALSE, even though it would have cancelled the pool-mean variance after
multinomial averaging. Conditional negative covariance by itself is weaker
and likewise insufficient. The full population-averaged matrix conjecture
remains OPEN; this example does not refute that conjecture.

## 3. New primary check and scope

Van Berkel and Vondenhoff, *Exact and approximation formulas for second-order
inclusion probabilities in randomized systematic sampling with unequal
probabilities and without replacement*, Survey Methodology52(1),2026,
https://www150.statcan.gc.ca/n1/pub/12-001-x/2026001/article/00003-eng.pdf .
Read §§1–4 through Theorem4.1 and its proof. Uniform block ordering and exact
overlap formulas are established survey-sampling antecedents; subset sums
already replace factorial order enumeration. Their setup uses supplied
fixed sizes and excludes certainty units. It is not, by itself, a proof of
the additional MULTINOMIAL-population safety assertion here. No claim of
new subset-formula computation or priority is justified by A45.

Neal's original *Modifying Gibbs Sampling to Avoid Self Transitions*,
https://glizen.com/radfordneal/ftp/gibbs-self.pdf , §§10/12 reread: the printed
HST/OHST non-domination example concerns fixed original/probability order,
not uniform random LABEL order followed by empirical-population averaging.
It remains a warning/competent comparator. Do not relabel it as a refutation
or proof of A45 without an actual reduction.

## 4. Decision

No new universal safety theorem or useful model result is claimed. Odd pools
can be removed DISTRIBUTIONALLY within this family, but known A38 controls
already recover B4/5's law and better adaptive cost. A complete proof or a
valid exact obstruction is still required for even B>=6. No new numerical
search can substitute for that obligation, and no neural campaign is triggered.
