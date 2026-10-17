# V2 — Final numerical-training antecedents and pinned consumer source audit

2026-10-17, AFTER V1 correctness execution. No exhaustive priority review.
The initial scopes/hashes in primary-reading-v1.md remain historical.

* [GenRe2, FINAL ICML2026](https://proceedings.mlr.press/v306/chen26ec.html):
  original official PDF, Sections3.2/3.3/3.5,4.2 and AppendixG's reward/evaluation
  paragraphs read as extracted text. It combines sequence-level numerical
  rewards with on-policy expert-token distillation; code targets use quantile
  transformation and clipped rewards. This is a direct mandatory training
  control. The earlier [arXivV1](https://arxiv.org/html/2512.06533v1) Sections3.3/
  4.2 were ALSO read, but lack that final OPD method; do not conflate versions.
  No reproduction or independent validation of the paper's results is claimed.
* [Decoding-based Regression](https://arxiv.org/html/2501.19383v2): Sections3.1/
  3.2/3.3 and Appendix's MDN/codec tuning paragraphs read directly. It already
  uses scientific numerical codecs, CE and distributional prediction. Strong
  mixture-density heads and carefully tuned decoding heads are mandatory;
  a weak MSE-only baseline is inadequate. Full proofs were not reverified.
* [TabDLM](https://arxiv.org/html/2602.22586v1): Sections2.2--2.5 read directly.
  It combines continuous numerical diffusion with masked text diffusion,
  numerical encoder/decoder modules and LoRA. The operation differs from exact
  native textual-value semantics, but rules out claiming that joint numerical
  and language diffusion itself is new. No result reproduced here.
* [ICF-DLM](https://arxiv.org/html/2609.07756v1): Sections3.1--3.2.3 and4.1.2
  read directly. Its numeric tokens and PPO rewards for complete physical
  descriptors predate this candidate. Not a read/audit of every experiment,
  dataset release or physical claim; no priority exclusion is inferred.
* [Bolin/Wallin](https://arxiv.org/html/1912.05642v3): Section4/Corollary1 and
  Section5/Theorems3/5 and Proposition5 read directly, not full appendices.
  Robust and scale-normalized proper kernel scores are established. Local scale
  invariance is their stated property and is not identical to V1's decimal
  relabeling invariance. Do not advertise generic robust/scale-aware proper
  scores as our invention. An epidemiological transformed-score article was
  located but its PMC open hit a CAPTCHA; its full method is NOT counted read.

Final GenRe2 PDF:1209876 bytes, SHA256
27fa1f292a210d116d1448e0ad2217c52d7991a358b5871dc0c712a878979b4c,
official URL https://raw.githubusercontent.com/mlresearch/v306/main/assets/chen26ec/chen26ec.pdf.
Cached outside the repository in the A61 primary-reading cache; original PDF
is not redistributed in the snapshot. Extracted text read, not visual figures.

## Author source, public availability and exact reading scope

[RegressLM](https://github.com/google-deepmind/regress-lm) pin
bf3c947309cb11c4b1d1b2667237cd73c7d0667d, shallow no-checkout source cache.
Read README, tokenizers.py's complete P10Tokenizer/IEEEFloatTokenizer classes,
and triton_demo.ipynb CODE CELLS. Notebook outputs were not read or executed.
vocabs.py was fetched/hash recorded; its full implementation was NOT read.
No package dependency, notebook, checkpoint or remote-code loader executed.

* tokenizers.py SHA256011aa862fb38f86fc0dc05fff1182eaa49f5ec12a98c537ed1a8977fb7b6fa34.
* vocabs.py SHA256cbc0678988e730d033972a4f331733a9131ae7ddeea05d5bd210c940a994f27d.
* colabs/triton_demo.ipynb SHA256d4cc9d8b42666574ca8a2316585c9305333ca3a0640b80f4cc201d705fca9f62.

IEEE allowed digits include leading0, so raw exponent tokens are not always
semantic decimal-order categories. P10 places its exponent at the END. These
facts matter to any claimed native-codec reduction. No tokenizer behavior was
silently patched, and no native product-law compatibility is asserted.

The notebook identifies makora-ai/triton-gpu-latency and Srizzle/triton-demo.
The latter checkpoint was only located, not inspected/downloaded. Read-only
Hugging Face API metadata then pinned these public resources BEFORE any row:

| Resource | Revision | Downloaded/read scope |
| --- | --- | --- |
| [Makora dataset](https://huggingface.co/datasets/makora-ai/triton-gpu-latency) | 3b30911350fa433e1cb97ec2a41bd8908dd35d5d | API metadata and complete README |
| [Code-Regression](https://huggingface.co/datasets/akhauriyash/Code-Regression) | c761060000167f2f3ef64a428c224928316dca14 | API metadata and complete README |
| [RLM checkpoint](https://huggingface.co/akhauriyash/RLM-GemmaS-Code-v0) | 0c927733af21f156d61743c4a40d03d13e65c16b | API metadata and complete README |

Public/non-gated file listings were observed; actual weight/data access and
execution were not tested. No Parquet or model weights downloaded. README
aggregate target statistics HAVE been read, so no future experiment may claim
complete blindness to them. No per-row label, evaluated response or prediction
was obtained. Readme usage code was inspected as text, never executed (including
its unsafe eval example). Metadata/card hashes are in evidence/v1/consumer.json.

Makora's card explicitly warns units/hardware/harness are unspecified and that
comparisons should be within problem. Code-Regression's card includes actual
profiled metrics and training-source links, with no predefined independent
split established by this audit. Its example also uses a target key different
from the documented val_accuracy schema; do not execute it unverified. These
are feasibility/provenance findings, not a scientific performance result.
