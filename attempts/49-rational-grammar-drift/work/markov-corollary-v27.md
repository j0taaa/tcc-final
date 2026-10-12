# Ordered-core Markov corollary and its precise relationship to grammatical paths

Written proof, not a new implementation, physical timing or application gate.
The sum/diagonal recurrence and sorted-list merge are classical: Feng/Liu/Liu
SODA2024 Section5 already uses q-way merging; Section6 Theorem2 and Lemma19
give the Markov variant. Primary <https://arxiv.org/html/2309.14696v1>.
Read those statements, Algorithm3 and the complete Lemma19 argument here;
this note does not claim a fresh complete audit of all Section6 lemmas.

## Full-state trajectory theorem

Two inhomogeneous Markov chains on q states have rational initial laws and
transition rows. Compare laws of the ENTIRE n-state trajectory, not only a
hidden-state marginal. For each position clear denominators with ONE common
multiplier over the whole transition matrix of that head. A multiplier
depending on the previous state would change the path law and is INVALID.

For each endpoint j maintain paired vectors for all prefixes ending at j.
At the first position this is its single initial-weight pair. To extend to
endpoint k, diagonally scale each preceding endpoint's family by its two
transition weights(j,k), then take their union. Different preceding j mean
disjoint trajectory events. A nonnegative diagonal image preserves canonical
angular order, with the stated exact singular-map handling. Thus q sorted
streams, each of length O(sqrt(n/epsilon)), suffice per endpoint. One ordered
compression follows each union; final endpoint union adds at most one gate.

With d<=n, choose the existing calibrated grid. Induction on positions gives
the same all-query lower factor alpha^d and upper factor1. Exact forward
normalizers A,B are computed separately. The final direction(B,-A) therefore
yields L<=TV<=U<=(1+epsilon)L. Zeros are admitted; either zero normalizer
refuses, and TV zero returns exact zero. Prefix masses sum to at most the
product of common position denominators, so the integer bit proof applies.

The arithmetic bound is

    O(n*q^2*sqrt(n/epsilon)*log(q+2)),

including O(nq^2) input/scaling/forward-normalizer work with the explicit
common-multiple algorithm. Charge grid/output arithmetic as in
full-arithmetic-scaling-v27.md. Polynomial input-bit intermediate lengths do
not imply input-bit-independent BIT time.

The previous stated deterministic Markov bound in SODA2024 is
O(n^2 q^2 epsilon^-1 log q log(n/(epsilon TV))). Fu2609.24235v1 Corollary1.5
gives the strongly polynomial real-arithmetic bound O-tilde(nq^2(n/epsilon)^4).
The improvement here concerns those published upper bounds, not a lower bound
on every implementation or a universal physical acceleration. All geometric
and Markov recurrence principles remain antecedents.

## Labeled deterministic automata: a grammatical special case

The same argument works on an acyclic layered deterministic labeled graph:
one token per physical position, original IDs on edges, every ID sequence
determining at most one state path. For e_i original transitions in layer i
and f the maximal number of incoming streams, the bound is
O(sum_i e_i*sqrt(n/epsilon)*log(f+2)), plus input and graph preparation.
Preserve every original label, including aliases; do not compare only terminal
state marginals. State probabilities from two differently weighted graphs
must normalize by their respective exact accepted-path masses.

A materialized deterministic predictive-stack graph for an LL(1) grammar has
this labeled-path property. Its construction can be exponential, so this
specialization does NOT replace the polynomial word-chart theorem. It also
need not be physically preferable to the implemented compressed token-group
AND forest: expanding every original edge may repeat large groups across
many states. Account both representations honestly; no smaller-work claim
follows just from the epsilon exponent.

An arbitrary nondeterministic HMM lacks the required original-word bijection.
Summing norms over its latent paths measures latent-path TV, which can exceed
observed-word TV. No general HMM theorem or hidden ambiguity elimination is
claimed.

## Eight-criterion disposition

This is a quantitative corollary of A49's proposed central algorithm, not a
new model or research branch. It broadens comparison with the exact nearest
published problems. Its use for dLLM/CFG auditing keeps README's frozen-head
contract, complete preparation/bit costs and original IDs. No scientific
novelty is assigned to the recurrence/heap. Before code, independently
enumerate small whole trajectories, including zero transitions and changing
normalizers; no synthetic performance family or new model campaign is planned.
Practical gate, human proof review, exhaustive priority and publication
sufficiency remain unconfirmed. V25's failure remains immutable.
