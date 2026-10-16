# Strong CPU/GPU controls: symbolic compilation and compatible-canvas reuse

Written after the V3 known-data screen, BEFORE the corresponding code or a
new speed/quality campaign. These are classical compiler/DP optimizations,
supplied equally to candidates and controls, not new scientific contributions.
The eight questions/objections in consumer-v3-contract.md still apply. V4
investigates A24's same structural certificate in the existing joint-sample
consumer; it must beat competent controls after these costs are reduced.

## Direct integer inference on the symbolic graph

V3's native GPU control receives a minimized original-ID graph. A competent
CPU control need not minimize it or expand class labels into original IDs.
An edge labeled a union of WHOLE global/refined classes has exact weight
equal to their row sums. Expose that symbolic graph as a layered deterministic
DAG with one group per outgoing edge. At fixed positions, the edge is enabled
iff it contains the fixed original ID. Backward trimming is language-only.

The existing integer StackPosterior then sums precisely the same original
words, because graph determinism gives one path per word. Its exact class/
block sampler and sparse confidence operations retain the same law. When
the legacy sampler requests actual members, present a lazy sequence of the
original IDs in those classes, never the class indices themselves. Its
iteration/index order need not match another implementation's RNG path;
the original word law is unchanged. No N×V member list is constructed just
to compute inside probabilities. Pay for all actually requested IDs.

This construction is particularly necessary for the EXACT unbounded CPU
control: V3's full graph minimization cost is not evidence that a CPU inside
algorithm must pay that cost. All full/unbounded and bounded methods receive
this interface before a positive timing claim.

## Cache ONLY the weight-independent compilation

Let c be the initial canvas. A later c' is compatible iff every original ID
fixed by c is still fixed to that SAME ID, and c' only adds fixed positions.
A graph compiled for J_d (or terminated T_d) under c recognizes exactly the
same target under c' after singleton filtering. Every word compatible with
c' was compatible with c; its own completion prevented its removal by the
initial language-only trimming. Conversely, no surviving transition changes
its real parser/termination meaning. Additional trimming is optional.

Therefore cache the compiled DAG/automaton/partition by initial canvas,
grammar, bytes, depth and termination contract. For EVERY fresh head/canvas,
rebuild numerical row sums, inside values and any outside/sampling caches.
Never reuse an old posterior's beta, marginal factors or token CDF after a
head change. All samplers receive the same new original weights and fixed
IDs. A changed/released old fixed ID or expanded byte contract recompiles.

For the first-overflow certificate one may retain the initial untrimmed
prefix DAG and its necessary suffix/lexical supersets. With c' singleton
rows, paths inconsistent with c' have zero weight. Its initial suffix bounds
remain necessary but may be loose. Every true deep completion compatible
with c' still has a first-overflow path in that initial DAG. Its mass-one
continuation gives a valid grammar-hit upper; continuing with the initial
counter supersets gives a valid handoff upper. Computing them does not use
the surrogate shallow mass as a denominator. A missing future path cannot
be inferred from a model weight of zero, so trimming stays language-only.

This extends the written proof's reuse contract; it does not silently relax
the historical OverflowFrontier API check. A new adapter must explicitly
declare the compatible current canvas while preserving the original prefix
language/suffix supersets. Test new fixed aliases and changing row weights
against recompilation/enumeration before timing it.

## Common ranking policy for an eventual native consumer

Mosaic's LLaDA loop may commit the k largest constrained confidences among
currently free positions. To compare approximate proposals to a FULL target
decoder, use the same deterministic ranking map of the sampled word in both.
If the tail bound is U and a queried original-ID numerator is a over shallow
mass L (all in common integer units), its true marginal is in

    [ a/(L+U), (a+U)/(L+U) ].

For a proposed set S of k positions, certify its selection only when every
selected lower endpoint exceeds every unselected upper endpoint. Where
endpoints tie, the fixed deterministic tie rule can additionally certify
only the comparisons it implies. Otherwise refine the confidence calculation
WITHOUT resampling the already drawn original word; exact fallback resolves
ties. The sample's support is nested, so it remains a valid word at deeper
levels. The resulting commit map equals the full decoder's map on that word.
The sampling error charged is ALWAYS the bound at the ORIGINAL draw depth.
A later confidence refinement does not change that draw's law or retrospectively
reduce its TV charge, even if its new confidence interval is much tighter.

The existing common-policy coupling then applies with the per-step structural
TV budgets. Ranking by an unverified approximate point estimate alone does
not have that guarantee. Nor does the argument certify Mosaic's IEEE draws:
the integer backend is exact on its bounded target, native float controls
retain their disclosed rounded law. Finite resource/timeout FAIL outcomes
are explicit; conditioning on successful managed requests may bias outputs.
No semantic gain or finite-resource unconditional TV claim is inferred.

## Next decision

V3's known-data resource gate passes14/15 but is NOT a timing gate. Before
fresh model work, freeze a complete-cost development comparison with direct
symbolic CPU controls, compatible caches, the five native GPU configurations,
grammar-hit/closure/handoff and compact full CFG where applicable. Select a
candidate only on known development; independently selected external inputs
and a native model/termination protocol must be fixed before confirmation.
Use the upstream Torch2.13 environment as well as the explicitly older port.
Originality must be judged for A24's specific certificate/application, not
these compiler improvements or a comparison against needlessly slow controls.
