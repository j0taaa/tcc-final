# A57 — Conditional moments of structured-policy importance weights

2026-10-16, written BEFORE this direction's arithmetic prototype/readouts.
A52 V18's numeric-gradient gate remains CLOSED NEGATIVE. This is a different
operation: finite-policy-change evaluation on stored visible decoder paths.
There is no new rollout, policy update, head readout or performance result.

1. **Use.** A developer of a frozen-denoiser structured dLLM could compare
   release planners using old expensive verified rollouts. Inputs are each
   sufficient visible state, original head probabilities, retained original
   IDs and two explicitly specified planner parameters. Outputs are observed
   transition likelihood ratios and the EXACT conditional second moments of
   several augmented ratios. This diagnoses avoidable auxiliary noise; it
   does not by itself certify off-policy overlap or improve generated answers.
2. **Difference.** MIPS already proves marginal-importance variance reduction;
   PAPL already marginalizes token-dependent planner proposals. Importance
   sampling, conditional expectation, weighted grammar inference and Renyi
   moments are CLASSICAL. The candidate specialization is a small fixed number
   of ordinary weighted-prefix queries for variable-EOS forced-anchor actions,
   including ID-class controls. Its sufficiency as an original contribution
   and useful full-cost consequence are OPEN, not established by formulas.
3. **Choice.** No extra neural/reward query is needed to compute these local
   moments when the common frozen proposal and old state heads are available.
   Compare latent IS, anchor-only integration, class-path integration, their
   combination, length-only integration and ordinary exact evidence giving the
   SAME visible ratio. Do not claim superiority over ordinary evidence. A
   useful application must survive those controls and the cost of storing or
   recomputing heads, not merely beat noisy full-latent IS.
4. **Proof.** work/theory-v1.md specifies joint laws, three weighted queries,
   terminal factors, partial controls, an adaptive-path corollary and costs.
   It also states the common-support and reward-measurability limitations.
   These are written derivations, not a new inference primitive or priority.
5. **First validation.** Only small independent rational joint enumeration,
   weighted prefix inference, variable EOS, fixed future IDs, original aliases,
   zero weights, state-dependent continuation and a support-change failure.
   No real-head statistics, fresh auxiliaries, fitting, model call or timing
   campaign before a separately source/input-frozen protocol. The old16 paths/
   70 heads are known development, never independent confirmation.
6. **Full cost.** Count old-path capture, all head normalization/class sums,
   gates, anchor sums, every query, memory/IO, verification, model calls and
   policy-selection overhead. Three queries diagnose moments; two suffice for
   the visible ratio. A common proposal cancels its partition, not the work
   required to produce/recover its probabilities. Rational arithmetic can have
   large bit complexity. Floating readouts are not certified finite-RNG laws.
7. **Objections.** This may be only ordinary reweighting of an existing grammar
   circuit and MIPS with a specific action map. Class/length controls may erase
   the noise; visible-path variation may dominate; a close target may barely
   change any weight. Direct rollout/SFT/DR/clipped or self-normalized IS may
   be preferable for the actual application. Hard confidence maps can change
   their preimages with parameters: a naive latent ratio can then be wrong.
8. **Article gap.** A substantive own distinction, useful deployment operation,
   honest finite-policy-change comparison, full cost and independent evidence.
   Passing the mathematical oracle authorizes NONE of those claims. If the
   exact readout is a direct classical composition with no useful difference,
   preserve it as a diagnostic/control and stop before a neural campaign.

The smooth policy here is the declared A52 V7 forced-anchor policy, not the
native Mosaic/EPIC planner. This independent attempt does not restore or alter
the old negative gradient application. No final-text likelihood, semantic
gain, native GPU RNG exactness, publication or achieved user goal is claimed.
