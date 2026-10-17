# V2 — Fresh local stop copulas: adaptive heads, unchanged pair trajectories

Written AFTER V1 data and BEFORE V2 code/execution. V1 remains intact.
The mathematical tools/count law are classical. Specific priority of this
online characterization/application is unconfirmed; no neural benefit yet.

## 1. Local interface avoids cumulative probability products

At each joint live state, obtain each request's CURRENT stop probability p_i
from its ordinary head. Choose a joint Bernoulli stop vector D satisfying:

    marginals: P(D_i=1 | full history)=p_i;
    pairs:     P(D_i=D_j=1 | full history)=p_i p_j;
    orthants:  P(D_i=1 for all i in S | full history)>=product_{i in S}p_i
               for EVERY subset S.

Choose terminal/nonterminal identities with independent private conditional
draws. The model's native per-request kernel must depend only on its own
history; stopped rows are absorbing. Randomness for this joint stop kernel
is fresh at every step. With fewer than3 active rows, use independent stops.

V1's clock copula evaluated at thresholds p_i satisfies these conditions.
Its cut q can now be ANY fresh choice measurable from the full CURRENT
history/heads, and the active cohort size can change. No virtual continuation
of stopped rows, future probability estimate, cumulative survival product,
fixed head or stable logits is needed. This is a DIFFERENT implementation
from V1's single inverse-hazard clock for a whole trajectory.

The moment/checkerboard kernel itself is the SAME classical construction.
This extension concerns the adaptive local interface and its trajectory/
completion guarantee, not invention of limited independence or copulas.

## 2. Full individual and pair trajectory laws

Conditional on the full past, the two stop decisions are independent with
the correct probabilities. Private conditional token draws then make every
pair's NEXT transitions the product of their native individual transitions.
That product depends only on those two individual histories. Induction
therefore gives independent COMPLETE trajectories for each pair, with the
native marginal laws, even though other histories/heads determine q and
the active count. The single-request statement follows by projection.

Every deterministic linear combination of individual scores consequently
has the same mean and variance as independent native runs. No claim is made
for group baselines, pass@K, nonlinear batch metrics, full iid joint laws or
an entire optimizer trajectory. Reusing the joint stop randomness across
steps without the required conditional law is outside this proof.

## 3. Universal maximum-round comparison by backward induction

Fix a deadline and a full joint state. Under independent native continuations,
the probability that all active rows finish by that deadline is the product
of individual finish probabilities. Suppose the coordinator's remaining
completion probability is at least that product at EVERY next joint state.

For row i let R_i in[0,1] be its independent native chance of finishing by
the deadline AFTER a private nonterminal transition. Terminal transitions
finish with certainty. Conditional nonterminal draws are independent, so
the expected independent-continuation product after this step is

    E_D product_i [R_i+(1-R_i)D_i]
      =sum_{S} [product_{i in S}(1-R_i) product_{i notin S}R_i]
                 P(D_i=1 for all i in S)
      >=product_i [R_i+(1-R_i)p_i].

Every coefficient is nonnegative. The right-hand side is precisely the
independent native completion probability from the current state. Combining
with the induction hypothesis proves the same inequality now. The terminal
deadline provides the base case. Thus maximum rounds M are stochastically
no larger than iid, for arbitrary history-dependent individual kernels,
arbitrary head/history-adaptive choices among valid local copulas and active
cohort changes. No future-logit stability assumption is used.

This is a product/Bellman comparison using classical orthant order. It is a
WRITTEN proof, not a priority claim or machine-checked software theorem.

## 4. The orthant condition is also necessary for this universal guarantee

At a current state suppose a subset S has joint stop probability strictly
below the independent product. Choose subsequent native dynamics so that
nonterminal rows in S cannot finish by the chosen deadline, while every
other nonterminal row finishes deterministically at the next step. Then
all rows finish by the deadline iff all rows in S stop NOW. The coordinator
has smaller completion probability than iid. These deterministic future
kernels cannot be corrected by any later coupling.

Therefore local upper-orthant domination of stop indicators is exactly the
condition for a universal one-step completion comparison against every
possible independent continuation. Pairwise independence alone is insufficient;
V1's affine-field adverse witness gives a concrete admissible-pairs failure.
This characterizes the LOCAL universal contract, not every global batch
coupling or a claim to optimal total latency.

## 5. Positive capability and cost scope

The V1 two-point family is implementable by this local coordinator too:
at the first step p_i=1-q, leaving the declared moment-law count of surviving
rows; survivors then have p=0 until a forced stop at H. Its exact expectation
formulas and constant limiting model-round saving apply, while every pair's
full law remains native. This is a constructed capability example, not an
observed real LLM workload or permission to engineer a slow benchmark.

Fixed-shape or affine active-row model cost with nonnegative round overhead
is dominated as in V1. Arbitrary nonlinear compaction costs are not; the
3/2 versus11/8 min(N,2) adverse example remains mandatory. Refillable serving
can remove the relevant tail overhead. All real sampler/model/output/setup/
communication/precision costs must be charged before a practical claim.

## 6. Finite categorical kernel, without trajectory-sized rational products

If a declared native categorical step has integer ticket counts summing to Q,
let p_i=H_i/Q be its terminal-set mass. Choose a rational cut q=L/Q with
0<L<Q. Conditional coarse bins contain Q-L or L uniform integer tickets.
The moment mixture and uniform subset give exact uniform single/pair tickets;
their grid CDF obeys the V1 orthant bound. Compare each ticket to H_i.
Independently sample the identity inside the terminal/nonterminal set using
its exact conditional ticket counts. The resulting per-step individual/pair
categorical law is EXACTLY that declared finite kernel.

The moment-mixture rational denominator has O(B+log K) bits for B=log Q
(constant-factor multiples of B); there is no O(HB) survival product. Uniform
subset selection and unbiased bounded-integer generation still cost work.
No floating residual-clock equality, Torch.multinomial finite-alias equality
or CPU/CUDA bit identity is inferred. Constructing the integer counts from
logits and sampler overhead/quantization require their own prospective audit.

The next gate is only the exact local/adaptive finite oracle in protocol-v2.md.
Native whole-model/engine compatibility, actual benefit and adequate own
priority remain OPEN. V1 sources/data/limits are unchanged.
