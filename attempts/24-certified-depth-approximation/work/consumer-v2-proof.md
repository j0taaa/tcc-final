# A24 consumer V2 — operation equivalence before code

Let each physical free row have original nonnegative binary64 weights w_i(t).
Their exact dyadic values admit an integer scale a_i>0 and integers W_i(t).
Use D_i=sum_t W_i(t), including ordinary unsupported tokens. Fixed positions
have one unit weight. For any positive rowwise scale k_i, every complete-word
integer weight, valid numerator and denominator multiplies by prod_i k_i;
all probabilities and normalized tail certificates therefore remain equal.
No positive weight may silently underflow or disappear.

## Exact summaries and selected IDs

Let c(t) be the complete lexer-effect signature of original token t over ALL
lexer states; M_i(c)=sum_{c(t)=c} W_i(t). A local lexer group is a union of
these global classes. The admitted deterministic stack DAG consequently has
the same integer transition weights when supplied with M rather than an
original-token integer vector. This is the established class quotient.

Sample its class path with ordinary integer ancestral choices, then choose
a class block proportional to its exact mass, then an ORIGINAL ID in that
block proportional to W_i. Conditional disintegration proves the exact
original-token law on the admitted bounded language J_d. Aliases are distinct
events; fixed IDs have their singleton law. Blocks may be retrieved only after
selection, provided the immutable provider reproduces their original weights.
This is A28's classical block recovery, not a new sampling theorem.

## Queried marginal numerator

Write alpha_i(s) for total weight of prefixes reaching state s at layer i,
and beta_{i+1}(r) for accepted continuation weight after the transition.
The deterministic lexer selects at most one local group g(s,t) for token t
from state s. The token marginal numerator is exactly

    N_i(t) = W_i(t) * sum_s alpha_i(s) * beta_{i+1}(next(s,t)),

where an absent/trimmed transition contributes zero. The sum is over ALL
reachable states, not the particular state visited by the sampled path.
Forward propagation uses each arc's full class mass. A cursor may compute
only layers preceding requested positions and retain just its current alpha.
It does not need V output numerators or a coefficient for every lexical group.
A full sparse outside pass computes the same quantity and is a mandatory
competent competitor. A fixed-slot query returns total for its fixed ID and
zero for every other original ID.

With graph edge/group storage E, cursor overhead is O(N_current) integers,
and it processes only the prefix through the last requested position. A
naive membership search is charged to group storage; no constant-time edge
lookup is presumed. Numeric preprocessing still scans all nV supplied weights
and digit words; selected-block recovery costs at most nB weights for block
size B. Bit lengths and nC exact class storage remain paid. This establishes
work/output bounds relative to the dense reference, not dominance over all
compact solvers or a universal latency factor.

## Full-posterior threshold and commitment

Let L be the bounded-language total in the same integer units and U be the
sound A24 tail upper bound. The full posterior query obeys

    N_i(t)/(L+U) <= mu_i(t) <= (N_i(t)+U)/(L+U).

For threshold theta, accept only if the lower bound >=theta, reject only if
the upper bound <theta; otherwise refine on the SAME original sampled word.
The old policy commits the first k accepted free positions in increasing
physical index, or the first free sampled position if there are no acceptances.
Once k acceptances are proved, later positions cannot change that list. Any
earlier ambiguous position must still resolve before committing. On refinement
keep the sampled word and repeat required confidence queries; no resampling.
Thus the commit map equals the existing fully evaluated policy for every
admitted sample. The unchanged A24 common-policy trajectory TV theorem applies
to the unlimited successful operation under its original assumptions.

No certificate proves semantic accuracy of the reference policy. Timed output
selection may depend on the sampled word and bias successful outputs: finite
resource measurements report COMPLETE/FAIL separately and do not certify the
law conditional on wall-time success. No post-sampling fallback changes this.
