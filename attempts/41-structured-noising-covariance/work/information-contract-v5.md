# Minimal real noising information audit, BEFORE code/model outputs

2026-10-11. Refines criteria1/3/5/6/7/8 of the README. Originality of the
query frontier remains open; this small opt-in probe tests a necessary useful
signal without claiming a new training algorithm or running a huge experiment.

The pinned MDLM checkpoint's own config has time_conditioning=false. Use
the known normalized count-NELBO operation, not a weak uniform-time comparator.
[Zheng et al., current v6](https://arxiv.org/html/2409.02908v6) Sections3.1--3.3,
Propositions3.1/3.2 actually read: count ELBO, Beta mixture and time independence
are direct predecessors. Their count low-discrepancy control remains admissible.

The purpose is to find whether a cheap proxy learned on PAST independent
corruptions predicts a material portion of real count-noising score/bias-gradient
variation on NEW corruptions. Six external JSONs are ALL the old A17 input-ranked
documents, reused only as DEVELOPMENT. The corpus, tokenizer and checkpoint
are pinned; own metadata/loader/config copies and hashes are in origin-v5.json.
No mutable A17 code or past neural outputs are imported. No golds/grammar
answers choose masks, classes, documents or positive outcomes.

Fitting32 old-noise observations costs32 CURRENT full model forwards per
document. It is charged, not called free teacher information. On64 fresh iid
original source indices compute normalized count-NELBO and the entire output
BIAS gradient (all original vocab coordinates). This is not the backbone,
full head-weight gradient, a parameter update or a complete training result.
The evaluator excludes only the original MASK class as in SUBS; no top-K or
vocabulary truncation. Role features come from the complete valid JSON, not
newly manufactured benchmark outputs. Classifier is fixed before eval sources.

Ridge and four-center classification are KNOWN proxy tools. Their use cannot
create novelty automatically. Full source law/covariance theory does not require
proxy accuracy. Actual utility does: an uninformative classifier costs extra
work and can lose against inexpensive known controls. Every doc, class count,
positive/negative fit result, call count and physical cost is preserved.

An exact64-source-bank covariance calculation can audit observed geometry.
That bank makes all class masses/labels cheaply available, so analytical
inverse/optimal controls are legitimate. It is NOT an opaque-source practical
victory, an unbiased estimate of the infinite-source improvement, or a
performance gate. A separate honest complete-cost protocol is required if
the information audit is promising; no independent test is silently triggered.
The already-known count/Rao-Blackwell/CV/importance/RSS/pivotal alternatives
must not be handicapped later. Main article and maintained APIs stay intact.
