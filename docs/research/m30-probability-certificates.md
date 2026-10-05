# Certified probability envelopes for diffusion commitment

## Scope and reason for the extension

The user requested a direction beyond another replay of the same 72 inputs.
M29 remains a separate optimization/computation study. This extension solves a
different deployment problem: obtaining valid structured completions while
knowing how much a truncated/unfinished inference can distort the **frozen
mean-field predictive distribution conditioned on the declared grammar**.
A valid completion alone supplies no such probability guarantee.

This is a proposed incremental synthesis, not a discovery of conditional
sampling, weighted counting, total variation, or deterministic error bounds.
An absolute novelty/real-world accuracy guarantee cannot be inferred from a
literature search. The contribution claimed here is a token-provenance-aware,
ambiguity-independent portable certificate, support-tail accounting, and its
use in finite-slot diffusion sampling/admission with composable error budgets.

## Antecedents checked before new outcomes

- [Amarilli, Monet, Raphaël and Salvati, STACS 2026](https://doi.org/10.4230/LIPIcs.STACS.2026.5):
  probabilistic-language membership is tractable for unambiguous CFLs, but can
  be #P-hard for unions of two unambiguous linear CFLs. We cannot promise an
  efficient exact probability parser for arbitrary ambiguous grammars.
- [Dubray, Schaus and Nijssen, CP 2024](https://doi.org/10.4230/LIPIcs.CP.2024.10):
  deterministic anytime weighted model counting already provides lower/upper
  bounds. Our partition search is a specialization, not a new WMC principle.
- [Renkens et al., AAAI 2014](https://ojs.aaai.org/index.php/AAAI/article/view/9067):
  explanation-based approximate WMC also predates this certificate application.
- [Grammar-Aligned Decoding/ASAp](https://arxiv.org/abs/2405.21047) and
  [CARS](https://arxiv.org/abs/2510.01902) address grammar-conditioned sampling
  and distortion in autoregressive LMs. We do not claim to first notice bias,
  to beat CARS, or to reproduce its exact AR-distribution guarantee.
- [Dang and Ermon, exact DFA inference](https://arxiv.org/abs/2607.07026) and
  [FactorDLM](https://arxiv.org/abs/2609.32900) already condition diffusion
  mean-field predictions exactly in their representations. Those are preferred
  when their exact representation is affordable. Our fallback accepts arbitrary
  finite-slot CFGs without assuming unambiguity or compiling a full DFA.
- EPIC supplies exact feasibility and heuristic commitment, not the mass
  certificate being specified here. This does not establish a faster full
  decoder or higher task accuracy than EPIC.

## Definitions

Use the immutable finite-slot state from M26/M27. For each free slot i, retain
original nonnegative rational token probabilities p_i(t) on declared S_i, with
sum s_i <= 1. Fixed slots instead have their fixed token with probability one:
this conditions on the current canvas rather than counting its original
unconditional probability again. At least one token is represented per row.
Zeros are allowed. These rational numbers define the predictive reference;
they are not claims about the exact real-valued softmax before numerical
rounding. A model adapter must record its normalization and numeric precision.

Let q(y)=product_i p_i(y_i), Omega=product_i S_i, and A be the set of token
sequences satisfying bytes/CFG, fixed positions and EOS/PAD. On the full
unresolved vocabulary there is an unknown mass delta=1-product_i s_i outside
Omega. No claim about the grammaticality of discarded tokens is necessary.

A certificate is a finite **disjoint partition tree** of Omega. A binary split
partitions one row into two nonempty disjoint subsets; all other rows stay
unchanged. Leaves are: a grammar-valid singleton (positive evidence), an
independently certified infeasible box (negative evidence), an exact zero-mass
box, or an unresolved box. For box D, m(D)=product_i sum_{t in D_i} p_i(t).
Let K be the accepted singleton leaves, L=sum_{y in K}q(y), and R the sum of
unresolved box masses. Every infeasible box carries an original-input M27
resource certificate with budget zero and no model rewards. The checker
imports neither optimizer nor search engine.

## Theorem 1: valid-mass envelope, including ambiguity and omitted support

The represented valid mass Z_S lies in [L,L+R]. The full-vocabulary valid
mass Z lies in [L,L+R+delta]. Probability mass is attached to token sequences,
not parse trees. Both statements therefore hold for any CFG ambiguity and for
multiple tokenizations/emission aliases.

**Proof.** Binary splits preserve box union and disjointness. Inducting on the
tree, its leaves partition Omega. Accepted singleton leaves are distinct valid
sequences; invalid leaves contain no valid sequence; zero leaves have no mass.
The valid mass in all remaining leaves is between zero and their total mass R.
Outside Omega, valid mass is between zero and delta. Add these contributions.
No derivation multiplicity enters either sum. □

## Theorem 2: a sharp conditional error certificate

Assume L>0. Sampling Q(y)=q(y)/L on K produces a valid token sequence.
For the represented conditional predictive P_S=q(.|A intersect Omega),
TV(Q,P_S)=1-L/Z_S <= R/(L+R).
For the full-vocabulary conditional predictive P=q(.|A),
TV(Q,P)=1-L/Z <= (R+delta)/(L+R+delta).

**Proof.** On K, P(y)=q(y)/Z <= q(y)/L=Q(y). Its contribution to the
L1 difference is sum_K q(y)(1/L-1/Z)=1-L/Z. Outside K, Q is zero and the
contribution is P(A\K)=1-L/Z. Divide their sum by two. Write Z=L+v,
where 0<=v<=U (U=R or R+delta); v/(L+v) increases with v because L>0.
The upper bound is sharp from the available evidence: let all unknown mass be
valid. Then v=U and equality holds. This is an information bound, not a claim
that every CFG realizes every unknown-mass allocation. □

In particular an exact solution on a severely truncated support can still have
full-vocabulary error arbitrarily close to one. Full-scope sampling must refuse
when only a support-scope tolerance was certified. A zero accepted mass permits
no posterior sampler. Zero represented valid mass does not imply full-vocabulary
infeasibility when delta>0.

## Finite-language coverage refinement (before new model predictions)

For a finite-language grammar, retain a finite set W_A of byte yields for each
nonterminal. Check that every terminal rule's byte belongs to its head's set
and every binary rule closes under concatenation of the two child sets.
Accepted empty output must also be included. Induction on derivations proves
L(G) is contained in W_start, even if the grammar is ambiguous. Independently
enumerate **all** full-vocabulary n-slot tokenizations of these byte strings,
respecting fixed slots (the implementation initially supports ABSENT EOS only).
If every such path uses represented tokens in every row, omitted **valid** mass
is zero. The original discarded mass delta remains visible; it is never
renormalized away. In Theorem 2 replace delta by this proved zero upper bound.

A finite yield closure may be exponentially large or impossible for a productive
recursive language; construction/verification refuses on explicit limits.
Failure to prove coverage leaves the general conservative bound intact. A finite
catalog is a specialization with a cheaper exact solution, not a speed baseline
we expect the generic engine to beat. All six fresh probes will report both the
generic tail bound and the independently checked finite-language refinement.
This refinement was specified before collecting any model probabilities.

## Theorem 3: certified event probabilities and admission

Let a=sum_{y in K, E(y)}q(y). For either reference above and its corresponding U,
P(E) is in [a/(L+U), (a+U)/(L+U)].

**Proof.** Let v<=U be actual unknown valid mass and b<=v its event mass.
P(E)=(a+b)/(L+v). A lower bound places all v=U outside E. An upper bound
places all v=U inside E; its monotonicity follows from a<=L. The bounds are
attained by those two allocations when unconstrained unknown outcomes can
realize them. □

A client can admit sampling at declared TV tolerance epsilon only if the
appropriate bound <=epsilon. It can certify low grammar probability and abstain
if L+R+delta is below a declared minimum. Conditioning itself has
TV(q,q(.|A))=1-Z; hence [1-(L+R+delta),1-L] bounds the unavoidable distortion
relative to the unconditioned mean-field prediction. This is not a probability
of factual correctness and must not appear as a semantic confidence score.

## Theorem 4: arbitrary parallel updates and trajectory error

Apply any common measurable update rule to the sampled completion (including
revealing a chosen subset in parallel, with a rule depending on that sample).
TV of the resulting canvas distributions is no greater than the completion
TV. This follows by taking preimages of events in the event definition of TV.

Suppose, at every accepted step and every possible same-history state, the
approximate transition has TV distance at most epsilon_t from the corresponding
ideal grammar-conditioned mean-field transition. If initial states match,
a T-step trajectory has TV distance at most min(1,sum_t epsilon_t).

**Proof.** Couple the two step distributions maximally whenever histories
match; the next steps disagree with probability at most epsilon_t. Induction
and the union bound give at most sum epsilon_t for any trajectory mismatch.
A deterministic post-processing cannot enlarge the discrepancy. This argument
includes history-dependent model predictions. It does not prove that a model's
mean-field transitions equal its true generative distribution, nor future
trajectory optimality. A tolerance refusal is a separate observable outcome:
silently substituting an uncertified fallback breaks this theorem. □

## Algorithm, work limits and reuse

Maintain a maximum-mass heap of unresolved boxes. A zero box needs no grammar
query. Otherwise a finite CFG oracle either returns a valid witness or reports
infeasibility. For a witness, subtract its singleton with a chain of binary
splits, leaving disjoint first-difference boxes in the heap. Validate the
witness independently. For infeasibility, obtain and check an independent
zero-budget proof. Oracle timeouts leave the box unresolved. Search priorities
can approximate log probabilities; they do not enter the mass proof.

After any finite amount of work, the envelope is sound. Splitting/subtracting a
witness preserves total mass and decreases unresolved mass; removing an invalid
box decreases the upper bound. With finite positive support and exhaustive work,
R reaches zero after at most one oracle query per represented token sequence;
there is no polynomial worst-case promise. Exact rational sums/products can
also be expensive. No hidden pruning or ambiguity assumption is permitted.

If grammar, support rows, fixed slots and token/EOS meaning stay unchanged,
all partition/validity evidence survives arbitrary probability reweighting.
The checker recomputes L,R,delta and the error from new probabilities; old
certified status does **not** automatically survive reweighting.

## Frozen broader application protocol

Collect fresh CPU predictions from official `kuleshov-group/mdlm-owt`, revision
`d0958fa851335ece6c15260ce0025f030673c0fb`, GPT-2 tokenizer at a pinned revision.
The GPU driver is unavailable. Use an explicitly audited CPU attention/rotary
backend port; do not claim bitwise identity with FlashAttention GPU execution.
Full model weights stay in the ignored cache. No generation occurred before
this protocol was written.

Use all six probes: one and two masked token slots for each of (1) the seven
JSON Schema primitive/type names, (2) the eight methods specified by RFC 9110,
(3) a declared package-license policy allowing MIT, Apache-2.0 and BSD-3-Clause.
Prefix/suffix are tokenized separately and kept fixed. Enumerations are declared
application constraints, never hidden answer injections. Include every probe,
including cases with no valid finite-slot completion. No accuracy/population
claim: these are application demonstrations, not a benchmark chosen to beat EPIC.

For each forward retain original logits for all masked slots, normalization,
model/tokenizer/code/config revisions and numeric precision. Generate two
support policies without inspecting outcomes: row-wise top-8 plus all tokens
occurring in an allowed finite-slot catalog completion, and catalog-induced
support alone. Use exact probabilities from normalized binary-rational softmax
outputs; never renormalize the retained rows to conceal omitted mass. Independent
catalog tokenization enumeration on the complete tokenizer is an exact reference
for valid mass and posterior (finite catalogs only), not a general CFG algorithm.
Compare the returned envelopes/TV with it and report full-scope refusals as well
as support-scope certificates. Use requested tolerance 1/20, call limits 1,8,64,
and one exhaustive maximum-4096-query control, with 60-second soft deadlines.
Freeze run configs and committed code before forwards, retain all outcomes and
portable certificates, and generate the report mechanically.

The finite-catalog control is expected to be better than a general CFG search on
this simple application; do not hide that. The mathematical utility is bounded
error and refusal under unfinished or truncated inference, not an invented
speed win over a specialized exact catalog method. Broader recursive-grammar
utility is mathematical scope unless separately demonstrated.
