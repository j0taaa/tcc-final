# V5 competent classical grid control passes

2026-10-17. Written contract `d24974e` precedes source
`217b752df7c4ab29a129c0a7398c27d3e01c94d6` and its single execution.
Direct observed exit0. Evidence/raw log/origin under `evidence/v5/`.

The control is ordinary weighted-automaton composition, bounded integer-sum
DP and moment semirings. It tracks native node, finite unfinished number/parser
state and sum in[0,100K], with mass, K first moments and total squared moment.
It NEVER enumerates all101^K completed value vectors. It includes pinned prefix
values, offset, budget, original aliases, edge-mass/state-path sampling and
within-edge argmax. Normalize each semantic vector BEFORE integrating; include
incomplete paths in the denominator and common uniform all-zero fallback.

Four prospective check groups PASS:114 valid numerical spellings, eight
invalid spellings/four EOT/PAD controls; three exact Fraction laws with split
number prefixes, completed prefix fields and several fields within a token;
per-sum first/second moments plus conditional means/variance/alpha against
direct independent rational evaluation; ALL12 native fixture families/device
pairs compared to independent full enumeration. These12 use one fixed seed17
and read_only false, executing12 additional native constrained steps/24 native
proposals. They are separate from V4's48 cases, not a rerun of its full matrix.

The native comparison's discrepancies are at rounding scale (full values in
origin.json), below both frozen5e-5 tolerances. Zero-sum has exact variance0;
partial-canvas completion probability is about0.0041 and is kept. These are
constructed logits, not a model measurement. Caller RNG is restored.
The three rational laws all reject naive normalize-after-mean aggregation.

'Exact-grid' describes exact retention of numerical values/semantic states.
Native path weights use ordinary float64 operations, not exact rational
exponentials or a certificate of the finite torch.multinomial law. Tiny
alpha overshoots such as1.0000000000000002 are raw rounding residuals retained
in records; they are not valid exact probabilities. A future certified
variance/loss bound must address numerical error rather than silently clamp
these values and call them exact.

No pretrained model/tokenizer, dataset/gold row, new neural forward/update,
competitive timing or maintained full-suite rerun. This strengthens the
mandatory control; it is not own new theory or a positive neural result.
If a real application makes this DP cheap, it can eliminate ideal terminal
variance completely and is a better control than more helpers. Neither a
passed native adapter nor classical conditional averaging settles novelty.
T8803 still needs a separately frozen, feasible named model/resource/variance
necessity screen BEFORE heads/labels, preserving all unfavorable cases and
full costs. There is no authorization from these correctness checks for a
large quality/training campaign or a claim that the scientific goal is met.
