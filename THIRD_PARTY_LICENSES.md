# Third-party notices

The maintained parent-project notice inventory is [LICENSES.md](LICENSES.md).
EPIC's original notices remain at
[vendor/EPIC-Decoding/THIRD_PARTY_LICENSES.md](vendor/EPIC-Decoding/THIRD_PARTY_LICENSES.md)
and its license remains unchanged. New optional MDLM CPU measurements use
hash-pinned upstream Apache-2.0 source/weights in an ignored local cache;
that license continues to apply. The parent MIT license covers original project
code, not the upstream model or baseline.

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
