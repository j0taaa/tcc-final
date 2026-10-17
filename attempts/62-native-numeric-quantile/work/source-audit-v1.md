# V1 — The actual checkpoint is not the paper's abstract codec

2026-10-17. Read-only source audit BEFORE producer, weights or neural execution.

[Public RLM checkpoint](https://huggingface.co/akhauriyash/RLM-GemmaS-Code-v0),
revision0c927733af21f156d61743c4a40d03d13e65c16b. API/card were located/read in
A61. This audit additionally fetched the following TEXT/JSON files only:

| File | Bytes | SHA256 |
| --- | ---: | --- |
| tokenization_p10.py | 19329 | 40f99ebd2ae674d7d58bb25efbabf4c8b285a8843a5861133029595351672c6b |
| configuration_regresslm.py | 6512 | 5a72f125c3d1462f5394fdd0e376ee3ed3ac56b6f5a368585f527a59eab07313 |
| modeling_regresslm.py | 12849 | a082dd3e10fb40ceb96f56e8e887410f947b7d8e578f7a76da2a885e6088558c |
| config.json | 3613 | 56875fa550cb1560e4d7642bcf615c9886b66cd93fc0c7ed1c7f42553025e9c8 |
| generation_config.json | 186 | 586fc33af4352570ac65042951115bef7fa2a4c3d0ff007636636842dd1989e1 |
| ieee_vocab.json | 163 | b79c82d4706d5a199086e5895e4dfb8b8190271e2e2840f4fda02d63675be319 |

Read scopes: complete config/generation/vocab JSON; tokenizer's
token_ids_to_floats/possible_next_token_ids and IEEEFloatTokenizer's conversion/
allowed-token methods; model's numeric helper/logit processor, forward wrapper,
prepare_inputs_for_generation, generation processor override/generate/decode.
The full architecture/configuration Python implementations were NOT audited.
No source module imported, remote-code loader run or third-party code executed.

Concrete findings from these exact files:

* base10, TWO exponent digits, FIVE mantissa digits, nine generated tokens;
  not the three exponent digits in the separately read paper description.
* Numeric decoder IDs0..12: PAD0, signs1/2, digits3..12. Encoder vocabulary
  256000 is different; do not use it as the decoder projection size.
* Sign and exponent-sign positions permit+/-; all later positions permit0..9,
  including the first mantissa digit. No canonical nonzero-leading rule.
* Decoder input begins with PAD0; numeric decoding drops that first ID and
  checks chunks of nine. PAD/EOS0 is not admitted by the per-position numeric
  mask during these nine steps. No arbitrary PAD suffix was forced or removed.
* IEEE conversion divides integer mantissa by10^4, then multiplies by10^e and
  sign using Python arithmetic. This is a binary64 result, not exact decimal
  semantics. All e in[-99,99] and five-digit mantissas stay finite; a nonzero
  minimum around10^-103 is well above binary64 underflow. Signed zero remains.
* The model appends its numeric logits processor AFTER the superclass processor
  list. The card's top-p0.95 example must therefore not be assumed equivalent
  to numeric conditioning before top-p; the installed superclass ordering
  remains to be audited before generation. Default/full-support and card
  sampling are different declared contracts, not interchangeable baselines.
* prepare_inputs_for_generation delegates to the underlying model. Encoder
  reuse and decoder caching are available interfaces, not measured cost savings.

Example to verify with an independent producer AFTER its freeze: decimal words
(e=-1,N=30000) and(e=0,N=3000), with value N*10^(e-4), are both exactly3/10.
The literal native arithmetic predicts0.1*3 versus0.3, which differ by one ULP.
A60's exact-decimal alias sum cannot silently replace this float pushforward.
This is a source-derived semantic expectation, not an executed tokenizer test.

## Antecedents and scope actually checked

[RAIL/MALI](https://arxiv.org/html/2403.04182v2), Sections3.2--3.4 read directly:
Bayes mean/median readouts from samples and cached/batched prefix inference
are established. A62 cannot invent metric-aware numerical decoding or make
sampling repeat the encoder to create a favorable cost comparison.

[Decoding-based Regression](https://arxiv.org/html/2501.19383v2), Section3.2
already read in A61, discusses sampling/point estimators and alternative
query-based readouts. [RLM for Code](https://proceedings.mlr.press/v306/akhauri26b.html)
documents this consumer's sample-median approach; those are author reports,
not an A62 reproduction. Reuse the exact read scopes/PDF hash in A61, not its
oracle evidence. No new paper theorem or priority exclusion is inferred.

[RELISH](https://arxiv.org/html/2604.01206v1) abstract/introduction were read;
full methods/experiments NOT yet read. It is an obligatory direct-head lead
when retraining is allowed, not evidence that A62 outperforms predictive heads.
Regression Transformer/Nature2023's XLNet methodology passage was read via the
publisher result; it already discusses nonautoregressive independence and
numeric tokens. Its full model/evaluation were not re-audited here.

Nearest general algorithms remain classical prefix enumeration, stochastic
CDF estimation and interval branch-and-bound. Searches for numerical quantile
decoding are not a systematic priority review. No implementation, resource
screen, semantic-quality measurement or positive goal completion is supplied.
