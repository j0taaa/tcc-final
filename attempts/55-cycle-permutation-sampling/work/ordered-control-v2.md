# Stronger classical ordered-loop control — after the first seven oracles

2026-10-16. This is an addendum, not a rewrite of theory-v1.md. Original
537af90 was written before code. The seven small oracles pass, but the
novelty/cost objection below prevents promotion of the NB/Ewens construction.

## Primary source actually read

Lawler, *Topics in loop measures and the loop-erased walk*, arXiv:1709.07531v1,
https://arxiv.org/pdf/1709.07531 , §5.3 Proposition5.3, Corollary5.4,
§5.4 Proposition5.5 and §5.5 Proposition5.8. Read these statements and their
surrounding constructions, not only a secondary summary. The time-one
growing-loop law is weight/G(x,x), its product normalizer is det(G), and
ordered rooted loops represent the ordinary soup. NB processes are already
explicit. These are direct antecedents to a competent implementation.

Also read Møller–Rubak2008, *Properties and simulation of alpha-permanental
random fields*, report R-2008-13,
https://webdoc.sub.gwdg.de/ebook/serien/e/reports_Aalborg_Univ/R-2008-13.pdf ,
§3.1's negative-binomial marginals and §§4.2–4.3's simulation. Its closed-walk
construction is known, including an explicit matrix-power bridge sampler.
This older bridge implementation may cost more to initialize, but does not
exhaust classical algorithms: Lawler's ordered construction is stronger.

## Direct implementation by last returns

Fix a vertex order 0,...,n-1 and S_v={v,...,n-1}. Independently for each v:

1. Start a Markov walk at v with substochastic transition R restricted to S_v;
   kill it when it leaves S_v or takes a row-deficit cemetery transition.
2. Retain only its prefix ending at the LAST visit to v. A walk never
   returning to v contributes the empty growing loop. Exclude the final
   repeated endpoint when counting loop visits.
3. Reject the whole trial if the retained growing loops visit a vertex more
   than once in total. Otherwise output their cycles and base fixed points.

The loop at v is sampled without evaluating a Green function. For a specified
closed prefix l, its probability is weight(l) times the probability, starting
from v, of no further return before killing. The latter is 1/G_Sv(v,v) by
the renewal decomposition into repeated returns. Thus its law is exactly
the CLASSICAL time-one growing-loop law.

After enforcing exclusion, each nontrivial output cycle is produced only
at its earliest vertex. Every other retained prefix is empty. The joint
probability of a permutation pi and acceptance is

    product_v [1/G_Sv(v,v)] product_{i:pi(i)!=i} R[i,pi(i)]
      = det(I-R) product_{i:pi(i)!=i} R[i,pi(i)].

The equality follows either from successive Schur complements or the
classical product-Green determinant identity. Consequently the acceptance
probability AND accepted normalized permutation law are exactly those of
A55 V1. Occupation counts also have the same law, so its rejection
certificate applies unchanged.

Importantly, one must NOT silently delete vertices already occupied by a
previous retained cycle or skip their walks. Doing so changes the law and
omits their empty-prefix normalization factors. Killing at earlier ORDER
vertices is required; killing at arbitrary occupied FUTURE vertices is a
different algorithm. Likewise, repeated vertices in the discarded tail do
not cause rejection.

## Complete-cost implication

Prepare categorical rows for R plus cemetery once, O(n²) arithmetic/storage;
leaving S_v can be recognized after the same unchanged row draw. Each walk
has at most r probability of remaining alive at every transition, so the
expected number of transition draws including killing is <=1/(1-r).
All n walks therefore cost O(n/(1-r)) draws/pointer work, or O(n log n/(1-r))
comparisons with simple CDFs. Inverse/matrix powers/Ewens/negative-binomial
construction are unnecessary. Rational bit costs and unlimited/capped laws
remain as in V1. This matches its favorable asymptotic cost with a simpler
classical implementation. Early rejection can be used in BOTH methods;
we do not claim a universal wall-time dominance from primitive counts.

## Decision and allowed next step

The elementary A55 construction and cost regime are not yet an adequate
own scientific contribution: a direct classical ordered-loop construction
recovers the same law/certificate and favorable complexity. This is a
NEGATIVE originality audit, not a failed latency benchmark or evidence
that exact assignment sampling is useless. No new model head, real-input
matrix statistic, competitive timing or broader neural campaign has occurred.

An independent small control-law oracle may check this reduction. There
is no reason to implement extensive NB/Ewens tuning or run a neural campaign
merely because it defeats independent-row rejection. A new useful distinction
would need its own eight-criterion reassessment. Current scientific goal
remains OPEN, and the main article is not promoted from this audit.
