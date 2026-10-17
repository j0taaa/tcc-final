# V4 fixture correction, before a second native run

2026-10-17. V3 source `3e62727105068826281b93b4ff6252bcad047e3c`
was frozen before the first actual native execution. Its observed exit code
is1, with16 completed CPU records,34 native step invocations and helpers
already charged in the literal summary. No CUDA fixture was reached. The
exact runner, records, log, traceback and metadata are preserved under
`evidence/v3-draft/`; this execution is not an all-case PASS.

The assertion that the zero-sum fixture ONLY produces zeros was wrong:
position3 fixed to original token `0` can be extended by `.1`/`.10` or other
decimal pieces before the closing object. Position1 fixed to `0.00` already
uses the native two-decimal maximum. The intended zero-variance control must
also fix position3 to `0.00` (original ID10), so neither number can acquire a
positive suffix. This corrects a synthetic fixture, not the sampler, observer,
readout, independent path enumeration or theorem. Do not relabel V3.

Change ONLY that pin and rerun ALL48 prospective CPU/CUDA records, not only
the failed case. Preserve all previous seeds, read_only modes, budgets,
600s/2GiB/500000 guards, tolerance5e-5 and literal state/RNG checks.
The pinned native source remains unchanged. This is a correctness preflight,
with no pretrained tokenizer/model/data/labels or new neural forward.

Freeze the corrected runner before execution in a new output directory.
Passing does not establish independent finite-RNG samples, native forecasting
quality, practical benefit, own novelty or the user's scientific goal.
