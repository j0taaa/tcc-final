# A65 — Terminal readout for an actual typed forecasting consumer

2026-10-17. Eight criteria BEFORE implementation, new model outputs, corpus
rows, golds or timings. This starts from Mosaic's published JevBench consumer,
not a new abstract coupling, another A63 cap or a reopened failed gradient case.

1. **Real operation.** Mosaic36945e4b already sends DiffusionGemma through
   vLLM and returns JSON probabilities to JevBench. The consumer scores the
   numerical vector, not its exact spelling. Its final canvas commit has
   residual state-path randomness. Investigate numerical aggregation of THAT
   terminal transition, after an unchanged original trace, reusing its frozen
   sampler inputs and adding no backbone forward. Post-normalization is an
   obligatory baseline. No actual model/readout benefit is established yet.
2. **Own candidate.** A specific engine-boundary readout with terminal-event
   conditioning, original token/alias/termination semantics and full-cost
   integration. Averaging, Rao--Blackwell, MBR, Jensen, normalization and moment
   DPs are CLASSICAL. RAIL2024 and probability-logprob averaging2025 are close
   predecessors. Sufficient own originality/significance is OPEN; a new name
   for sample means or their variance formula would not be a contribution.
3. **Choice.** The proposed readout has a written all-gold convex-risk guarantee
   versus ONE normalized draw of the SAME terminal native kernel, and a sharp
   squared-risk improvement in terms of its conditional variance. Helpers use
   no extra model forwards, but may be expensive. Full-trace ensembles, exact
   small-grid semantic DP, native sampling/MAP, normalization and mean-token
   shortcuts remain controls. No superiority to those methods presumed.
4. **Proof first.** Work/theory-v1.md defines the actual absorbed transition,
   finite helper budget including nonterminal returns, mean/risk/cost identity,
   rendering error and a whole-trace corollary BEFORE a reference. It does NOT
   equate the original head product with the native marginal-reprojection law.
5. **Validation.** First only independent finite rational oracles for terminal
   conditioning, aliases/zero sums and whole absorbing traces, plus a source
   boundary audit. Then a separately frozen native replay/resource protocol
   before any new forward or semantic observation. A necessity screen must
   measure the removable variance and complete cost BEFORE a large campaign.
   No threshold or selected favorable data is manufactured in this first note.
6. **Full costs.** Preserve original backbone calls/trace, but charge frozen
   sampler capture, copies, dense memory, all helpers including incomplete
   proposals, parsing/normalization, exact/float arithmetic and serialization.
   The primary implementation may retain dense last-head inputs; no claimed
   neural memory saving. Native RNG/control/canvas snapshots must be complete.
7. **Fatal objections.** Last-step variance may be negligible because the model
   has converged. Whole-trace uncertainty is NOT integrated. Native temperature
   zero still samples paths; assuming deterministic/MAP or plain mean-field
   changes the target. Two-decimal numbers make ordinary integer-sum DP a
   strong exact control; a Laplace or general-precision advantage is unnecessary
   here. Larger model ensembles can improve between-trace uncertainty. The
   reported native26B/48GB setup is not reproduced on the local12GB GPU.
8. **Article.** Need a surviving own engine/application difference, native
   correctness and meaningful independent risk/cost improvement, not just the
   known theorem or a small reference. Accuracy/ECE/Capability do NOT follow
   from convex-risk domination. No model training, sufficient priority, human
   review, publication/admission guarantee or achieved goal is asserted.

Read [actual source and primary scopes](work/source-audit-v1.md) and
[written operation/proof](work/theory-v1.md). External sources are copied
immutably for inspection; no third-party module, model, dataset row or result
file was executed/read. Aggregate README results HAVE been seen and must be
disclosed in any future protocol. All earlier failed branches remain closed.
