# V4 — Final prerequisite record before any pretrained forward

2026-10-16. This refines the implementation of the eight criteria and budgets
already frozen in consumer-resource-v4.md at47b7f6c. That contract, all inputs,
gates and gates for decisions remain unchanged. No real pretrained forward,
parameter update, semantic label or competitive measurement has occurred yet.
Classical evidence inference, mixtures and conditional means are not novelty.

The full-V synthetic32-position screen passes three actions (anchor only,
partial release, complete release), with38 classes and all151936 original IDs.
Maximum allocated sampler workspace is421728768 bytes, below2GiB; maximum
CPU/GPU projected-score discrepancy is1.26e-12. Refined toy checks explicitly
include discarded proposals:48 NumPy/Torch CPU/CUDA records match Fraction,
maximum log error1.78e-15 and score error4.45e-15. These are finite checks,
not a global error bound or an exact native finite-RNG law.

A tiny RANDOM1-layer architecture passes five forwards: cropped logits agree
literally, changing the final unmasked token changes earlier predictions, and
masking it removes that effect. The final version also saves/loads a local
random checkpoint through the explicit pinned config, BF16 and no-cache API;
all reloaded weight bits match the rounded originals. None of those calls
uses the pretrained checkpoint or consumes its nine-forward budget.

The initial full-V preflight unconditionally wrote PASS before checking memory.
Its actual memory was below the cap, so its observed PASS is valid. The original
producer/report are retained; the final producer reports RESOURCE_REFUSAL on a
cap violation. Earlier preliminary refinement rows did not record exact working
source hashes; they remain diagnostics without a fabricated immutable producer.
Final sources and results are separately hashed before real heads.

The independent consumer-control test enumerates a rational original-ID JSON
law and verifies both full-triple and known-anchor projected scores. Together
there are19 focused tests. The maintained suite passes224 tests74.209s;
make check and focused Ruff pass. These tests ran before pretrained capture.

consumer_resource.py and consumer-protocol-v4.json specify the next bounded
operation. Input prompt whitespace is one line followed by a newline before
Problem, with the official non-thinking chat template. Per-draw seeds are the
little-endian first eight SHA256 bytes of ASCII52040:case:draw. Sampling is
NumPy floating class/ID suffix sampling; scoring is FP64 Torch log-semiring
autodiff against an independent scaled NumPy forward/outside reference.
These choices do not preserve any other decoder's floating RNG law.

The model weights were downloaded and their complete LFS SHA verified. A
separate Python3.11 environment overlays Transformers4.57.1/tokenizers0.22.1
and appends the unchanged old Torch2.8 runtime; the failed Python3.12 venv
attempt is retained. No pretrained model instance has been evaluated yet.
The runner saves EVERY attempted/completed call, including warmup, original
BF16 head bits, prompt IDs, byte/effect tables, joint draws, three scores,
independent checks and status. Timers are diagnostic resources only. Timeout
successes are not asserted to preserve an unconditional ideal sampler law.

Evidence: work/evidence/consumer-preflight-v4-before-heads. A passing resource
screen merely permits reconsidering a new predeclared complete-cost variance
probe. Own originality, useful training, independent confirmation and the
user's scientific goal remain OPEN.
