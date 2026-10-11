# Third-party notices

The maintained parent-project notice inventory is [LICENSES.md](LICENSES.md).
EPIC's original notices remain at
[vendor/EPIC-Decoding/THIRD_PARTY_LICENSES.md](vendor/EPIC-Decoding/THIRD_PARTY_LICENSES.md)
and its license remains unchanged. New optional MDLM CPU measurements use
hash-pinned upstream Apache-2.0 source/weights in an ignored local cache;
that license continues to apply. The parent MIT license covers original project
code, not the upstream model or baseline.

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
