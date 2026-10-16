# A24 consumer V2: complete neural pilot

Producer: `451de4199be5f9884d4c84e886862f314880b571`; frozen protocol: `d2d471810d0099a8d14b042f74bad51257cd93051565bd76ef2432f121dd44d6`. Reporting is post-capture; the gate is unchanged.

Completed campaign: 270/270; statuses: {'complete': 246, 'resource_refusal': 24}; audit errors: 0.
New forwards: 1345 plus 1 warmup. Original-ID/sample checks: 1321; head checks: 1345 (314 distinct matrices).
Literal cursor/full-sparse trajectory matches: 30. Certificate checks against same-canvas exact masses: 735.
Selected candidate: 30/30 complete; maximum observed local-bound sum 9.90859804e-05, below the frozen trajectory allocation.

Scoped paired warm-cost gate: 2/15. Strict timing wins with ALL six controls fully completed: 0/15.

Each ratio is the median of the two paired candidate/control ratios. The displayed worst ratio is the maximum across COMPLETED controls; passing also requires favorable wall AND CPU signs in both seeds. Capacity refusals at3GiB/120s are separate and are not speed measurements.

| Original document / masks | Candidate warm wall (s) | Worst wall ratio | Worst CPU ratio | Capacity controls | Scoped gate |
| --- | ---: | ---: | ---: | ---: | --- |
| y_string_uEscape.json / 4 | 0.0375 | 1.0044 | 0.9951 | 0 | FAIL |
| y_string_uEscape.json / 8 | 0.1149 | 0.8137 | 0.9771 | 0 | FAIL |
| y_string_uEscape.json / 16 | 0.6185 | 0.4102 | 0.5433 | 3 | PASS |
| y_object_extreme_numbers.json / 4 | 0.0460 | 1.1877 | 1.0414 | 0 | FAIL |
| y_object_extreme_numbers.json / 8 | 0.2450 | 1.4755 | 1.3445 | 0 | FAIL |
| y_object_extreme_numbers.json / 16 | 4.4900 | 0.8383 | 0.7571 | 3 | FAIL |
| y_string_accepted_surrogate_pairs.json / 4 | 0.1251 | 1.1363 | 1.0737 | 0 | FAIL |
| y_string_accepted_surrogate_pairs.json / 8 | 0.5002 | 1.4608 | 1.2285 | 0 | FAIL |
| y_string_accepted_surrogate_pairs.json / 16 | 1.7281 | 0.5506 | 0.6427 | 3 | PASS |
| y_object_string_unicode.json / 4 | 0.0943 | 1.1905 | 1.1675 | 0 | FAIL |
| y_object_string_unicode.json / 8 | 0.2757 | 1.1630 | 1.1456 | 0 | FAIL |
| y_object_string_unicode.json / 16 | 0.8328 | 1.2499 | 1.1827 | 0 | FAIL |
| y_object_long_strings.json / 4 | 0.0633 | 1.1215 | 1.1009 | 0 | FAIL |
| y_object_long_strings.json / 8 | 0.4191 | 1.3372 | 1.1146 | 0 | FAIL |
| y_object_long_strings.json / 16 | 8.0984 | 0.8724 | 0.8517 | 3 | FAIL |

These are real new MDLM forwards on ALL five previously inspected documents, not independent corpus confirmation or semantic evaluation. The warm gate includes model execution, softmax, head capture, hashes, IPC, solver and output validation. Model/service loading is outside warm cost; reported cold totals are reconstructions from measured startup, not separately timed cold runs. Journal bookkeeping and service teardown follow the request timing boundary; failed requests retain their measured request cost and status.

The strongest interpretation is a scoped benefit for this CPU posterior/commit consumer. General decoder advantage, sufficient novelty, semantic usefulness, native EPIC/GPU-baseline superiority and publication remain open. Wall-censored COMPLETE outputs are not certified unconditional target-law draws. The existing independent A24 query result remains a different experiment.

Rows SHA256: `9e68be277b1b61ff358ac534007d8cff5feb673c54746a03d18d592f7e33e2c4`.
