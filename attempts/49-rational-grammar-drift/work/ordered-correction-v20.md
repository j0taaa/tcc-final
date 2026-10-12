# V20 — Correct minimum-angle rotation; repeat the unchanged gate

V19 sourceb0c678a and its first failure are preserved. Canonical generators
lie in the right half-plane. The earlier angle has a POSITIVE determinant
with the later angle; V19's minimum scan used the opposite comparison.
Correct that sign only. The geometric/sweep/product proof remains unchanged;
this is an implementation error, not a new theorem or a relaxed oracle.

The eight answers and contract in ordered-product-proof-v19.md still apply.
Repeat every frozen geometry, exhaustive projection, ordered-image, product,
extreme-precision and original-ID forest case. No public run or improvement
claim before the entire correctness gate passes. Preserve any further failure.
