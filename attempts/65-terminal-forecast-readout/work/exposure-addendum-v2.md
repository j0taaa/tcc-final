# Documentation-task exposure clarification

2026-10-17. Supplement to the frozen V1 source-audit/consumer manifest.

No dataset task/gold JSONL or generated-output record was loaded. However,
the published Mosaic integration README DOES contain a complete public
JevBench example, `hard-sol-b-judge_hard-18`, and that example WAS read during
the source audit, together with aggregate published result tables. It concerns
an exact semicolon-format response and its trailing newline. Thus the original
manifest flag about not reading task/output/gold rows refers to DATA FILES;
it must not be expanded into a claim that no task content was ever seen.

There was no model inference or new evaluation label. Future protocols must
disclose the example/aggregate exposure and cannot call this example an unseen
independent evaluation. The A65 mathematical toy kernels were constructed for
proof checks, not taken from this example or any model. No old result/source
has been overwritten or relabeled as unexposed.
