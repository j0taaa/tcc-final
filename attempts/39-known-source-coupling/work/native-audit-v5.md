# A39 full-native first-yield pilot — complete descriptive audit

All72 planned records captured before gold export; original producer `52df9a110eae011084796fe00306706dec90a1ec`.
1595 new forwards including four shared initial heads. 3 different first keys; eight common first trajectories unchanged across nine methods.
All per-prefix checks require zero extra forwards; all repeated-seed full IDs independently audited.
Original EOS-to-PAD rewrites strictly after the final terminator: 74 across selected outcomes; other first commitments preserved. This is the native suffix policy, not an adapter change.

| Method | Calls | New forwards (warm) | Median wall s | Median CPU s | Median cold s | Pass@K /8 | Peak allocated GiB |
|---|---:|---:|---:|---:|---:|---:|---:|
| pool4 | 32 | 167 | 5.191 | 5.191 | 5.378 | 3 | 8.930 |
| early_pool | 25 | 167 | 5.145 | 5.146 | 5.314 | 3 | 8.303 |
| adaptive4 | 25 | 168 | 5.155 | 5.155 | 5.323 | 3 | 8.303 |
| mean3 | 20 | 167 | 5.130 | 5.130 | 5.299 | 3 | 8.303 |
| iid2 | 16 | 168 | 5.041 | 5.041 | 5.210 | 4 | 7.542 |
| derange2 | 16 | 167 | 5.142 | 5.143 | 5.311 | 3 | 7.542 |
| seed_half | 16 | 168 | 5.049 | 5.049 | 5.218 | 3 | 7.542 |
| iid3 | 24 | 252 | 7.612 | 7.609 | 7.781 | 4 | 7.542 |
| novelty3 | 24 | 167 | 5.164 | 5.165 | 5.333 | 3 | 8.303 |

Iid3 returns THREE outputs; others return TWO. Gold labels are absent from selection.
These eight paired requests do NOT establish population semantic/latency improvement.
Original failures, all helpers, model queries, dense noise, parsing, copies and memory are retained/charged.
A mathematical expected-forward equality is NOT equal measured forwards in each sampled pair or equal wall time.
Invalid native-contract/error records: 0. No publication/priority confirmation follows.
