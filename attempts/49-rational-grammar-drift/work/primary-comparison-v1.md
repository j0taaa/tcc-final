# Closest-primary audit before the finite oracle

2026-10-12. No publication/priority certificate or human review.

1. **Fu2609.24235v1, actually read1,3.3--3.4,4.1.**
   <https://arxiv.org/html/2609.24235>
   Definition3.6, Assumption3.7 and Theorem3.8 ALREADY permit an acyclic sequence
   of admissible gates and a low-dimensional root zonotope. They are NOT limited
   to the named product/Markov/fixed-tree examples. Disjoint tagged unions and
   componentwise Cartesian products are a direct instantiation. Consequently,
   merely giving an arithmetic FPTAS for unambiguous shared grammar derivations
   is a corollary of that theorem, not discovery of a new principle. The stated
   computational model explicitly includes exact real square roots/exponentials
   and a matrix inverse-square-root primitive; it does not analyze bit lengths.
   Our prospective exact rational planar implementation must add something
   useful beyond filling that boundary with standard geometry. This is OPEN.
2. **Bhattacharyya/Cormode/Fu/Meel2609.18707v2, actually read1,4.**
   <https://arxiv.org/html/2609.18707>
   Theorem4.1 handles smooth decomposable PCs sharing a v-tree, with unrelated
   gate wiring allowed. Its product propagation lemma is the same bilinear
   all-linear-query principle used here. Section5 covers WTAs on a FIXED binary
   tree, not arbitrary variable-shape word parses. This is a scope distinction,
   not an encoding-independent lower bound against the method. Fu's more general
   abstract framework above already closes a generic novelty claim.
3. **Bhattacharyya et al. ICML2024, originalarXiv2309.09134.**
   <https://arxiv.org/abs/2309.09134>
   Actually read definitions2.7--2.11 and technical overview3.1 this turn.
   The reduction uses locally normalized CPTs over a common Bayes-net graph
   and a partial coupling/derived inference oracle. It is a randomized relative
   approximation, not the rational deterministic certificate proposed here.
   A product conditioned on a CFG is not automatically a locally normalized
   Bayes net over the independent-token graph. Do not assert impossibility of
   a competent alternative encoding; the full proof has NOT been audited yet.
4. **Anand/Benford/Guo2607.27088, actual Algorithm1 and Lemmas2--4 read.**
   <https://arxiv.org/html/2607.27088>
   Already gives linear-time relative randomized TV approximation for products.
   Filtered-martingale unbiasedness holds more broadly, but its relative second
   moment proof uses independence of the unseen suffix. No speed claim against
   this algorithm on product inputs is justified by the planar prototype.

The scientific novelty of the rational compressor, complete grammar bit bound
and application is unresolved. No performance, model, or article gate follows
from an exact norm oracle. A49 is a small falsification prototype only.
