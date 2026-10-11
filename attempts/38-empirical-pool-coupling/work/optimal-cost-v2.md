# A38: pointwise minimum expected work, written BEFORE implementation

2026-10-11. This refines v1, which remains intact. V1's early version costs
4-c and attains the atom optima. The stronger construction below has the
SAME full joint output law but expected work4-2c+s3. The difference is
positive whenever at least two classes have positive mass. Priority remains
OPEN: unknown-density ordered overrelaxation and early auxiliary simulation
are known principles, and binary Bernstein clipping is already published.

## Contract and theorem

An iid original-payload oracle has unknown law P. The algorithm is universal
over ALL P on a fixed countable payload domain with AT LEAST THREE allowed
canonical keys, sees samples and independent random bits, and has cap4.
It retains the first payload, returns another OBSERVED nonfirst draw index,
preserves both original marginals, and attains the maximum reduction
p_i^2*(1-p_i)^2 for EVERY canonical atom and EVERY P. Do not assume that
only the keys seen so far are possible. A known two-key alphabet has a
different, cheaper binary optimum; informed algorithms remain controls.

For EVERY P, the minimum expected total draws among ALL such universal
simultaneous maximizers is

    E_P N_min =4-2c+s3,
    c=sum_i p_i^2, s3=sum_i p_i^3.                           (5)

The theorem concerns oracle work, not wall time, model forwards or all
decoders receiving logits. It compares the SAME maximal canonical benefit.

## Attaining adaptive construction

Draw the original X1,X2,X3; write their keys a,b,c. Return X1 and:

- If b=c, return ORIGINAL X2, stop at3.
- If a=b (so c differs), stop at3 returning X3 with probability1/2;
  otherwise draw X4 and return that literal X4.
- If a=c (so b differs), stop at3 returning X2 with probability1/2;
  otherwise draw X4 and return that literal X4.
- Otherwise the first three keys are DISTINCT. Draw X4, key d:
  if d=a, return a uniform one of X2,X3;
  if d=b or d=c, return X4;
  if d is new, return a uniform one of X2,X3,X4.

All coins are independent of the oracle. No new payload is synthesized.
This rule reads only equality of keys, never their numerical order or gold.
Selecting an original nonfirst index preserves the independent P|key lift.

### Why the joint law equals v1

Complete stopped transcripts by virtual unused iid draws to length4.
For patterns2+2, the two classes are always crossed. For2+1+1, singleton
first is always paired to the repeated class. Repeated first is paired to
each singleton with probability1/2: either the fair early/late choice selects
it, or it is one of the two uniform choices after three distinct initial keys.
For3+1, conditional on repeated first, the singleton appears at positions2,
3 or4. The repeated-second probabilities are respectively1/2,1/2,1, summing
to2; v1 gives0,1,1, also summing to2. Singleton first always receives the
repeated class. Thus the integrated conditional-multiset joint law agrees.
All-four-distinct choices are uniform among the other three classes after
averaging their exchangeable order; v1's literal X2 has that same law.
All-four-same is unchanged. These are all multiplicity patterns.

Consequently the diagonal, off-diagonal, negative covariance for EVERY L2
score and collision bound of v1 continue to hold for full raw payloads,
including aliases and failures. This is joint-law equality, NOT literal
second-output equality on each RNG tape. Literal FIRST is preserved.

### Work of the construction

Three draws are compulsory. A fourth is needed on every three-distinct
prefix, whose probability is1-3c+2s3. Prefixes with first repeated and a
different singleton have total probability2(c-s3); half require draw4.
The other prefixes stop at3. Therefore

    E N=3+(1-3c+2s3)+(c-s3)=4-2c+s3.

Memory is at most four raw payloads plus the oracle's working state. All
three/four FULL oracle calls and key conversion must be charged. A frozen
head callback need not rerun the model, but DOES rerun all native selection,
rejection and parsing required for that accepted-transition draw.

## Lower bound: ANY universal simultaneous maximizer

The binary Bernstein bound in v1 is attained for every atom. Equality at an
interior probability forces every nonnegative coefficient to its minimum.
In a virtual four-sample transcript with count_i=2:

- returning i twice is impossible;
- second has conditional marginal1/2;
- first!=i has probability1/2, so on that event second MUST be i.

These claims hold conditional on each finite multiset of keys with positive
probability: vary the distribution of the remaining keys, use uniqueness
of multivariate polynomial coefficients, or condition on their iid law and
use the zero of a nonnegative expectation. Within-class payload randomness
and independent randomization are integrated, not discarded.

1. N cannot stop at2. Equal first keys i,i may be followed by two different
   keys j,k, making count_i=2 and forbidding the only observed class i.
   Distinct first keys i,j may be followed by k,k, forcing the unobserved k.
   A positive stopping probability would violate the universal contract on
   a law with all three keys positive. Thus N>=3 almost surely, even if the
   actual P has only one/two positive keys; three are ALLOWED, not necessarily
   present in every actual P. Returning a nonfirst observed index also
   rules out stopping at1.
2. A three-distinct prefix MUST continue. Returning first is contradicted
   by a fourth equal to first. Returning either other observed class is
   contradicted by a fourth repeating the other nonfirst class, which forces
   that repeated class. These contradictions also cover randomized returns.
3. Fix distinct i,j. On a prefix i,i,j or i,j,i, stopping cannot return i:
   a fourth new k would make count_i=2. Let u_iij,u_iji denote the respective
   probabilities of CONTINUING past3, averaged over independent within-key
   payloads. In a virtual multiset3i+1j, required joint diagonal coefficient
   is1/2. Its four placements of j contribute a total of2. Singleton-first
   contributes0; the i,i,i,j placement contributes at MOST1; the two mixed
   prefixes contribute at MOST u_iij+u_iji. Hence

       u_iij+u_iji>=1.

   Multiply by p_i^2*p_j and sum over ordered distinct keys. These disjoint
   mixed prefixes contribute at least sum_i p_i^2*(1-p_i)=c-s3 to the
   probability of requesting draw4. All other prefixes contribute>=0.

Combining2 and3 proves E N>=3+(1-3c+2s3)+(c-s3)=4-2c+s3.
The written construction attains it. For countable alphabets, sum disjoint
events using nonnegative convergence. The pointwise optimum implies v1's
minimax value4 by uniform laws with support size tending to infinity.

## Application and unavoidable objections

Apply the callback to a COMPLETE original CFG-constrained decoder, or to
its accepted transition with a frozen head and a COMPLETE sufficient state.
The latter can avoid extra forwards for auxiliary draws, but its parser,
rejection budgets, error statuses and EOS behavior are NOT free. The bound
does not exclude methods using accessible logits, CDFs, raw-ticket strata,
more candidates or a different output distribution. They must be measured.

The half mixture with iid2 has the same gain as v1's mixture and smaller
expected cost3-c+s3/2<=3. It guarantees D_opt/8 but NOT pointwise dominance
over A37. The optimal-cost theorem does not by itself establish that extra
draws pay for final-answer accuracy. No neural campaign is authorized by
these written calculations alone; priority and a meaningful effect remain gates.
