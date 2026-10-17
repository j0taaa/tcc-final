# A58 — A streamed training head for grammar losses

2026-10-16. WRITTEN BEFORE this direction's prototype, kernels or measurements.
A28's inference gate, A36's simple sparse-head refusal, A44's gradient-variance
gate and A52 V18's numeric-gradient gate remain CLOSED. This is a different
operation: computing an existing loss AND its full neural-head derivatives.

1. **Real operation.** Train/fine-tune a masked denoiser with token CE plus
   weighted grammatical semantic loss, -log probability of a valid completion
   under its independent predictions. Users consume the scalar loss and exact
   mathematical gradients for hidden states and the ORIGINAL classifier IDs.
   The regularizer is known; its quality benefit is not assumed. The potential
   improvement is the memory/throughput of the SAME training operation.
2. **Candidate systems distinction.** One indirect, class-segmented projection
   produces class log-sum-exp statistics and target logits; grammar inference
   supplies class adjoints; a tiled recomputation contracts them into hidden/
   classifier gradients. No dense position-by-vocabulary activation or copied
   reordered classifier is required. CCE, online LSE, checkpointing, CRF
   gradients, semantic loss and lexical quotienting are ANTECEDENTS. The own
   candidate is a useful grouped execution/data-flow specialization, not a new
   differentiation theorem. Sufficient systems distinction remains unproved.
3. **Why choose it.** Potentially preserve the objective with less workspace
   than dense logits and less overhead than many class-specific CCE calls or
   a checkpointed projection/scatter loop. Those last controls can MATCH its
   asymptotic memory and MUST be provided. No win is presently measured. A
   mere memory comparison with a needlessly materialized dense head is not
   enough to meet the user's goal.
4. **Proof first.** work/theory-v1.md derives forward sufficiency, arbitrary
   class-adjoint backward, original-ID gradients and variable-prefix occupancy
   correction. Full vocabulary normalizers do NOT generally cancel at variable
   EOS. Written cost bounds count gradient/model storage and tile padding.
5. **First validation.** Small rational derivative oracles and dense CPU
   autodiff checks, including variable EOS, fixed future IDs, aliases, zero
   supports and an explicit wrong-gradient counterexample. No real head,
   backbone, optimizer update, GPU timing or fresh data before its own frozen
   source/input/resource protocol. Toy success is not a performance gate.
6. **Complete costs.** Include tokenizer/class compilation and metadata,
   indirect loads, every projection/recomputation/reduction, grammar inside/
   outside, gradient initialization/contraction, optimizer, backbone, memory
   traffic, synchronization, precision and cold compilation. dW of size V*D
   is unavoidable for full-head training. Tied input embeddings add their
   ordinary input-branch gradient. Never claim all model memory disappears.
7. **Main objections.** This may be just segmented CCE. Generic ragged/grouped
   kernels or a few large classes plus batched tiny classes may match it.
   Padding, random weight gathers, atomics, graph inference and backbone
   activations may dominate. A modified loss need not improve downstream
   answers. Disabling gradient filtering is mandatory for an equivalence
   comparison; arbitrary class adjoints invalidate CE-tail assumptions.
8. **Article gaps.** An actual own kernel/architecture distinction and useful
   complete training-step benefit against equally optimized controls, numerical
   accuracy, a real dLLM integration and independent evaluation. No new loss,
   sampling law, parsing theorem, trained dJev or accepted publication is
   claimed. If only the classical algebra survives, keep it as a control and
   stop before a broad model campaign.

This direction does not retain A28's already-materialized GPU logits and call
that model-memory savings. It also does not project only grammar-valid IDs:
mass regularization and variable EOS require the original row normalizers.
Do not transfer timings, neural updates or claims between these attempts.
