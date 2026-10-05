# Certified grammar-conditioned updates from fresh MDLM predictions

Independent original-input/logit, complete-grid and portable-certificate audit: **PASS**.

12 fresh CPU canvases, 192 repeated-measure evaluations, 192 independently checked proofs. Every outcome is retained.

## Concrete use and mathematical guarantee

A consumer selects a maximum tolerated distributional error. The certificate either authorizes a valid parallel update or refuses it, rather than silently renormalizing top-K predictions. The reference is the frozen product of original per-slot predictions conditioned on the declared grammar and fixed canvas. It is not the model's full generative joint or semantic accuracy.

Disjoint token boxes yield valid-mass bounds [L,L+U] and TV <= U/(L+U). Ambiguous parses and token aliases cannot duplicate mass. Original omitted mass remains recorded. Closed-yield or terminal-alphabet proofs can establish zero valid omitted mass independently of its size. Lean checks partition, conditional-error algebra and CFG coverage; the full coupling argument and scope are in `docs/research/m30-probability-certificates.md`.

## All admission outcomes

| Coverage mode | Certified | Incomplete/refused | Zero on support | Timeout | Error |
|---|---:|---:|---:|---:|---:|
| finite_language_coverage | 33 | 15 | 0 | 0 | 0 |
| generic_tail | 0 | 72 | 24 | 0 | 0 |
| terminal_alphabet_coverage | 18 | 6 | 24 | 0 | 0 |

## Every new canvas at 64 calls (top-8 plus declared coverage support)

| Canvas | Valid token paths | Full valid mass | Original omitted mass | Expected rejection draws | Generic TV bound | Coverage TV bound | True TV | Sample/update |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| http_method-1 | 4 | 0.0358092 | 0.0999293 | 27.9258 | 0.73619 | 0 | 0 | `{"method":"POST","path":"/status"}` |
| http_method-2 | 10 | 3.31686e-08 | 0.656995 | 3.0149e+07 | 1 | 0 | 0 | `{"method":"PUT","path":"/status"}` |
| json_schema_type-1 | 6 | 0.00416255 | 0.592686 | 240.237 | 0.993026 | 0 | 0 | `{"type":"object"}` |
| json_schema_type-2 | 16 | 1.21528e-06 | 0.897876 | 822859 | 0.999999 | 0.0302623 | 7.72844e-07 | `{"type":"string"}` |
| one_child_arrays_depth1-1 | 1 | 0.19422 | 0.0278316 | 5.1488 | 0.125338 | 0 | 0 | `[]` |
| one_child_arrays_depth1-2 | 2 | 0.0132747 | 0.0370473 | 75.3311 | 0.736204 | 0.000182729 | 0 | `[[]]` |
| one_child_arrays_depth3-1 | 0 | 0 | 0.0659476 | -- | -- | -- | -- | `None` |
| one_child_arrays_depth3-2 | 2 | 0.0833926 | 0.373054 | 11.9915 | 0.8173 | 0 | 0 | `[[[]]]` |
| one_child_arrays_depth8-1 | 0 | 0 | 0.00135115 | -- | -- | -- | -- | `None` |
| one_child_arrays_depth8-2 | 0 | 0 | 0.00329856 | -- | -- | -- | -- | `None` |
| package_license_policy-1 | 1 | 7.17563e-05 | 0.0423551 | 13936.1 | 0.998309 | 0 | 0 | `{"license":"MIT"}` |
| package_license_policy-2 | 2 | 6.43569e-12 | 0.289341 | 1.55384e+11 | 1 | 0 | 0 | `{"license":"MIT"}` |

## Limits and controls

The rejection column is the exact mathematical expectation 1/Z for independent draws from the frozen mean-field prediction, not measured runtime or model forwards. A null value has Z=0, so no draw can succeed. No enormous sampling trial was performed. It quantifies why validity rejection can be impractical for rare constraints; the specialized exact controls can avoid it too. This is a post-hoc algebraic analysis of every new canvas, not an additional pre-registered performance experiment.

The first six probes use the seven JSON-Schema type names, eight RFC9110 methods, and a declared three-license project policy. They concern format/schema admissibility, not correct type inference, selecting a safe HTTP action, or recommending a license. The follow-up uses canonical nested one-child JSON arrays (depths 1,3,8) and a genuinely recursive grammar. Its support is defined from grammar bytes, without injecting the most probable legal answer. One and two free token slots are deliberately small enough for exact independent controls; this does not demonstrate scaling to general JSON documents.

The recursive protocol was developed after observing finite-catalog results. Its config was frozen before the new recursive predictions, but this is development evidence, not a held-out benchmark or twelve independent requests from a deployment population. The 192 cells reuse twelve predictions across support/coverage/work limits. No selection by favorable output occurs.

The specialized catalog control enumerates all one/two-token spellings using emission lookup and byte cut points. The recursive control enumerates alphabet-compatible token pairs and uses Python's JSON parser plus the one-child-list predicate. Both give exact full-vocabulary mass and true TV, including aliases. These cheap exact controls are preferable for these small instances; the generic engine is not claimed to beat them or FactorDLM, DFA inference, CARS, or the full EPIC decoder. The benefit demonstrated is an independently checkable error certificate for admission, including sound partial/refused outcomes, under arbitrary CFG ambiguity.

WMC bounds, conditioning, support filters and coupling are established principles. The contribution is their explicit finite-slot/token-provenance certification and integration, with precisely scoped proofs and fresh dLLM executions. Exponential search or conservative bounds may prevent admission. A soft deadline is not a hard wall-time guarantee; proof construction/checking can exceed it.

## Complete repeated-measure grid

| Case | Support | Coverage | Limit | Status | Calls | Certified TV | True TV | Solve+internal check (s) | External check (s) |
|---|---|---|---:|---|---:|---:|---:|---:|---:|
| json_schema_type-1 | top8_plus_catalog | generic_tail | 1 | incomplete | 1 | 0.998599 | 0.663397 | 0.050962 | 0.028332 |
| json_schema_type-1 | top8_plus_catalog | generic_tail | 8 | incomplete | 7 | 0.993026 | 0 | 0.366441 | 0.166476 |
| json_schema_type-1 | top8_plus_catalog | generic_tail | 64 | incomplete | 7 | 0.993026 | 0 | 0.405127 | 0.160304 |
| json_schema_type-1 | top8_plus_catalog | generic_tail | 4096 | incomplete | 7 | 0.993026 | 0 | 0.427797 | 0.162545 |
| json_schema_type-1 | top8_plus_catalog | finite_language_coverage | 1 | incomplete | 1 | 0.99656 | 0.663397 | 0.075230 | 0.043133 |
| json_schema_type-1 | top8_plus_catalog | finite_language_coverage | 8 | certified_tolerance | 7 | 0 | 0 | 0.440138 | 0.137478 |
| json_schema_type-1 | top8_plus_catalog | finite_language_coverage | 64 | certified_tolerance | 7 | 0 | 0 | 0.372910 | 0.162128 |
| json_schema_type-1 | top8_plus_catalog | finite_language_coverage | 4096 | certified_tolerance | 7 | 0 | 0 | 0.323431 | 0.123425 |
| json_schema_type-1 | catalog_only | generic_tail | 1 | incomplete | 1 | 0.998599 | 0.663397 | 0.078648 | 0.036960 |
| json_schema_type-1 | catalog_only | generic_tail | 8 | incomplete | 6 | 0.995837 | 0 | 0.250403 | 0.076223 |
| json_schema_type-1 | catalog_only | generic_tail | 64 | incomplete | 6 | 0.995837 | 0 | 0.245939 | 0.086914 |
| json_schema_type-1 | catalog_only | generic_tail | 4096 | incomplete | 6 | 0.995837 | 0 | 0.239127 | 0.086672 |
| json_schema_type-1 | catalog_only | finite_language_coverage | 1 | incomplete | 1 | 0.663397 | 0.663397 | 0.071212 | 0.034053 |
| json_schema_type-1 | catalog_only | finite_language_coverage | 8 | certified_tolerance | 4 | 0.0410112 | 0.0410112 | 0.206471 | 0.074031 |
| json_schema_type-1 | catalog_only | finite_language_coverage | 64 | certified_tolerance | 4 | 0.0410112 | 0.0410112 | 0.205495 | 0.083104 |
| json_schema_type-1 | catalog_only | finite_language_coverage | 4096 | certified_tolerance | 6 | 0 | 0 | 0.300960 | 0.083403 |
| json_schema_type-2 | top8_plus_catalog | generic_tail | 1 | incomplete | 1 | 0.999999 | 0.0710099 | 0.084802 | 0.044499 |
| json_schema_type-2 | top8_plus_catalog | generic_tail | 8 | incomplete | 8 | 0.999999 | 0.000115571 | 0.359654 | 0.116935 |
| json_schema_type-2 | top8_plus_catalog | generic_tail | 64 | incomplete | 31 | 0.999999 | 0 | 12.967619 | 1.308196 |
| json_schema_type-2 | top8_plus_catalog | generic_tail | 4096 | incomplete | 31 | 0.999999 | 0 | 13.157053 | 1.257670 |
| json_schema_type-2 | top8_plus_catalog | finite_language_coverage | 1 | incomplete | 1 | 0.999989 | 0.0710099 | 0.077826 | 0.035788 |
| json_schema_type-2 | top8_plus_catalog | finite_language_coverage | 8 | incomplete | 8 | 0.999988 | 0.000115571 | 0.387864 | 0.094244 |
| json_schema_type-2 | top8_plus_catalog | finite_language_coverage | 64 | certified_tolerance | 28 | 0.0302623 | 7.72844e-07 | 12.374652 | 1.844219 |
| json_schema_type-2 | top8_plus_catalog | finite_language_coverage | 4096 | certified_tolerance | 31 | 0 | 0 | 14.764291 | 1.573574 |
| json_schema_type-2 | catalog_only | generic_tail | 1 | incomplete | 1 | 0.999999 | 0.0710099 | 0.060136 | 0.030370 |
| json_schema_type-2 | catalog_only | generic_tail | 8 | incomplete | 8 | 0.999999 | 0.000406256 | 0.599791 | 0.136095 |
| json_schema_type-2 | catalog_only | generic_tail | 64 | incomplete | 30 | 0.999999 | 0 | 6.163582 | 1.175973 |
| json_schema_type-2 | catalog_only | generic_tail | 4096 | incomplete | 30 | 0.999999 | 0 | 6.277359 | 1.174716 |
| json_schema_type-2 | catalog_only | finite_language_coverage | 1 | incomplete | 1 | 0.833569 | 0.0710099 | 0.154625 | 0.044864 |
| json_schema_type-2 | catalog_only | finite_language_coverage | 8 | incomplete | 8 | 0.773967 | 0.000406256 | 0.588938 | 0.188154 |
| json_schema_type-2 | catalog_only | finite_language_coverage | 64 | certified_tolerance | 24 | 0.018248 | 1.21199e-06 | 4.366720 | 0.705119 |
| json_schema_type-2 | catalog_only | finite_language_coverage | 4096 | certified_tolerance | 30 | 0 | 0 | 6.115419 | 1.093304 |
| http_method-1 | top8_plus_catalog | generic_tail | 1 | incomplete | 1 | 0.980563 | 0.457201 | 0.315746 | 0.152723 |
| http_method-1 | top8_plus_catalog | generic_tail | 8 | incomplete | 5 | 0.73619 | 0 | 2.060879 | 0.551196 |
| http_method-1 | top8_plus_catalog | generic_tail | 64 | incomplete | 5 | 0.73619 | 0 | 1.836782 | 0.559554 |
| http_method-1 | top8_plus_catalog | generic_tail | 4096 | incomplete | 5 | 0.73619 | 0 | 1.839938 | 0.551599 |
| http_method-1 | top8_plus_catalog | finite_language_coverage | 1 | incomplete | 1 | 0.978405 | 0.457201 | 0.307617 | 0.147779 |
| http_method-1 | top8_plus_catalog | finite_language_coverage | 8 | certified_tolerance | 5 | 0 | 0 | 1.857748 | 0.553313 |
| http_method-1 | top8_plus_catalog | finite_language_coverage | 64 | certified_tolerance | 5 | 0 | 0 | 1.869627 | 0.563071 |
| http_method-1 | top8_plus_catalog | finite_language_coverage | 4096 | certified_tolerance | 5 | 0 | 0 | 1.863118 | 0.573468 |
| http_method-1 | catalog_only | generic_tail | 1 | incomplete | 1 | 0.980563 | 0.457201 | 0.282955 | 0.145629 |
| http_method-1 | catalog_only | generic_tail | 8 | incomplete | 4 | 0.964191 | 0 | 1.003275 | 0.490835 |
| http_method-1 | catalog_only | generic_tail | 64 | incomplete | 4 | 0.964191 | 0 | 1.003315 | 0.495720 |
| http_method-1 | catalog_only | generic_tail | 4096 | incomplete | 4 | 0.964191 | 0 | 1.003267 | 0.489790 |
| http_method-1 | catalog_only | finite_language_coverage | 1 | incomplete | 1 | 0.457201 | 0.457201 | 0.300338 | 0.153434 |
| http_method-1 | catalog_only | finite_language_coverage | 8 | certified_tolerance | 2 | 0.000277893 | 0.000277893 | 0.525852 | 0.261144 |
| http_method-1 | catalog_only | finite_language_coverage | 64 | certified_tolerance | 2 | 0.000277893 | 0.000277893 | 0.525780 | 0.261221 |
| http_method-1 | catalog_only | finite_language_coverage | 4096 | certified_tolerance | 4 | 0 | 0 | 1.017520 | 0.527898 |
| http_method-2 | top8_plus_catalog | generic_tail | 1 | incomplete | 1 | 1 | 0.460822 | 0.269744 | 0.152849 |
| http_method-2 | top8_plus_catalog | generic_tail | 8 | incomplete | 8 | 1 | 0.0600866 | 2.070897 | 1.011674 |
| http_method-2 | top8_plus_catalog | generic_tail | 64 | incomplete | 20 | 1 | 0 | 18.787686 | 1.875250 |
| http_method-2 | top8_plus_catalog | generic_tail | 4096 | incomplete | 20 | 1 | 0 | 18.797575 | 1.899658 |
| http_method-2 | top8_plus_catalog | finite_language_coverage | 1 | incomplete | 1 | 1 | 0.460822 | 0.280342 | 0.138843 |
| http_method-2 | top8_plus_catalog | finite_language_coverage | 8 | incomplete | 8 | 1 | 0.0600866 | 2.093107 | 1.041575 |
| http_method-2 | top8_plus_catalog | finite_language_coverage | 64 | certified_tolerance | 20 | 0 | 0 | 18.769963 | 1.891291 |
| http_method-2 | top8_plus_catalog | finite_language_coverage | 4096 | certified_tolerance | 20 | 0 | 0 | 18.750828 | 1.931590 |
| http_method-2 | catalog_only | generic_tail | 1 | incomplete | 1 | 1 | 0.460822 | 0.268557 | 0.135929 |
| http_method-2 | catalog_only | generic_tail | 8 | incomplete | 8 | 1 | 0.0207302 | 3.729240 | 0.809318 |
| http_method-2 | catalog_only | generic_tail | 64 | incomplete | 19 | 1 | 0 | 10.404745 | 1.883280 |
| http_method-2 | catalog_only | generic_tail | 4096 | incomplete | 19 | 1 | 0 | 10.447144 | 1.825809 |
| http_method-2 | catalog_only | finite_language_coverage | 1 | incomplete | 1 | 0.935814 | 0.460822 | 0.286224 | 0.140688 |
| http_method-2 | catalog_only | finite_language_coverage | 8 | incomplete | 8 | 0.190011 | 0.0207302 | 3.729080 | 0.832584 |
| http_method-2 | catalog_only | finite_language_coverage | 64 | certified_tolerance | 15 | 0.0367121 | 0.000182337 | 7.615177 | 1.557021 |
| http_method-2 | catalog_only | finite_language_coverage | 4096 | certified_tolerance | 19 | 0 | 0 | 10.428788 | 1.853398 |
| package_license_policy-1 | top8_plus_catalog | generic_tail | 1 | incomplete | 1 | 0.999928 | 0 | 0.048422 | 0.024988 |
| package_license_policy-1 | top8_plus_catalog | generic_tail | 8 | incomplete | 2 | 0.998309 | 0 | 0.217465 | 0.083081 |
| package_license_policy-1 | top8_plus_catalog | generic_tail | 64 | incomplete | 2 | 0.998309 | 0 | 0.213611 | 0.081665 |
| package_license_policy-1 | top8_plus_catalog | generic_tail | 4096 | incomplete | 2 | 0.998309 | 0 | 0.217425 | 0.080827 |
| package_license_policy-1 | top8_plus_catalog | finite_language_coverage | 1 | incomplete | 1 | 0.999925 | 0 | 0.062576 | 0.029316 |
| package_license_policy-1 | top8_plus_catalog | finite_language_coverage | 8 | certified_tolerance | 2 | 0 | 0 | 0.227267 | 0.111896 |
| package_license_policy-1 | top8_plus_catalog | finite_language_coverage | 64 | certified_tolerance | 2 | 0 | 0 | 0.227326 | 0.140002 |
| package_license_policy-1 | top8_plus_catalog | finite_language_coverage | 4096 | certified_tolerance | 2 | 0 | 0 | 0.245475 | 0.133610 |
| package_license_policy-1 | catalog_only | generic_tail | 1 | incomplete | 1 | 0.999928 | 0 | 0.048188 | 0.024714 |
| package_license_policy-1 | catalog_only | generic_tail | 8 | incomplete | 1 | 0.999928 | 0 | 0.046364 | 0.024382 |
| package_license_policy-1 | catalog_only | generic_tail | 64 | incomplete | 1 | 0.999928 | 0 | 0.046449 | 0.025210 |
| package_license_policy-1 | catalog_only | generic_tail | 4096 | incomplete | 1 | 0.999928 | 0 | 0.045775 | 0.024811 |
| package_license_policy-1 | catalog_only | finite_language_coverage | 1 | certified_tolerance | 1 | 0 | 0 | 0.063673 | 0.029391 |
| package_license_policy-1 | catalog_only | finite_language_coverage | 8 | certified_tolerance | 1 | 0 | 0 | 0.056062 | 0.029447 |
| package_license_policy-1 | catalog_only | finite_language_coverage | 64 | certified_tolerance | 1 | 0 | 0 | 0.058990 | 0.029445 |
| package_license_policy-1 | catalog_only | finite_language_coverage | 4096 | certified_tolerance | 1 | 0 | 0 | 0.124379 | 0.029294 |
| package_license_policy-2 | top8_plus_catalog | generic_tail | 1 | incomplete | 1 | 1 | 0.0671707 | 0.051046 | 0.027922 |
| package_license_policy-2 | top8_plus_catalog | generic_tail | 8 | incomplete | 5 | 1 | 0 | 1.172087 | 0.225678 |
| package_license_policy-2 | top8_plus_catalog | generic_tail | 64 | incomplete | 5 | 1 | 0 | 1.121697 | 0.195099 |
| package_license_policy-2 | top8_plus_catalog | generic_tail | 4096 | incomplete | 5 | 1 | 0 | 1.126604 | 0.196144 |
| package_license_policy-2 | top8_plus_catalog | finite_language_coverage | 1 | incomplete | 1 | 1 | 0.0671707 | 0.063650 | 0.029453 |
| package_license_policy-2 | top8_plus_catalog | finite_language_coverage | 8 | certified_tolerance | 5 | 0 | 0 | 1.154808 | 0.195343 |
| package_license_policy-2 | top8_plus_catalog | finite_language_coverage | 64 | certified_tolerance | 5 | 0 | 0 | 1.153088 | 0.196866 |
| package_license_policy-2 | top8_plus_catalog | finite_language_coverage | 4096 | certified_tolerance | 5 | 0 | 0 | 1.232652 | 0.247130 |
| package_license_policy-2 | catalog_only | generic_tail | 1 | incomplete | 1 | 1 | 0.0671707 | 0.046198 | 0.024279 |
| package_license_policy-2 | catalog_only | generic_tail | 8 | incomplete | 4 | 1 | 0 | 0.236717 | 0.133011 |
| package_license_policy-2 | catalog_only | generic_tail | 64 | incomplete | 4 | 1 | 0 | 0.239345 | 0.130282 |
| package_license_policy-2 | catalog_only | generic_tail | 4096 | incomplete | 4 | 1 | 0 | 0.235521 | 0.141326 |
| package_license_policy-2 | catalog_only | finite_language_coverage | 1 | incomplete | 1 | 0.828725 | 0.0671707 | 0.054348 | 0.029411 |
| package_license_policy-2 | catalog_only | finite_language_coverage | 8 | certified_tolerance | 3 | 0.01394 | 0 | 0.159146 | 0.084211 |
| package_license_policy-2 | catalog_only | finite_language_coverage | 64 | certified_tolerance | 3 | 0.01394 | 0 | 0.206603 | 0.085389 |
| package_license_policy-2 | catalog_only | finite_language_coverage | 4096 | certified_tolerance | 4 | 0 | 0 | 0.247958 | 0.164292 |
| one_child_arrays_depth1-1 | top8_plus_alphabet | generic_tail | 1 | incomplete | 1 | 0.80578 | 0 | 0.033364 | 0.019007 |
| one_child_arrays_depth1-1 | top8_plus_alphabet | generic_tail | 8 | incomplete | 2 | 0.125338 | 0 | 0.102892 | 0.065520 |
| one_child_arrays_depth1-1 | top8_plus_alphabet | generic_tail | 64 | incomplete | 2 | 0.125338 | 0 | 0.102180 | 0.066001 |
| one_child_arrays_depth1-1 | top8_plus_alphabet | generic_tail | 4096 | incomplete | 2 | 0.125338 | 0 | 0.103845 | 0.067029 |
| one_child_arrays_depth1-1 | top8_plus_alphabet | terminal_alphabet_coverage | 1 | incomplete | 1 | 0.80022 | 0 | 0.054072 | 0.028107 |
| one_child_arrays_depth1-1 | top8_plus_alphabet | terminal_alphabet_coverage | 8 | certified_tolerance | 2 | 0 | 0 | 0.118890 | 0.075298 |
| one_child_arrays_depth1-1 | top8_plus_alphabet | terminal_alphabet_coverage | 64 | certified_tolerance | 2 | 0 | 0 | 0.118203 | 0.075967 |
| one_child_arrays_depth1-1 | top8_plus_alphabet | terminal_alphabet_coverage | 4096 | certified_tolerance | 2 | 0 | 0 | 0.117006 | 0.075635 |
| one_child_arrays_depth1-1 | alphabet_only | generic_tail | 1 | incomplete | 1 | 0.80578 | 0 | 0.034461 | 0.018623 |
| one_child_arrays_depth1-1 | alphabet_only | generic_tail | 8 | incomplete | 2 | 0.22417 | 0 | 0.101383 | 0.065800 |
| one_child_arrays_depth1-1 | alphabet_only | generic_tail | 64 | incomplete | 2 | 0.22417 | 0 | 0.094107 | 0.066468 |
| one_child_arrays_depth1-1 | alphabet_only | generic_tail | 4096 | incomplete | 2 | 0.22417 | 0 | 0.097025 | 0.066291 |
| one_child_arrays_depth1-1 | alphabet_only | terminal_alphabet_coverage | 1 | incomplete | 1 | 0.794232 | 0 | 0.054062 | 0.027937 |
| one_child_arrays_depth1-1 | alphabet_only | terminal_alphabet_coverage | 8 | certified_tolerance | 2 | 0 | 0 | 0.116468 | 0.076015 |
| one_child_arrays_depth1-1 | alphabet_only | terminal_alphabet_coverage | 64 | certified_tolerance | 2 | 0 | 0 | 0.115564 | 0.075929 |
| one_child_arrays_depth1-1 | alphabet_only | terminal_alphabet_coverage | 4096 | certified_tolerance | 2 | 0 | 0 | 0.119050 | 0.075245 |
| one_child_arrays_depth1-2 | top8_plus_alphabet | generic_tail | 1 | incomplete | 1 | 0.986726 | 7.1497e-05 | 0.035340 | 0.019063 |
| one_child_arrays_depth1-2 | top8_plus_alphabet | generic_tail | 8 | incomplete | 5 | 0.736204 | 0 | 0.245605 | 0.168018 |
| one_child_arrays_depth1-2 | top8_plus_alphabet | generic_tail | 64 | incomplete | 5 | 0.736204 | 0 | 0.244073 | 0.166815 |
| one_child_arrays_depth1-2 | top8_plus_alphabet | generic_tail | 4096 | incomplete | 5 | 0.736204 | 0 | 0.245645 | 0.168347 |
| one_child_arrays_depth1-2 | top8_plus_alphabet | terminal_alphabet_coverage | 1 | incomplete | 1 | 0.986216 | 7.1497e-05 | 0.054475 | 0.028972 |
| one_child_arrays_depth1-2 | top8_plus_alphabet | terminal_alphabet_coverage | 8 | certified_tolerance | 4 | 0.000182729 | 0 | 0.196708 | 0.126016 |
| one_child_arrays_depth1-2 | top8_plus_alphabet | terminal_alphabet_coverage | 64 | certified_tolerance | 4 | 0.000182729 | 0 | 0.221218 | 0.149771 |
| one_child_arrays_depth1-2 | top8_plus_alphabet | terminal_alphabet_coverage | 4096 | certified_tolerance | 5 | 0 | 0 | 0.364224 | 0.211483 |
| one_child_arrays_depth1-2 | alphabet_only | generic_tail | 1 | incomplete | 1 | 0.986726 | 7.1497e-05 | 0.044137 | 0.024316 |
| one_child_arrays_depth1-2 | alphabet_only | generic_tail | 8 | incomplete | 5 | 0.824684 | 0 | 0.299132 | 0.190932 |
| one_child_arrays_depth1-2 | alphabet_only | generic_tail | 64 | incomplete | 5 | 0.824684 | 0 | 0.288726 | 0.173149 |
| one_child_arrays_depth1-2 | alphabet_only | generic_tail | 4096 | incomplete | 5 | 0.824684 | 0 | 0.256182 | 0.163912 |
| one_child_arrays_depth1-2 | alphabet_only | terminal_alphabet_coverage | 1 | incomplete | 1 | 0.985842 | 7.1497e-05 | 0.057050 | 0.030389 |
| one_child_arrays_depth1-2 | alphabet_only | terminal_alphabet_coverage | 8 | certified_tolerance | 4 | 0.000180396 | 0 | 0.197883 | 0.124528 |
| one_child_arrays_depth1-2 | alphabet_only | terminal_alphabet_coverage | 64 | certified_tolerance | 4 | 0.000180396 | 0 | 0.224041 | 0.126144 |
| one_child_arrays_depth1-2 | alphabet_only | terminal_alphabet_coverage | 4096 | certified_tolerance | 5 | 0 | 0 | 0.322774 | 0.201118 |
| one_child_arrays_depth3-1 | top8_plus_alphabet | generic_tail | 1 | zero_valid_probability_on_support | 1 | -- | -- | 0.088075 | 0.075454 |
| one_child_arrays_depth3-1 | top8_plus_alphabet | generic_tail | 8 | zero_valid_probability_on_support | 1 | -- | -- | 0.103252 | 0.080068 |
| one_child_arrays_depth3-1 | top8_plus_alphabet | generic_tail | 64 | zero_valid_probability_on_support | 1 | -- | -- | 0.088198 | 0.070684 |
| one_child_arrays_depth3-1 | top8_plus_alphabet | generic_tail | 4096 | zero_valid_probability_on_support | 1 | -- | -- | 0.097701 | 0.085657 |
| one_child_arrays_depth3-1 | top8_plus_alphabet | terminal_alphabet_coverage | 1 | zero_valid_probability_on_support | 1 | -- | -- | 0.114816 | 0.085597 |
| one_child_arrays_depth3-1 | top8_plus_alphabet | terminal_alphabet_coverage | 8 | zero_valid_probability_on_support | 1 | -- | -- | 0.105345 | 0.076905 |
| one_child_arrays_depth3-1 | top8_plus_alphabet | terminal_alphabet_coverage | 64 | zero_valid_probability_on_support | 1 | -- | -- | 0.111191 | 0.077042 |
| one_child_arrays_depth3-1 | top8_plus_alphabet | terminal_alphabet_coverage | 4096 | zero_valid_probability_on_support | 1 | -- | -- | 0.109577 | 0.077496 |
| one_child_arrays_depth3-1 | alphabet_only | generic_tail | 1 | zero_valid_probability_on_support | 1 | -- | -- | 0.087341 | 0.066806 |
| one_child_arrays_depth3-1 | alphabet_only | generic_tail | 8 | zero_valid_probability_on_support | 1 | -- | -- | 0.087335 | 0.067004 |
| one_child_arrays_depth3-1 | alphabet_only | generic_tail | 64 | zero_valid_probability_on_support | 1 | -- | -- | 0.087911 | 0.067125 |
| one_child_arrays_depth3-1 | alphabet_only | generic_tail | 4096 | zero_valid_probability_on_support | 1 | -- | -- | 0.088871 | 0.067070 |
| one_child_arrays_depth3-1 | alphabet_only | terminal_alphabet_coverage | 1 | zero_valid_probability_on_support | 1 | -- | -- | 0.108084 | 0.076633 |
| one_child_arrays_depth3-1 | alphabet_only | terminal_alphabet_coverage | 8 | zero_valid_probability_on_support | 1 | -- | -- | 0.110022 | 0.081356 |
| one_child_arrays_depth3-1 | alphabet_only | terminal_alphabet_coverage | 64 | zero_valid_probability_on_support | 1 | -- | -- | 0.123188 | 0.126031 |
| one_child_arrays_depth3-1 | alphabet_only | terminal_alphabet_coverage | 4096 | zero_valid_probability_on_support | 1 | -- | -- | 0.144035 | 0.098287 |
| one_child_arrays_depth3-2 | top8_plus_alphabet | generic_tail | 1 | incomplete | 1 | 0.926039 | 0.113096 | 0.038557 | 0.023348 |
| one_child_arrays_depth3-2 | top8_plus_alphabet | generic_tail | 8 | incomplete | 5 | 0.8173 | 0 | 0.299325 | 0.190839 |
| one_child_arrays_depth3-2 | top8_plus_alphabet | generic_tail | 64 | incomplete | 5 | 0.8173 | 0 | 0.271117 | 0.191418 |
| one_child_arrays_depth3-2 | top8_plus_alphabet | generic_tail | 4096 | incomplete | 5 | 0.8173 | 0 | 0.246972 | 0.168853 |
| one_child_arrays_depth3-2 | top8_plus_alphabet | terminal_alphabet_coverage | 1 | incomplete | 1 | 0.882029 | 0.113096 | 0.056664 | 0.028754 |
| one_child_arrays_depth3-2 | top8_plus_alphabet | terminal_alphabet_coverage | 8 | certified_tolerance | 5 | 0 | 0 | 0.307588 | 0.199635 |
| one_child_arrays_depth3-2 | top8_plus_alphabet | terminal_alphabet_coverage | 64 | certified_tolerance | 5 | 0 | 0 | 0.290204 | 0.194112 |
| one_child_arrays_depth3-2 | top8_plus_alphabet | terminal_alphabet_coverage | 4096 | certified_tolerance | 5 | 0 | 0 | 0.291038 | 0.190885 |
| one_child_arrays_depth3-2 | alphabet_only | generic_tail | 1 | incomplete | 1 | 0.926039 | 0.113096 | 0.042271 | 0.021439 |
| one_child_arrays_depth3-2 | alphabet_only | generic_tail | 8 | incomplete | 5 | 0.843044 | 0 | 0.240278 | 0.169134 |
| one_child_arrays_depth3-2 | alphabet_only | generic_tail | 64 | incomplete | 5 | 0.843044 | 0 | 0.272056 | 0.184174 |
| one_child_arrays_depth3-2 | alphabet_only | generic_tail | 4096 | incomplete | 5 | 0.843044 | 0 | 0.264623 | 0.172675 |
| one_child_arrays_depth3-2 | alphabet_only | terminal_alphabet_coverage | 1 | incomplete | 1 | 0.866031 | 0.113096 | 0.056497 | 0.032055 |
| one_child_arrays_depth3-2 | alphabet_only | terminal_alphabet_coverage | 8 | certified_tolerance | 5 | 0 | 0 | 0.280739 | 0.186214 |
| one_child_arrays_depth3-2 | alphabet_only | terminal_alphabet_coverage | 64 | certified_tolerance | 5 | 0 | 0 | 0.291179 | 0.188211 |
| one_child_arrays_depth3-2 | alphabet_only | terminal_alphabet_coverage | 4096 | certified_tolerance | 5 | 0 | 0 | 0.286586 | 0.174795 |
| one_child_arrays_depth8-1 | top8_plus_alphabet | generic_tail | 1 | zero_valid_probability_on_support | 1 | -- | -- | 0.091596 | 0.067921 |
| one_child_arrays_depth8-1 | top8_plus_alphabet | generic_tail | 8 | zero_valid_probability_on_support | 1 | -- | -- | 0.091676 | 0.067429 |
| one_child_arrays_depth8-1 | top8_plus_alphabet | generic_tail | 64 | zero_valid_probability_on_support | 1 | -- | -- | 0.092334 | 0.068168 |
| one_child_arrays_depth8-1 | top8_plus_alphabet | generic_tail | 4096 | zero_valid_probability_on_support | 1 | -- | -- | 0.094231 | 0.068758 |
| one_child_arrays_depth8-1 | top8_plus_alphabet | terminal_alphabet_coverage | 1 | zero_valid_probability_on_support | 1 | -- | -- | 0.111218 | 0.078077 |
| one_child_arrays_depth8-1 | top8_plus_alphabet | terminal_alphabet_coverage | 8 | zero_valid_probability_on_support | 1 | -- | -- | 0.109241 | 0.077503 |
| one_child_arrays_depth8-1 | top8_plus_alphabet | terminal_alphabet_coverage | 64 | zero_valid_probability_on_support | 1 | -- | -- | 0.111908 | 0.077752 |
| one_child_arrays_depth8-1 | top8_plus_alphabet | terminal_alphabet_coverage | 4096 | zero_valid_probability_on_support | 1 | -- | -- | 0.109906 | 0.077897 |
| one_child_arrays_depth8-1 | alphabet_only | generic_tail | 1 | zero_valid_probability_on_support | 1 | -- | -- | 0.090146 | 0.068398 |
| one_child_arrays_depth8-1 | alphabet_only | generic_tail | 8 | zero_valid_probability_on_support | 1 | -- | -- | 0.086597 | 0.068124 |
| one_child_arrays_depth8-1 | alphabet_only | generic_tail | 64 | zero_valid_probability_on_support | 1 | -- | -- | 0.087261 | 0.068343 |
| one_child_arrays_depth8-1 | alphabet_only | generic_tail | 4096 | zero_valid_probability_on_support | 1 | -- | -- | 0.088215 | 0.068014 |
| one_child_arrays_depth8-1 | alphabet_only | terminal_alphabet_coverage | 1 | zero_valid_probability_on_support | 1 | -- | -- | 0.106087 | 0.078090 |
| one_child_arrays_depth8-1 | alphabet_only | terminal_alphabet_coverage | 8 | zero_valid_probability_on_support | 1 | -- | -- | 0.107560 | 0.077820 |
| one_child_arrays_depth8-1 | alphabet_only | terminal_alphabet_coverage | 64 | zero_valid_probability_on_support | 1 | -- | -- | 0.108384 | 0.078250 |
| one_child_arrays_depth8-1 | alphabet_only | terminal_alphabet_coverage | 4096 | zero_valid_probability_on_support | 1 | -- | -- | 0.110866 | 0.077581 |
| one_child_arrays_depth8-2 | top8_plus_alphabet | generic_tail | 1 | zero_valid_probability_on_support | 1 | -- | -- | 0.096090 | 0.071415 |
| one_child_arrays_depth8-2 | top8_plus_alphabet | generic_tail | 8 | zero_valid_probability_on_support | 1 | -- | -- | 0.096501 | 0.072741 |
| one_child_arrays_depth8-2 | top8_plus_alphabet | generic_tail | 64 | zero_valid_probability_on_support | 1 | -- | -- | 0.096418 | 0.069303 |
| one_child_arrays_depth8-2 | top8_plus_alphabet | generic_tail | 4096 | zero_valid_probability_on_support | 1 | -- | -- | 0.097347 | 0.070014 |
| one_child_arrays_depth8-2 | top8_plus_alphabet | terminal_alphabet_coverage | 1 | zero_valid_probability_on_support | 1 | -- | -- | 0.116532 | 0.079190 |
| one_child_arrays_depth8-2 | top8_plus_alphabet | terminal_alphabet_coverage | 8 | zero_valid_probability_on_support | 1 | -- | -- | 0.116563 | 0.079292 |
| one_child_arrays_depth8-2 | top8_plus_alphabet | terminal_alphabet_coverage | 64 | zero_valid_probability_on_support | 1 | -- | -- | 0.116309 | 0.079076 |
| one_child_arrays_depth8-2 | top8_plus_alphabet | terminal_alphabet_coverage | 4096 | zero_valid_probability_on_support | 1 | -- | -- | 0.118144 | 0.079660 |
| one_child_arrays_depth8-2 | alphabet_only | generic_tail | 1 | zero_valid_probability_on_support | 1 | -- | -- | 0.092927 | 0.068795 |
| one_child_arrays_depth8-2 | alphabet_only | generic_tail | 8 | zero_valid_probability_on_support | 1 | -- | -- | 0.091155 | 0.069345 |
| one_child_arrays_depth8-2 | alphabet_only | generic_tail | 64 | zero_valid_probability_on_support | 1 | -- | -- | 0.092372 | 0.068987 |
| one_child_arrays_depth8-2 | alphabet_only | generic_tail | 4096 | zero_valid_probability_on_support | 1 | -- | -- | 0.091097 | 0.068153 |
| one_child_arrays_depth8-2 | alphabet_only | terminal_alphabet_coverage | 1 | zero_valid_probability_on_support | 1 | -- | -- | 0.113043 | 0.078327 |
| one_child_arrays_depth8-2 | alphabet_only | terminal_alphabet_coverage | 8 | zero_valid_probability_on_support | 1 | -- | -- | 0.107650 | 0.078236 |
| one_child_arrays_depth8-2 | alphabet_only | terminal_alphabet_coverage | 64 | zero_valid_probability_on_support | 1 | -- | -- | 0.110320 | 0.078436 |
| one_child_arrays_depth8-2 | alphabet_only | terminal_alphabet_coverage | 4096 | zero_valid_probability_on_support | 1 | -- | -- | 0.109903 | 0.078399 |

## Provenance

Producing commits: `8e891f8e79bbb471c0bb21e60f542a939302788f`, `b0ed276858eb9f74e932ff192729654c8034d71c`.

Official MDLM-OWT checkpoint and GPT-2 tokenizer are pinned by revision and hashes; no weights are committed. CPU F32 network kernels are an audited attention/rotary port, not a bitwise GPU/FlashAttention equivalence claim. Full-vocabulary F64 softmax excludes MASK, then exact binary rationals are normalized over the whole vocabulary. Fixed positions have probability one; retained support rows are never renormalized. Full logs/logits, configurations, metadata and compact portable proofs are retained in the raw archive.
