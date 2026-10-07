# M34: complete outcomes, including refusals and stronger controls

Classical weighted CFG sampling adapted to finite original dLLM tokens. Exactness is per frozen prediction/support, not semantic quality or the future trajectory. No published competitor was timed here.

8/9 fresh full-JSON inputs finish; 18/18 array replays finish. All 52 initially successful masses/marginals are unchanged. The integer/pre-binarization refinement has a paired query-time ratio reported below; both independent stack controls get the integer optimization.

```json
{
  "phases": {
    "scaling": {
      "cfg:EXACT_ON_SUPPORT": 28,
      "stack:EXACT_ON_SUPPORT": 22,
      "stack:TIMEOUT_WORK_LIMIT": 6
    },
    "replay": {
      "cfg:EXACT_ON_SUPPORT": 18,
      "stack:EXACT_ON_SUPPORT": 18
    },
    "json-model": {
      "cfg:EXACT_ON_SUPPORT": 6,
      "cfg:TIMEOUT_EXTERNAL": 1,
      "cfg:TIMEOUT_WORK_LIMIT": 2
    },
    "integer-scaling": {
      "cfg:EXACT_ON_SUPPORT": 28,
      "stack:EXACT_ON_SUPPORT": 22,
      "stack:TIMEOUT_WORK_LIMIT": 6
    },
    "integer-replay": {
      "cfg:EXACT_ON_SUPPORT": 18,
      "stack:EXACT_ON_SUPPORT": 18
    },
    "integer-json-model": {
      "cfg:EXACT_ON_SUPPORT": 8,
      "cfg:TIMEOUT_WORK_LIMIT": 1
    }
  },
  "correctness_scope": "focused independent extension tests; no whole-source refinement",
  "exact_before_after_pairs": 52,
  "median_query_refinement_ratio": 10.225318600119397,
  "rejection_statuses": {
    "TRIAL_LIMIT": 13,
    "SAMPLED": 14
  },
  "reuse_statuses": {
    "EXACT_ON_SUPPORT": 26,
    "TIMEOUT_WORK_LIMIT": 1
  }
}
```

| Case | CFG first sample (ms) | Support rejection expected trials | Rejection outcome / ms | Cached / fresh (ms) |
| --- | ---: | ---: | --- | ---: |
| recursive_arrays_depth1-16 | 57.653 | 1.85e+07 | TRIAL_LIMIT / 100.505 | 8.565 / 8.949 |
| recursive_arrays_depth1-4 | 2.897 | 90.8 | SAMPLED / 0.275 | 0.278 / 0.697 |
| recursive_arrays_depth1-8 | 7.980 | 1.34e+04 | TRIAL_LIMIT / 67.857 | 1.182 / 2.156 |
| recursive_arrays_depth3-16 | 65.833 | 2.22e+07 | TRIAL_LIMIT / 100.173 | 10.147 / 19.595 |
| recursive_arrays_depth3-4 | 3.577 | 137 | SAMPLED / 0.984 | 0.309 / 0.984 |
| recursive_arrays_depth3-8 | 9.003 | 2.47e+04 | SAMPLED / 29.296 | 1.283 / 2.279 |
| recursive_arrays_depth8-16 | 85.197 | 9.06e+06 | TRIAL_LIMIT / 106.521 | 11.964 / 21.939 |
| recursive_arrays_depth8-4 | 3.553 | 235 | SAMPLED / 0.114 | 0.363 / 1.057 |
| recursive_arrays_depth8-8 | 10.643 | 1.72e+04 | TRIAL_LIMIT / 80.711 | 1.619 / 2.853 |
| recursive_one_child_arrays_depth1-16 | 8.149 | 3.16e+07 | TRIAL_LIMIT / 96.810 | 1.399 / 3.064 |
| recursive_one_child_arrays_depth1-4 | 1.871 | 90.5 | SAMPLED / 0.264 | 0.141 / 0.444 |
| recursive_one_child_arrays_depth1-8 | 3.423 | 1.38e+04 | SAMPLED / 27.030 | 0.393 / 1.104 |
| recursive_one_child_arrays_depth3-16 | 9.228 | 1.25e+08 | TRIAL_LIMIT / 100.533 | 1.561 / 3.986 |
| recursive_one_child_arrays_depth3-4 | 1.976 | 134 | SAMPLED / 0.204 | 0.147 / 2.342 |
| recursive_one_child_arrays_depth3-8 | 3.943 | 8.06e+04 | TRIAL_LIMIT / 70.915 | 0.453 / 1.175 |
| recursive_one_child_arrays_depth8-16 | 13.197 | 9.04e+06 | TRIAL_LIMIT / 111.837 | 2.350 / 3.370 |
| recursive_one_child_arrays_depth8-4 | 3.422 | 235 | SAMPLED / 0.100 | 0.203 / 0.565 |
| recursive_one_child_arrays_depth8-8 | 5.008 | 1.72e+04 | TRIAL_LIMIT / 78.363 | 0.629 / 1.292 |
| json-context0-4 | 68.680 | 9.16e+03 | SAMPLED / 41.965 | 8.097 / 24.134 |
| json-context0-8 | 456.004 | 2.42e+03 | SAMPLED / 7.110 | 46.949 / 116.390 |
| json-context0-16 | 3345.223 | 1.67e+04 | TRIAL_LIMIT / 116.271 | 227.203 / 626.177 |
| json-context1-4 | 37.868 | 137 | SAMPLED / 0.504 | 2.917 / 20.778 |
| json-context1-8 | 192.541 | 5.95e+03 | SAMPLED / 40.138 | 20.394 / 36.185 |
| json-context1-16 | 1844.048 | 1.01e+04 | TRIAL_LIMIT / 125.478 | 179.165 / 458.075 |
| json-context2-4 | 127.567 | 13.1 | SAMPLED / 0.124 | 10.656 / 28.955 |
| json-context2-8 | 922.455 | 238 | SAMPLED / 2.023 | 85.207 / 307.397 |
| json-context2-16 | TIMEOUT_WORK_LIMIT | unresolved | TRIAL_LIMIT / 112.148 | TIMEOUT_WORK_LIMIT |

Rejection is cheaper on all six smaller JSON cases in this recorded seed. Trial exhaustion is not infeasibility. Expected trial counts are algebra from Z and represented mass, not measured wall-time speedups. Cached/fresh reuse equality is checked on all 26 completed cases; reuse can still lose to a compact specialized controller. One-type counters generally remain cheaper. The 28 Dyck probes are declared mathematical scaling inputs, not external/neural quality benchmarks. Full logits remain local; losslessly deduplicated original inputs, probabilities, full tokenizer bytes, every config, outcome and source hash are archived.

## Every final grid/application comparison

Times below exclude model loading/forward and include construction separately. Method `stack` is an independent local exact controller, not published code.

| Case | Method | Status | Cells | Compile / query (ms) |
| --- | --- | --- | ---: | ---: |
| dyck-4-uniform-all_masked | cfg | EXACT_ON_SUPPORT | 36 | 0.571 / 0.042 |
| dyck-4-uniform-all_masked | stack | EXACT_ON_SUPPORT | 11 | 0.039 / 0.054 |
| dyck-4-uniform-fixed_alternating_opening_half | cfg | EXACT_ON_SUPPORT | 22 | 0.557 / 0.031 |
| dyck-4-uniform-fixed_alternating_opening_half | stack | EXACT_ON_SUPPORT | 5 | 0.025 / 0.039 |
| dyck-4-seeded_positive_integer_rows-all_masked | cfg | EXACT_ON_SUPPORT | 36 | 0.570 / 0.042 |
| dyck-4-seeded_positive_integer_rows-all_masked | stack | EXACT_ON_SUPPORT | 11 | 0.068 / 0.057 |
| dyck-4-seeded_positive_integer_rows-fixed_alternating_opening_half | cfg | EXACT_ON_SUPPORT | 22 | 0.552 / 0.032 |
| dyck-4-seeded_positive_integer_rows-fixed_alternating_opening_half | stack | EXACT_ON_SUPPORT | 5 | 0.026 / 0.042 |
| dyck-8-uniform-all_masked | cfg | EXACT_ON_SUPPORT | 104 | 0.740 / 0.090 |
| dyck-8-uniform-all_masked | stack | EXACT_ON_SUPPORT | 57 | 0.160 / 0.125 |
| dyck-8-uniform-fixed_alternating_opening_half | cfg | EXACT_ON_SUPPORT | 60 | 0.641 / 0.055 |
| dyck-8-uniform-fixed_alternating_opening_half | stack | EXACT_ON_SUPPORT | 9 | 0.039 / 0.066 |
| dyck-8-seeded_positive_integer_rows-all_masked | cfg | EXACT_ON_SUPPORT | 104 | 0.755 / 0.099 |
| dyck-8-seeded_positive_integer_rows-all_masked | stack | EXACT_ON_SUPPORT | 57 | 0.155 / 0.133 |
| dyck-8-seeded_positive_integer_rows-fixed_alternating_opening_half | cfg | EXACT_ON_SUPPORT | 60 | 0.628 / 0.054 |
| dyck-8-seeded_positive_integer_rows-fixed_alternating_opening_half | stack | EXACT_ON_SUPPORT | 9 | 0.032 / 0.066 |
| dyck-16-uniform-all_masked | cfg | EXACT_ON_SUPPORT | 336 | 1.903 / 0.302 |
| dyck-16-uniform-all_masked | stack | EXACT_ON_SUPPORT | 1013 | 2.052 / 0.982 |
| dyck-16-uniform-fixed_alternating_opening_half | cfg | EXACT_ON_SUPPORT | 184 | 0.923 / 0.117 |
| dyck-16-uniform-fixed_alternating_opening_half | stack | EXACT_ON_SUPPORT | 17 | 0.045 / 0.118 |
| dyck-16-seeded_positive_integer_rows-all_masked | cfg | EXACT_ON_SUPPORT | 336 | 1.611 / 0.318 |
| dyck-16-seeded_positive_integer_rows-all_masked | stack | EXACT_ON_SUPPORT | 1013 | 1.991 / 1.109 |
| dyck-16-seeded_positive_integer_rows-fixed_alternating_opening_half | cfg | EXACT_ON_SUPPORT | 184 | 0.914 / 0.118 |
| dyck-16-seeded_positive_integer_rows-fixed_alternating_opening_half | stack | EXACT_ON_SUPPORT | 17 | 0.053 / 0.121 |
| dyck-24-uniform-all_masked | cfg | EXACT_ON_SUPPORT | 696 | 2.596 / 0.596 |
| dyck-24-uniform-all_masked | stack | EXACT_ON_SUPPORT | 16369 | 38.393 / 15.704 |
| dyck-24-uniform-fixed_alternating_opening_half | cfg | EXACT_ON_SUPPORT | 372 | 1.704 / 0.221 |
| dyck-24-uniform-fixed_alternating_opening_half | stack | EXACT_ON_SUPPORT | 25 | 0.059 / 0.171 |
| dyck-24-seeded_positive_integer_rows-all_masked | cfg | EXACT_ON_SUPPORT | 696 | 2.737 / 0.714 |
| dyck-24-seeded_positive_integer_rows-all_masked | stack | EXACT_ON_SUPPORT | 16369 | 38.504 / 18.716 |
| dyck-24-seeded_positive_integer_rows-fixed_alternating_opening_half | cfg | EXACT_ON_SUPPORT | 372 | 1.623 / 0.226 |
| dyck-24-seeded_positive_integer_rows-fixed_alternating_opening_half | stack | EXACT_ON_SUPPORT | 25 | 0.056 / 0.182 |
| dyck-32-uniform-all_masked | cfg | EXACT_ON_SUPPORT | 1184 | 4.092 / 1.111 |
| dyck-32-uniform-all_masked | stack | TIMEOUT_WORK_LIMIT | None | -- |
| dyck-32-uniform-fixed_alternating_opening_half | cfg | EXACT_ON_SUPPORT | 624 | 2.200 / 0.340 |
| dyck-32-uniform-fixed_alternating_opening_half | stack | EXACT_ON_SUPPORT | 33 | 0.112 / 0.231 |
| dyck-32-seeded_positive_integer_rows-all_masked | cfg | EXACT_ON_SUPPORT | 1184 | 3.948 / 1.343 |
| dyck-32-seeded_positive_integer_rows-all_masked | stack | TIMEOUT_WORK_LIMIT | None | -- |
| dyck-32-seeded_positive_integer_rows-fixed_alternating_opening_half | cfg | EXACT_ON_SUPPORT | 624 | 2.185 / 0.359 |
| dyck-32-seeded_positive_integer_rows-fixed_alternating_opening_half | stack | EXACT_ON_SUPPORT | 33 | 0.120 / 0.245 |
| dyck-48-uniform-all_masked | cfg | EXACT_ON_SUPPORT | 2544 | 8.684 / 2.915 |
| dyck-48-uniform-all_masked | stack | TIMEOUT_WORK_LIMIT | None | -- |
| dyck-48-uniform-fixed_alternating_opening_half | cfg | EXACT_ON_SUPPORT | 1320 | 4.033 / 0.679 |
| dyck-48-uniform-fixed_alternating_opening_half | stack | EXACT_ON_SUPPORT | 49 | 0.089 / 0.317 |
| dyck-48-seeded_positive_integer_rows-all_masked | cfg | EXACT_ON_SUPPORT | 2544 | 8.806 / 3.498 |
| dyck-48-seeded_positive_integer_rows-all_masked | stack | TIMEOUT_WORK_LIMIT | None | -- |
| dyck-48-seeded_positive_integer_rows-fixed_alternating_opening_half | cfg | EXACT_ON_SUPPORT | 1320 | 4.091 / 0.760 |
| dyck-48-seeded_positive_integer_rows-fixed_alternating_opening_half | stack | EXACT_ON_SUPPORT | 49 | 0.091 / 0.345 |
| dyck-64-uniform-all_masked | cfg | EXACT_ON_SUPPORT | 4416 | 16.798 / 6.691 |
| dyck-64-uniform-all_masked | stack | TIMEOUT_WORK_LIMIT | None | -- |
| dyck-64-uniform-fixed_alternating_opening_half | cfg | EXACT_ON_SUPPORT | 2272 | 6.761 / 1.225 |
| dyck-64-uniform-fixed_alternating_opening_half | stack | EXACT_ON_SUPPORT | 65 | 0.121 / 0.449 |
| dyck-64-seeded_positive_integer_rows-all_masked | cfg | EXACT_ON_SUPPORT | 4416 | 16.729 / 8.466 |
| dyck-64-seeded_positive_integer_rows-all_masked | stack | TIMEOUT_WORK_LIMIT | None | -- |
| dyck-64-seeded_positive_integer_rows-fixed_alternating_opening_half | cfg | EXACT_ON_SUPPORT | 2272 | 6.803 / 1.404 |
| dyck-64-seeded_positive_integer_rows-fixed_alternating_opening_half | stack | EXACT_ON_SUPPORT | 65 | 0.125 / 0.483 |
| recursive_arrays_depth1-16 | cfg | EXACT_ON_SUPPORT | 6600 | 33.363 / 24.106 |
| recursive_arrays_depth1-16 | stack | EXACT_ON_SUPPORT | 786 | 3.743 / 4.256 |
| recursive_arrays_depth1-4 | cfg | EXACT_ON_SUPPORT | 432 | 2.538 / 0.328 |
| recursive_arrays_depth1-4 | stack | EXACT_ON_SUPPORT | 54 | 0.817 / 0.315 |
| recursive_arrays_depth1-8 | cfg | EXACT_ON_SUPPORT | 1672 | 6.036 / 1.883 |
| recursive_arrays_depth1-8 | stack | EXACT_ON_SUPPORT | 202 | 1.044 / 0.993 |
| recursive_arrays_depth3-16 | cfg | EXACT_ON_SUPPORT | 7169 | 39.756 / 25.791 |
| recursive_arrays_depth3-16 | stack | EXACT_ON_SUPPORT | 880 | 4.150 / 4.896 |
| recursive_arrays_depth3-4 | cfg | EXACT_ON_SUPPORT | 483 | 3.158 / 0.382 |
| recursive_arrays_depth3-4 | stack | EXACT_ON_SUPPORT | 76 | 1.487 / 0.359 |
| recursive_arrays_depth3-8 | cfg | EXACT_ON_SUPPORT | 1827 | 6.609 / 2.309 |
| recursive_arrays_depth3-8 | stack | EXACT_ON_SUPPORT | 248 | 1.753 / 1.055 |
| recursive_arrays_depth8-16 | cfg | EXACT_ON_SUPPORT | 9149 | 54.044 / 30.772 |
| recursive_arrays_depth8-16 | stack | EXACT_ON_SUPPORT | 1089 | 5.159 / 5.557 |
| recursive_arrays_depth8-4 | cfg | EXACT_ON_SUPPORT | 629 | 3.128 / 0.376 |
| recursive_arrays_depth8-4 | stack | EXACT_ON_SUPPORT | 105 | 1.334 / 0.350 |
| recursive_arrays_depth8-8 | cfg | EXACT_ON_SUPPORT | 2413 | 8.046 / 2.497 |
| recursive_arrays_depth8-8 | stack | EXACT_ON_SUPPORT | 337 | 1.985 / 1.254 |
| recursive_one_child_arrays_depth1-16 | cfg | EXACT_ON_SUPPORT | 2523 | 6.022 / 2.054 |
| recursive_one_child_arrays_depth1-16 | stack | EXACT_ON_SUPPORT | 426 | 1.700 / 1.499 |
| recursive_one_child_arrays_depth1-4 | cfg | EXACT_ON_SUPPORT | 183 | 1.666 / 0.175 |
| recursive_one_child_arrays_depth1-4 | stack | EXACT_ON_SUPPORT | 36 | 1.062 / 0.202 |
| recursive_one_child_arrays_depth1-8 | cfg | EXACT_ON_SUPPORT | 663 | 2.891 / 0.488 |
| recursive_one_child_arrays_depth1-8 | stack | EXACT_ON_SUPPORT | 118 | 1.223 / 0.474 |
| recursive_one_child_arrays_depth3-16 | cfg | EXACT_ON_SUPPORT | 2950 | 6.808 / 2.318 |
| recursive_one_child_arrays_depth3-16 | stack | EXACT_ON_SUPPORT | 458 | 1.849 / 1.539 |
| recursive_one_child_arrays_depth3-4 | cfg | EXACT_ON_SUPPORT | 221 | 1.767 / 0.173 |
| recursive_one_child_arrays_depth3-4 | stack | EXACT_ON_SUPPORT | 44 | 1.140 / 0.203 |
| recursive_one_child_arrays_depth3-8 | cfg | EXACT_ON_SUPPORT | 779 | 3.365 / 0.524 |
| recursive_one_child_arrays_depth3-8 | stack | EXACT_ON_SUPPORT | 134 | 1.276 / 0.469 |
| recursive_one_child_arrays_depth8-16 | cfg | EXACT_ON_SUPPORT | 4435 | 9.688 / 3.377 |
| recursive_one_child_arrays_depth8-16 | stack | EXACT_ON_SUPPORT | 529 | 2.122 / 1.721 |
| recursive_one_child_arrays_depth8-4 | cfg | EXACT_ON_SUPPORT | 331 | 3.155 / 0.213 |
| recursive_one_child_arrays_depth8-4 | stack | EXACT_ON_SUPPORT | 55 | 1.307 / 0.202 |
| recursive_one_child_arrays_depth8-8 | cfg | EXACT_ON_SUPPORT | 1219 | 4.170 / 0.765 |
| recursive_one_child_arrays_depth8-8 | stack | EXACT_ON_SUPPORT | 165 | 1.370 / 0.521 |
| json-context0-4 | cfg | EXACT_ON_SUPPORT | 14907 | 57.664 / 10.915 |
| json-context0-8 | cfg | EXACT_ON_SUPPORT | 54646 | 389.416 / 66.295 |
| json-context0-16 | cfg | EXACT_ON_SUPPORT | 162525 | 2845.697 / 499.052 |
| json-context1-4 | cfg | EXACT_ON_SUPPORT | 5875 | 34.457 / 3.319 |
| json-context1-8 | cfg | EXACT_ON_SUPPORT | 25554 | 162.812 / 29.514 |
| json-context1-16 | cfg | EXACT_ON_SUPPORT | 112307 | 1507.150 / 336.366 |
| json-context2-4 | cfg | EXACT_ON_SUPPORT | 18436 | 112.633 / 14.781 |
| json-context2-8 | cfg | EXACT_ON_SUPPORT | 96452 | 817.364 / 104.729 |
| json-context2-16 | cfg | TIMEOUT_WORK_LIMIT | None | -- |
