# Relative one-sided grammar masses and an exact residual sampler

2026-10-13. Written before code. These are written proofs to audit, not Lean
verification or independent human review. The construction uses classical
monotone-function approximation and self-reduction; priority is OPEN.

## 1. Mathematical input

An acyclic, deterministic, decomposable event forest represents a finite set
F of ORIGINAL-token assignments. OR alternatives are disjoint events with the
same position scope. AND children have disjoint scopes and their Cartesian
product is in bijection with the alternative's events. The root consumes all
n positions exactly once. Empty-scope unweighted events have multiplicity one.
Aliases of rendered bytes are distinct original IDs. There is no EOS/remasking
or changes to the support in this operation. A resource refusal is not zero.

Two nonnegative integer leaf tables a_i(v), b_i(v) give raw weights

    A(y)=prod_i a_i(y_i), B(y)=prod_i b_i(y_i).

The exact root totals Z_A,Z_B are positive. The probability laws are
P(y)=A(y)/Z_A and Q(y)=B(y)/Z_B on F. Clearing rational denominators per
position produces this input; its full cost is charged, not unit-cost LCM.
Let H include every alternative/edge actually processed. Let d be a polynomial
bound on the number of approximation operations in an expanded derivation,
adding costs at AND and maximizing at OR. For an admitted epsilon/unit-free
CNF byte chart of maximal word length B_bytes, d<=3*B_bytes-2 suffices when
compressing each binary product and each OR list; singleton leaves are exact.
Source normalization/admission costs are separate. Repeated squaring with
unbounded expanded derivations is outside this theorem.

The new query is the ONE-SIDED mass

    D_lambda(P,Q;E)=sum_{y in F intersect E} (P(y)-lambda*Q(y))_+,

for rational lambda>=0 and unary evidence E. Normalizers remain the ORIGINAL
Z_A,Z_B when E is imposed. Renormalizing after each prefix changes the problem
and invalidates the sampling proof.

## 2. Why a relative TV interval is insufficient

For unnormalized restricted masses, the positive part is

    [sum |P(y)-lambda Q(y)| + sum P(y)-lambda sum Q(y)] / 2.

A relative approximation of the absolute sum can lose all information about
a much smaller positive part after this subtraction. For example the two
signed differences -1 and 2^-k have positive part 2^-k, whereas their absolute
sum is 1+2^-k. A constant relative norm approximation need not resolve it.
This is a proof objection, not a favorable benchmark. Ordinary TV at lambda=1
without evidence has equal total mass and does not suffer this cancellation.

## 3. Sparse survival measures (classical ingredient)

For a finite positive measure mu on nonnegative rational ratios, write
T_mu(t)=mu((t,infinity)), t>=0. Sort and combine equal ratios. Construct a
new measure by partitioning the sorted atoms into contiguous blocks and
moving each block's total integer mass to its MINIMUM ratio. Keep the highest
atom exactly. Process downward; a nonsingleton block may have mass at most
eta times the mass strictly ABOVE that block. A heavier atom is kept alone.
Greedily extend a block until adding the next atom would violate this rule.

**Lemma S1.** T_mu/(1+eta)<=T_mu_hat<=T_mu for ALL t>=0, and total mass is
unchanged. At a threshold inside a moved block, the entire possible loss is
at most its block mass, bounded by eta times the retained mass above. Outside
blocks the tails agree. Singleton blocks lose nothing. These observations
also prove exact preservation of every zero tail, including the maximum ratio.

**Size.** Adjacent finalized blocks cannot have been merged under the upper
block's budget: their total mass exceeds eta times the mass above that upper
block. This holds also if the next atom becomes a heavy singleton. Every two
successive new blocks therefore increase the accumulated tail by a factor
greater than 1+eta. If total integer mass is at most 2^W and every nonempty
atom has mass at least one, the list has O(1+W/eta) atoms for 0<eta<=1.
Sorting/scanning an input list of m atoms costs O(m log(m+2)) comparisons and
additions. Splitting an atom is unnecessary. The greedy rule and this adjacent-
block argument must be checked by an independent oracle before implementation
is used; neither a fixed number of bins nor geometric ratio rounding proves S1.

**Lemma S2.** Tail containment with factor c implies the same containment for
the integral of ANY nonnegative nondecreasing function f with f(0)=0. On a
finite domain, f is a nonnegative sum of threshold indicators, or use its
Stieltjes integral. This is classical first-order stochastic comparison.

## 4. Composition without enumerating all completions

For events with B(y)>0, associate mass B(y) with ratio R(y)=A(y)/B(y).
Ratios zero are allowed. For a leaf with b>0 use the atom (a/b,b); b=0 emits
no atom. An empty event uses (1,1). OR takes measure sum. AND takes multiplicative
convolution: (r,w),(s,z) contribute (r*s,w*z), adding equal ratios. Compress
after each nontrivial product and each OR. This does NOT enumerate full words;
temporary AND lists have at most M^2 entries, and wide OR fan-in is charged.

**Lemma C.** If child tails approximate their exact measures from below with
factors c_1,c_2, the product tails approximate from below with factor c_1*c_2.
For t>0, the test x -> T_child(t/x), with value zero at x=0, is nonnegative
and nondecreasing. First apply the second child's tail guarantee pointwise,
then S2 to the first child's measure. Apply the upper bounds similarly. For
t=0, both positive-ratio masses multiply, giving the same conclusion.
OR uses the larger child factor, since sums of pointwise enclosures preserve
it. Compression adds another factor 1+eta by S1. Induction gives

    T_true/(1+eta)^d <= T_root_hat <= T_true.

Integrating from any threshold lambda_raw gives the SAME relative guarantee
for sum B(y)*(R(y)-lambda_raw)_+. Equivalently evaluate the finite sum of
retained w*(r-lambda_raw)_+; do not subtract approximate counts/moments.

Events with B=0 contribute exactly A(y) to the positive part. Compute their
mass s as the exact A-total minus the exact A-total on B-positive leaves.
For evidence E these are restricted raw totals. Thus

    L = [s + sum_hat w*(r-lambda*Z_A/Z_B)_+] / Z_A,
    U = [s + (1+eta)^d*sum_hat w*(r-lambda*Z_A/Z_B)_+] / Z_A

enclose D_lambda(P,Q;E), and U<=c*L for c=(1+eta)^d. A zero lower endpoint
is equivalent to true zero. For accuracy xi<=1, eta=xi/(2*max(1,d)) implies
c<=1+xi (log(1+xi)>=xi/2). All arithmetic is rational/integer.

**Cost.** W=max bit length of exact B-inside totals. With word-faithful scopes,
these totals are bounded by products of position totals; W is polynomial in
the original input bits. Coarsened masses stay integral, their totals are
unchanged, and every representative ratio is a product of original ratios
on a disjoint scope. Ratio numerator/denominator bits stay polynomial too.
M=O(1+Wd/xi). A direct implementation costs O(H*M^2*log(H*M+2)) arithmetic
operations, O(H*M+M^2) stored atoms, plus input, preparation, exact total passes
and output. Rational sums/normalization can use O(M*W) bits, so the arithmetic
bound alone is not a bit bound; multiplying by polynomial integer-arithmetic
cost and charging GCD/comparisons yields polynomial bit time. Wide sums can
be processed in a binary OR tree, whose added expanded cost must enter d.
No dependence on 1/D_lambda occurs; log-small rational probabilities are
already present in the input-bit parameter W. This is not strongly polynomial.

## 5. Pointwise proposal and exact correction

Set w(y)=(P(y)-Q(y))_+ and delta=sum_y w(y). First obtain L_root,U_root with
accuracy xi=1/(4*n). If L_root=0, delta=0 exactly and the residual is undefined;
the coupling never needs it. Otherwise construct a sequential proposal.
At each original physical position, query the lower residual mass for every
allowed value with the current prefix evidence. Choose among those values
proportionally to their lower masses. Each child query uses ORIGINAL Z_A,Z_B.
Keep the product s(y) of the exact rational proposal transition probabilities.

Let rho=w/delta. The per-value lower masses lie between their true masses
divided by 1+xi and their true masses. Summing them gives the corresponding
parent enclosure. Every proposal transition divided by the rho transition
is between 1/(1+xi) and 1+xi. Zero branches are omitted exactly. Therefore

    (1+xi)^(-n) <= s(y)/rho(y) <= (1+xi)^n

on the residual support. Put K=(1+xi)^n and E_bound=K*U_root. After a proposal,
accept it with the EXACT rational probability

    w(y)/(E_bound*s(y)).

The pointwise bound proves this number is in [0,1]. An accepted proposal has
unnormalized probability w(y)/E_bound, so repeated independent attempts give
EXACT rho, not an approximate residual. Acceptance per attempt is
delta/E_bound >= 1/[K*(1+xi)] >= exp(-1/2) > 1/2. Hence

    E[attempts] < 2,   Pr[attempts>k] < 2^-k,

even CONDITIONAL on entering a residual branch and for arbitrarily small
positive delta. Every attempt pays up to n*q complete profile constructions,
its exact point density and rational RNG/correction; it is not an O(n) sampler.
Taking xi=1/(4n) gives polynomial work per attempt and polynomial expected bit
time/second moment, with the stated input/preparation terms. A hard cap has
FAIL probability <2^-k; outputting a native P draw on FAIL would bias the law.

## 6. Classical maximal coupling as consumer

Draw X~Q and accept X as the target output with probability min(1,P(X)/Q(X)).
If rejected, use the above rho sampler independently of X. Then the target
output Y has law P and Pr[Y=X]=sum min(P,Q)=1-TV(P,Q), the largest possible
agreement for those marginals. Both outputs are valid original-ID assignments.
This is classical maximal coupling, not a new coupling identity.

Jacob/O'Leary/Atchade2020 Section4.1/Algorithm2 samples the residual by
proposing P; conditional attempt count is geometric with mean 1/delta and
second moment (2-delta)/delta^2. Its overall mean remains constant because
that branch occurs with probability delta, while cost variance diverges as
delta tends to zero. Our proposed polynomial per-attempt work avoids this
conditional rarity factor; it does NOT imply a smaller unconditional mean,
a deterministic deadline, or dominance over every other residual algorithm.
Categorical enumeration, exact ratio envelopes and structured counting
controls may be much cheaper and are retained as comparisons.

## 7. dLLM/CFG use and limits

The result is a reference primitive for verifying a whole grammatical draft
sample or coupling two frozen prediction heads. A target forward is still
needed. The theorem preserves the target LOCAL completion posterior, not
EPIC's native proposal/commitment trajectory, and not the base dLLM conditioned
on eventual validity across all future denoising steps. TWISTER2609.35609v1
already treats the latter distinction. A value-dependent partial commitment
may require a different pushforward density and is outside this theorem.

No semantic accuracy or generation latency is inferred from exact marginal
preservation. Repeated expensive queries may make this primitive unsuitable
for online inference. What is mathematically changed is a conditional-cost
guarantee of an operational correction, including original-token identities,
not another fidelity-budget table decision. Its academic significance still
depends on comparison with known counting-to-sampling constructions.
