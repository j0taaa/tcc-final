# Licenses and attribution

## Parent repository

Except for the exclusions below, the original software, tests, configurations,
technical documentation, versioned research evidence, and generated research
artifacts in this parent repository are Copyright (c) 2026 Gabriel Jota
Lizardo and are licensed under the MIT License in [`LICENSE`](LICENSE).

The scholarly manuscript prose and authored article content under `paper/`
remain Copyright (c) 2026 Gabriel Jota Lizardo, all rights reserved, unless an
institutional deposit or later explicit notice applies different publication
terms. The MIT License does apply to the project-authored scripts and generated
research artifacts used to reproduce the article, including files under
`paper/generated/`.

This license does not grant rights to external model weights, tokenizers,
datasets, trademarks, or other dependencies that are not distributed as
original parent-repository material.

## Third-party material

The pinned EPIC production snapshot is versioned under `vendor/EPIC-Decoding` and remains governed by its own `LICENSE` and `THIRD_PARTY_LICENSES.md` files. Do not remove or rewrite those notices.

Any other file that carries its own license notice remains governed by that
notice. The parent MIT License does not replace third-party terms.

The production parser uses pinned `num-bigint` 0.4.6 and `num-traits` 0.2.19
for exact ordering and rounding of binary64 weight sums. Both are licensed
`MIT OR Apache-2.0`; their upstream notices remain authoritative. Their exact
transitive resolutions and checksums are recorded in both Rust lockfiles.

The eight BFCL examples and acceptable answers embedded in
`configs/experiments/m24_bfcl_enum_pilot_v1.json` and derived M24 archives are
third-party dataset excerpts from the Berkeley/Gorilla project, repository
`ShishirPatil/gorilla`, commit `6ea57973c7a6097fd7c5915698c54c17c5b1b6c8`.
Upstream `berkeley-function-call-leaderboard/bfcl_eval/data/README.md` declares
the data Apache-2.0. Source files and hashes are recorded in
`docs/evidence/m24-bfcl-coverage.json`; these data are excluded from the parent
MIT grant. Question/schema/answer fields were regrouped into the experiment
config. Apache-2.0 license text is available in the preserved
`vendor/EPIC-Decoding/regex-dfa/LICENSE-APACHE`.

The 68 scalar-query examples embedded in `configs/experiments/m25_grounded_*`
and derived M25 archives have the same BFCL source revision and Apache-2.0
attribution. `docs/evidence/m25-grounding-coverage.json` records the question and
answer file hashes. Their fields are regrouped, and query-derived finite domains
are generated locally; the original dataset excerpts remain outside the parent
MIT grant.


Recorded public geocoding responses under `docs/artifacts/demo/` are third-party
service data, outside the parent MIT grant. Each record retains its retrieval
date, source URL and attribution to Open-Meteo and GeoNames. Service documentation:
https://open-meteo.com/en/docs/geocoding-api; location source:
https://www.geonames.org/. No model weights are included.

## Fresh MDLM CPU probes (M30)

The model architecture/checkpoint is downloaded from the official
[kuleshov-group/mdlm-owt](https://huggingface.co/kuleshov-group/mdlm-owt),
revision `d0958fa851335ece6c15260ce0025f030673c0fb`, under Apache-2.0.
The upstream [MDLM repository](https://github.com/kuleshov-group/mdlm) and its
license govern the cached source and weights. They are not copied into Git or
redistributed with the package. `scripts/exact_commit/mdlm_cpu.py` records and
checks upstream hashes and provides native CPU attention/rotary/reshape kernels;
it does not replace the upstream license or claim a bitwise FlashAttention port.
The official GPT-2 tokenizer revision is recorded in both M30 configs.
Only newly measured outputs, probabilities and portable project certificates
are versioned as scientific evidence. No downloaded weights are distributed.

## Additional third-party material

The optional A24 V3 kernel comparator loads unchanged MIT-licensed
[Mosaic](https://github.com/MhDang/mosaic) commit
`36945e4b3c64913e23962e0924a8b40a84c58807` from an ignored local checkout.
The license is preserved in
`attempts/24-certified-depth-approximation/work/evidence/consumer-v3-preflight-v1/Mosaic-LICENSE`.
Its imported sources are checked against that Git object; no model is bundled.
The local Torch2.8 preflight is not the project's full native serving stack.

M34's small external conformance corpus is from
[JSONTestSuite](https://github.com/nst/JSONTestSuite), commit
`1ef36fa01286573e846ac449e8683f8833c5b26a`, by Nicolas Seriot and contributors,
under MIT. Its original license is retained at
`tests/data/json_suite/LICENSE`; the manifest records original hashes and the
predeclared size exclusions. These are external test inputs, not original code.


BFCL/Gorilla public function-call input excerpts in
`attempts/31-sufficient-state-coupling/work/external-inputs-v3.json`:
Apache License2.0, upstream commit6ea57973c7a6097fd7c5915698c54c17c5b1b6c8.
Source:https://github.com/ShishirPatil/gorilla; original license preserved at
`attempts/31-sufficient-state-coupling/work/third_party/BFCL-LICENSE`.
The external checker is downloaded separately into cache, pinned by SHA;
our adapter keeps original function bodies and uses Python-only registry.
No model weights are distributed.

GSM8K question excerpts in
`attempts/32-native-oracle-antithetics/work/gsm-inputs-v4.json`:
MIT, original OpenAI grade-school-math commit
`3101c7d5072418e28b9008a6636bde82a006892c`.
Source: https://github.com/openai/grade-school-math; unmodified license retained
at `attempts/32-native-oracle-antithetics/work/GSM8K-LICENSE.txt`.
The combined upstream files contain annotations; question-only selection
ignores answers and is declared separately from evaluation. No claim of
newly authored or previously unseen model-training questions is made.

A70 V4 preserves unmodified NNCPv2 model/coder source components from
Fabrice Bellard's original2021-02-06-1 archive (SHA256
ced40f3cee1cb2948a5465ead64dffa2614c54abe0ed12fdce084f5c63c29fb1),
https://bellard.org/nncp/nncp_v2-2021-02-06-1.tar.gz . Original attribution,
Apache-2.0 and arithmetic-coder MIT/public-domain provenance are retained in
`attempts/70-native-adam-erasure/work/consumer_v4/{NOTICE.md,provenance.json,
Apache-2.0.txt,MIT-Nayuki.txt,readme.txt}`. They are third-party sources, not
original project code. Only a declared CPU/FP32 component resource screen
is authorized here; no published GPU/Apex result or LibNC binary is bundled.
