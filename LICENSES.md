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

The pinned EPIC code is not copied into the parent repository; it is referenced as the submodule `vendor/EPIC-Decoding` and remains governed by its own `LICENSE` and `THIRD_PARTY_LICENSES.md` files. Do not remove or rewrite those notices.

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
