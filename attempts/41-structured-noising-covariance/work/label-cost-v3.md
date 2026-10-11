# Separate raw preparation from surrogate classification

2026-10-11. Written BEFORE the label-lazy reference and its oracle.
This corrects a potential MODEL TRANSFER error: A39's opaque query obtains
both original payload AND label; A41 can prepare masks separately and can
evaluate a selected mask without first classifying it. A39's4-2c2+c3 lower
bound is NOT automatically a bound on expensive surrogate calls here.

## Exact operation and scope of the new lower bound

A uniform distinct four-source pool is given (or drawn lazily with virtual
unused sources). The anchor is uniform in that pool, chosen before any key
query, and retained literally. Unknown labels come from at least three
PERMITTED labels. A classifier query reveals a label at one visible pool
address. Raw states and independent randomness are available; neither labels
of unqueried states nor class sizes/inverses are given for free. The second
returned raw state can be UNCLASSIFIED. Full expensive scoring is separate.

The required conditional POOL sampling design has each source marginal
uniform in the four-pool and attains empirical minimal atom diagonals
max(0,r_i/2-1), for EVERY partition of the four sources. This is the classical
balanced-pivotal law after source symmetrization, NOT a novel target law.
This requirement is stronger than only preserving global original marginals.
The lower bound below covers this pool-design operation; it does NOT cover
every possible two-output sampler of a huge original source space.

## Label-lazy same-law decision rule

1. Draw/retain original first X, draw Y. Classify X and Y, obtaining a,b.
2. If a=b, return(X,Z) for a fresh UNCLASSIFIED Z. Two classifier calls.
3. Otherwise draw/classify Z, obtaining c.
4. If c=a, return(X,W) with a fresh UNCLASSIFIED W. Three classifier calls.
5. If c=b, return(X,Y). Three classifier calls.
6. If a,b,c are all different, draw/classify W. If its key is a, choose Y/Z
   uniformly; if it is b or c, choose W; if new, choose Y/Z/W uniformly.

All raw returned states retain their original tokens/randomness. No score,
gradient, semantic answer or current expensive neural output defines the
classifier. Key is fixed before the source queries. The first score may
already have been computed: retain it and compute just ONE additional score.
Adapting the key using the just-observed score is outside the theorem.

## Written correctness by the five multiplicity patterns

Average the ordering of the other three sources keeping the anchor literal.
For4 equal keys the companion is uniform among the other three. For2+2 the
companion always belongs to the other class. For2+1+1 the doubled class is
represented exactly once: a doubled anchor chooses one singleton uniformly,
a singleton anchor chooses a doubled source uniformly. For all distinct keys
the companion is uniform among the other three. For3+1, a majority anchor has
a majority companion with probability2/3 and the singleton with probability
1/3; the singleton anchor always has a uniform majority companion.

For the last calculation, with majority anchor, Y matches it with probability
2/3 and Z then matches it with probability1/2, contributing1/3. If Y is the
singleton (probability1/3), step4 returns the majority W, contributing1/3.
Thus2/3 in total. Source symmetry within each class proves ORIGINAL-SOURCE
joint equality with C4/full class-first pivotal, not only class diagonals.
Consequently the existing entire-gradient covariance guarantee is unchanged.

Let c2=sum(n_i)_2/(M)_2 and c3=sum(n_i)_3/(M)_3 for a finite original source.
The label count Q and prepared-source count N satisfy

 E Q=2+P(a!=b)+P(a,b,c all distinct)=4-4c2+2c3,
 E N=3+P(a!=b,c=a)+P(a,b,c all distinct)=4-2c2+c3.

Thus label queries save4c2-2c3 relative to classifying a whole four-pool,
or2c2-c3 relative to classifying every prepared state. Labels can stop at2
even though3 original raw states have been prepared. These are different
costs, not relabelled A39 source counts. Controls may use the SAME shortcuts.

## Sharp classification cost for the specified pool design

In any hidden class of size2 the required expected number of selected sources
is1, and its minimal joint diagonal is0. Therefore EXACTLY ONE source of that
class must be returned almost surely, for every hidden completion. No positive
probability of omitting both or selecting both can be compensated elsewhere.

This forces the following necessary queries under at least three permitted
labels, regardless of which visible addresses an algorithm chooses:

* Stop at0/1 labels is impossible: two unclassified sources can form a hidden
  size2 class for which the selected pair contains zero or two members.
* If the first TWO queried labels differ, a third query is necessary. If the
  anchor is queried, completing the two unknown labels as a third doubled
  class forces an unknown companion; completing them as the two observed
  classes in both orders then forbids any fixed unknown companion. If the
  anchor is unqueried, assigning the two unknown sources the same third class
  forbids their joint selection; completing them in the two opposite observed
  classes requires opposite known companions. Neither choice works universally.
* If the first THREE queried labels are all distinct, the fourth must be
  classified. If the anchor is known, the last label may duplicate each of
  the three observed labels: a known companion misses one of those doubles,
  while an unknown companion duplicates the anchor in another completion.
  If the anchor is unqueried, its last label may duplicate any observed label;
  no companion can avoid selecting both of that possible size2 class.

Symmetrize unknown placements over the four visible pool addresses. Conditional
on previous labels, each newly queried label is uniformly without replacement,
even for an adaptive address choice. Necessary expected label cost is
at least2+(1-c2)+(1-3c2+2c3)=4-4c2+2c3. Our rule attains it on every
placement averaged over the original random pool order. Thus it is minimax
over UNKNOWN pool placements, not pointwise optimal for a known map.
Uniform pool averaging over a larger finite source gives the displayed finite
population expression. Known sizes, two permitted labels, analytical inverses
and unrestricted raw pools change the model and are not covered by this bound.

## An incorrect plausible shortcut, recorded before code

Nearest-class pivotal processing chosen by the anchor, then forcing that
anchor to win its pivot, is NOT generally an original-marginal companion.
With pool classes(A,A,A,B), majority anchor A pairs with another A, then
chooses A/B uniformly from the remaining pair. A singleton anchor B selects
an A. The second is A with probability(3/4)*(1/2)+(1/4)*1=5/8, not3/4.
Conditioning a design that DEPENDS on the selected anchor is not the same as
uniformly orienting a fixed exchangeable pool design. The return-W correction
in step4 preserves the marginal; do not replace it with a naive fair choice.

## Scientific decision, not a success declaration

This refines README criteria1/3/4/6/7: an already-computed original noising
score can be upgraded with one new current-model evaluation, cheap raw masks,
and a class-query-optimal balanced tree in the precisely stated pool model.
Dropping that anchor in RSS may require another score; charge actual reuse
and let competent controls use it whenever possible. Matrix lifting,
balancing and pivotal rules remain known. The possibly distinct result is a
sharp opaque CLASS-query theorem admitting unclassified returned states.
Its priority and significance remain to be audited. No external model, broad
latency win, improved full training, or publication acceptance is established.
