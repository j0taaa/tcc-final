# V7 — Runtime obligations and a legal iterative dLLM consumer

2026-10-13. Written only: no model, timing, new sampler implementation or
claim of novelty. V6's complete2019 primary reading confirms that preparation
and back-pointers are antecedents. V5's accepted-law checks remain unchanged.
The README's eight criteria still apply; this file strengthens use/proof/cost
obligations and records a consumer that must not silently change its policy.

## 1. Complete rational bit bound

Let I be the total bit length of all original nonnegative rational leaf
weights, original support IDs and the explicit scoped forest. Per-position
denominator clearing uses an LCM whose bit length is at most the sum of that
row's denominator bit lengths. The resulting integer table therefore has
polynomial size in I. Computing it, including GCD/LCM and reading every
original ID, is charged.

Let D bound the number of nodes in any expanded root derivation. This is an
explicit polynomial hypothesis; for an epsilon/unit-free CNF byte chart with
maximal emitted length B_bytes, D<=2*B_bytes-1. A decomposable word-faithful
inside total is bounded by the product of the sums of the leaf weights on
its scope, so its integer bit length is O(I). In a more general admitted
representation, a loose bound D*(I+log(H+2)) also suffices. Repeated squaring
without a polynomial expanded-size bound is not covered.

Every retained ratio is a product of original a/b ratios from disjoint
physical scopes: OR compression selects an existing representative, AND
multiplies representatives on disjoint scopes. Its numerator/denominator
bit lengths are polynomial in I,D. Each stored integer mass, constituent
mass and cumulative mass has polynomial bit length. Fraction-valued root
payoffs have polynomial numerator/denominator bits. Combining M such values
by a common denominator costs at most O(M*poly(I,D)) bits; it cannot be
treated as constant-time rational addition, but is still polynomial.

At eta=1/(2*d), M=O(1+W*d). Constructing each node's sorted precompression
constituents costs O(H*M^2*log(H*M+2)) arithmetic/comparison steps overall,
and retains O(H*M^2) entries with the above bit lengths. This counts all
provenance, exact scalar channels and root CDF construction. The reference's
max_pairs is a refusal limit, not proof that compilation fits hardware RAM.
Grammar admission, tokenizer expansion and the forward generating each
head precede these costs. A50 does not claim a verified source compiler.

After preparation, a common or singular proposal follows at most D selected
forest occurrences. Categorical choices use binary searches in cumulative
integer masses; singular channel branching has two choices. Computing the
original A(y),B(y) is a product over n original IDs, not another forest
membership pass: provenance already supplies validity. Exact rejection uses
the retained root ratio and those true products. All finite operands and
the number of comparisons/multiplications per proposal have polynomial bounds.

## 2. Random-bit work, not a deterministic deadline

The mathematical RNG interface supplies independent fair bits, equivalently
an unbiased uniform integer below a declared positive bound. A seeded PRNG
is an implementation of that interface for reproduction, not a new proof
that its finite state gives every mathematical rational law literally.

For a b-bit integer bound, bit-rejection accepts a b-bit draw with probability
strictly greater than1/2. Its retries have an exponential tail and moments
of every fixed order bounded by constants. There are at most D+2 such calls
per proposal, all with polynomial b. Consequently the proposal cost C has
uniform polynomial second/fourth moments and polynomial expectation. There
is no deterministic cap on fair-bit retries, even though all arithmetic
operands are of bounded size.

The correction attempts are independent; their acceptance probability
alpha=D_raw/U_raw>1/2. Let N be the first successful attempt and C_i its
work. The event N>=i depends only on earlier attempts, hence is independent
of the fresh C_i. Therefore E[sum_(i<=N) C_i]<=2*E[C]. For the second moment,
write the square as a double sum. By Cauchy–Schwarz and a uniform fourth-
moment bound K, each term with i<=j is at most

    sqrt(Pr[N>=j])*sqrt(E[C_i^2*C_j^2]) <= sqrt(K)*2^(-(j-1)/2).

There are at most2j such ordered terms for that j, and their series converges.
The second moment is thus polynomial too. Acceptance and proposal work
need NOT be independent within the same attempt. A random wall-time race
between two samplers can bias outputs and is not authorized by this argument.

## 3. An iterative consumer with correctly distributed cached drafts

Consider a decoder with a fixed grammar/support and absent EOS. At step t,
given canvas C_t, evaluate a deterministic dLLM head and define the exact
completion posterior P_t on the valid assignments extending C_t. Choose a
nonempty set S_t of positions using ONLY C_t, time, the head and independent
policy randomness: S_t must not depend on the sampled free token values.
Sample Y_t~P_t and fix its tokens on S_t. Eventually all positions are fixed.
This is the comparison decoder; it is not EPIC's native policy.

Keep the complete Y_t as a draft for the next step. Conditional on the newly
visible C_(t+1), the previous head and the permitted policy information,
Y_t has law Q_(t+1)=P_t conditioned on those fixed values. This follows from
ordinary conditioning, precisely because S_t was selected without inspecting
the remaining sample. Its table is the cached old head with fixed positions
made deterministic and the appropriate NEW conditional normalizer.

The next dLLM forward gives P_(t+1). Standard draft acceptance plus V5's
residual correction turns the cached Q draft into an exact P sample. Induct
over steps: each visible canvas transition has the SAME law as the comparison
decoder, and the final token assignment has the same law and grammatical
validity. The draft remains unchanged with the largest possible probability
1-TV(Q_(t+1),P_(t+1)) among updaters with those conditional marginals.

This does not apply to policies that choose positions by confidence of the
SAMPLED tokens, or record additional value-dependent rejection/remasking
history. Conditioning only on canvas there can give the wrong draft law.
It also does not assume that the next neural logits remain stable. Original
token aliases remain distinct; optimal ID agreement is not an automatic
theorem about minimum tree-edit distance or semantic equivalence.

## 4. What this actually buys, and what it does not

The legal consumer proves law-preserving reuse and minimum probability of
changing the complete draft. The original independent-update decoder changes
it with probability1-sum_y Q(y)*P(y), at least TV(Q,P); this is classical
coupling theory, not an invented optimality result. Cached head normalization,
target normalization and one target forward still cost. Each changed head
requires its own profile preparation; a previous certificate cannot be
amortized over different predictions without proof.

For a pair of heads and K outputs, a full cost comparison must contain

    common head/grammar preparation + Q normalization + P normalization
    + acceptance density work for ALL K drafts
    + residual preparation (if triggered) + correction/reconstruction.

It must compare with direct P sampling from an equally prepared scalar
inside plan, with categorical enumeration when possible and competent ratio
envelopes/OS*/CARS. For K=1, double normalization can cost more than all
reconstruction saved. Neural evaluations are not reduced by this consumer.
Minimum replacement probability is useful information but not a demonstrated
speed or semantic advantage. A practical experiment must identify its actual
consumer, workload and paid costs before choosing tolerances or successes.

Current status: the mathematical operation and a legal dLLM insertion are
written and the residual reference is finitely validated. The construction's
substantial difference from the competent known combination and useful
full-generation economics remain unresolved. Do not promote the main article
or treat this addendum as achieving the user's objective.
