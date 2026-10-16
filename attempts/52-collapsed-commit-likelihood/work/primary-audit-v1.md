# Primary audit before an A52 prototype

Read 2026-10-16. No new model head, update, timing or human review. Source
PDFs were retrieved into ignored .cache/a52-primary and hashed; the scopes
below are narrower than the complete papers. Searches do not prove absence
of earlier work. Primary citations rather than automated paper reviews ground
the comparison.

| Source / exact PDF SHA-256 | Actual relevant scope and boundary |
| --- | --- |
| [DUEL v1](https://arxiv.org/pdf/2603.01367v1), 64bee7c83b71bc29a98d0964ba44ddda5f5cab915dd075f3644225dcd676d950 | Sections3–4 and Algorithm1/2: positions are a deterministic function of the current partial state/network predictions, chosen BEFORE token sampling. Its confidence uses maximum token probability. A52 does not allege an error in that contract; sampled-token confidence defines a different, random observed mask. |
| [MAPG v1](https://arxiv.org/pdf/2607.15200v1), 2be882b200e456ee6f250fc5362d6ad63e3d84e3474ae4709079a79c10e1d811 | Sections2–3, Eq9 and the displayed two-stage action: the token and position decisions both matter; the differentiable selection is PL. This is a direct antecedent for optimizing masking. A52's deterministic-confidence preimage formula neither invents that objective nor supplies the PL conditional law. |
| [d2 v4](https://arxiv.org/pdf/2509.21474v4), a2dcf1fa704e0a1fddc23297ebde5edcf7ce0c706e68cc220b641e05a24b3e46 | Abstract and Section3 outline: exact AnyOrder and approximate StepMerge are already trajectory methods. No claim that exact path likelihood is new. The paper's entire proofs/experiments have NOT been reread in this audit. |
| [EGSPO v2](https://arxiv.org/pdf/2603.12554v2), 2091bcdd93d1d9fcc0a95a01f92f75799dccac772e5648daf5bcbb48ae9baa77 | Section4.1/Remarks2–3: exact MDP gradient and per-step baselines are antecedents; practical confidence rule uses per-position maxima and freezes selected positions. This must not be silently equated to selecting by newly sampled-token confidence. No criticism of its empirical results is inferred. |
| [CoDD v3](https://arxiv.org/pdf/2603.00045v3), 7e372a9a1ffb5bd5acd9382c8d28a2d7bc5abd4cd2e24e2911674236c8c815f6 | Sections3–5/6.2 and the dynamic-prior discussion: tractable correlated inference layers, frozen-backbone PC training and HMM priors are direct antecedents. Merely adding a joint mixture/prior is rejected as a new central idea. Temperature difficulty is for its general latent mixture; deterministic circuit powers are not a new solution. |
| [Di4C v4](https://arxiv.org/pdf/2410.08709v4), 257e4bafcce658a7af82081b48d8f88324b1b0cdf5982cad027e4b4bbf4c2461 | Section3.1–3.3, Proposition1 and selected implementation paragraphs: product mixtures/distillation already address dimensional dependence. No new latent-head or generic distillation prototype is justified by renaming those mechanisms. |

## Existing native consumer

[Mosaic](https://github.com/MhDang/mosaic), immutable commit
36945e4b3c64913e23962e0924a8b40a84c58807, MIT. Read
mosaic/dlm/llada2.py and integrations/sglang/mosaic_low_confidence.py's
proposal/commit section: joint proposal then gather ORIGINAL model probability
at its sampled ID, STRICT confidence>threshold, first-index argmax fallback.
Constrained marginals are an optional different confidence readout. Native
temperature0 uses a maximizer, not the positive-temperature law assumed in A52.
The theorem covers the ideal normalized product posterior, not automatically
the rounded native GPU distribution. llada.py uses torch.topk; its tie behavior
must not be described as a stable physical-index convention without validation.

## Other objections already identified, before implementation

Weighted evidence queries and conditional-score/Rao–Blackwell identities are
classical, and the maintained CFG backend already offers restricted partition
operations. A52's unary-filter reduction may therefore be a direct application
too small for a paper. The checksum variance comparison only separates it from
the specified full-proposal estimator, not all competent analytic controls.

Expensive-verification application of A38 is NOT launched: an unbiased mean
need not preserve every raw output marginal, so weighted stratification,
prediction-powered/control-variate evaluation and cache-aware labels are strong
controls. No measured verifier/generation cost ratio or useful cheap semantic
signal has been established. A new expensive SWE-bench campaign is unwarranted
on the current evidence. This refusal is separate from A38's earlier pilot.

The investigation proceeds only to a small rational counterexample/correctness
oracle for the new observed-action operation. Useful neural cost/variance,
specific priority and publication sufficiency are still OPEN.
