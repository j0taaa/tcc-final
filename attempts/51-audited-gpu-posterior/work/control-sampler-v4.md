# V4 — retained-uniform GPU control before implementation

2026-10-16. Same original-word target and actual consumer as README; this is the
mandatory CLASSICAL interval control, not the proposed correction's speed result.
It uses V3's identical class/beta intervals, rescaling and compiled graph.

Refine every global class into disjoint original-ID blocks of at most1024 IDs;
replace its occurrence in an edge with ALL its blocks. No ID/byte/probability is
pruned. This is classical disintegration. Coaccessible deterministic graph arcs
remain unique for every original word. Explicit original fixed rows are one-hot;
initial fixed-canvas restrictions remain part of the graph. Terminal masks
implement the declared EOT/PAD contract, not arbitrary EOS disappearance.

At physical position p in state s, exact edge branch weight is
(sum_(blocks in e) sum_(t in block) w[p,t]) * beta[p+1,target(e)].
The common successor-layer scale cancels from the normalized edge categorical.
Given its selected edge, select a block by its original weight sum; given the
block, select an original ID by w[p,t]. These three conditional categorials
produce P by the ordinary backward/ancestral identity. They need neither exact
conditional marginals nor a new head; model-confidence commitment is separate.

Give EACH (position, edge/block/ID phase) an independent b-bit uniform prefix.
Three phases remain allocated even when a singleton needs no RNG decision.
GPU applies outward CDF comparisons. If a choice is ambiguous, flag the WHOLE
trial for exact fallback and stop its GPU walk; do NOT publish or discard it as
an accepted word. Exact fallback computes original rational inside messages and
replays the ENTIRE trial using the SAME three prefix coordinates at every slot,
revealing extra independent bits only when necessary. Earlier certified choices
match those true inverse-CDF choices. Thus flagging only changes work, not law;
restarting from fresh uniforms on flagged trials would generally be biased.

Every trial eventually returns its exact original word in the unlimited fair-bit
model. Unlike word rejection there is no fixed-trial accept/reject loss here,
but a finite preprocessing/fallback timeout is explicit FAIL and can still
censor the successful-output law (V1 caveat). Admission must prove positive root
mass (e.g. lower>0) or use exact fallback; a zero LOWER bound is not infeasibility.
GPU launch width is limited by all relevant outgoing/block/ID arities; resource
refusals preserve the complete support, never silently reduce it.

Preflight before any performance run: independent exact category-prefix laws,
independent full-word JSON checks, CPU exact retained-prefix replay for EVERY
trial including all ambiguities, fixed original aliases, zero weights and true
termination. All block/class/beta preparation, uniform generation, CPU fallback,
output copying and confidence gathering count in a later complete-cost protocol.
No control timings, new neural heads, priority or useful systems advantage are
asserted by this design.
