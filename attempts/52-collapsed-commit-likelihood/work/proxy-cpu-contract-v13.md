# V13 — Separate CPU correctness replay, written before code/queries

2026-10-16. The frozen V12 GPU replay remains NOT_RUN after its startup
isolation refusal. Do not relabel it as a pass or weaken its isolation rule.
The other user's GPU process is still active after four minutes; do not kill
or contact it. This separate CPU implementation tests the mathematical
operation, with no CUDA context, model construction or pretrained forward.

V12's eight scientific criteria, regular-subset proof, all70 transitions,
known labels, original IDs/aliases/EOS/fixed bits, independent NumPy/autodiff
comparisons, structural-zero rules and1e-7 absolute/scaled-relative tolerances
are unchanged. No query has yet been computed on these original heads for
either version. V13 is a resource-portability refinement, not a new scientific
mechanism or new variance/cost claim. Ordinary weighted inference remains the
same control. All errors/refusals/zeros and semantic-correct proxy misses stay.

Change ONLY execution resource: PrefixTorch uses device="cpu", four threads;
remove CUDA/NVML calls, and track entire process peak RSS via getrusage.
Peak RSS must be<=2GiB, whole replay<=1200s, each numeric operation<=60s.
Other users' GPU activity is irrelevant to CPU numerical correctness; host
load precludes interpreting diagnostic wall/CPU times as competitive results.
Do not claim whole-GPU isolation or GPU proxy validation from a CPU pass.
Strict functionality requires all70 PASS, no errors/refusals. Input manifests,
runtime, source and driver freeze before queries. Preserve the V12 producer,
protocol and refusal alongside this independent version.

After small regression checks of the device/memory/serialization adaptation,
run the full CPU replay ONCE. A pass only permits considering a separately
frozen full-cost variance study; it is not training authorization, sufficient
originality or goal completion. No extra heads/samples/updates/labels.
