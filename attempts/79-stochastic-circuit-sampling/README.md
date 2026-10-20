# A79 — Stochastic arithmetic for a grammatical sampler

## Operation and current claim

This is a small, offline investigation, not a selected TCC contribution. Its
consumer draws one complete original-ID sequence from a frozen product head
conditioned on a checked LL(1) byte grammar. Pins are deltas; aliases remain
distinct; EOS is absent. No model or GPU execution is authorized by this protocol.
The maintained exact posterior API and all earlier experiments stay unchanged.

The candidate evaluates a deterministic, position-decomposable positive binary
circuit with stochastic rounding (SR), then samples using the **stored** operands
of its sum gates. Each rounded gate occurs at most once in any derivation.
Rounded gates may share a uniform only within an exclusive group, and the
dependency graph after contracting groups must be acyclic. Each output receives
fresh arithmetic noise, independent of the randomness used for reconstruction.
Zero values and structural constants are exact. Positive values have explicit
integer exponents and never silently underflow to zero.

For a fixed arithmetic realization, the executed law is

\[
Q_R(x)=W(x)R_x/\sum_y W(y)R_y,
\qquad W(x)=\mathbf1_G(x)\prod_i w_i(x_i).
\]

Write \(u=2^{1-p}\), \(c=u^2/[4(1+u)]\). If every derivation uses at most \(K\)
rounded gates, the written proof gives, for the **mean output law**,

\[
C^{-1}Q(x)\leq\mathbb E Q_R(x)\leq C Q(x),\quad
C=(1+c)^K,\quad
\operatorname{TV}(\mathbb E Q_R,Q)\leq(C-1)/(C+1).
\]

Common gates cancel in the ratio proof. This is not a guarantee for every random
table, adaptive reuse of that table, rounded marginal rankings, or native neural
trajectories. A fixed selector using the original head and the sampled IDs does
inherit the TV bound by deterministic postprocessing. Pruned support would add
its own **valid conditional** omitted mass, separately from numerical error.

Independent agent reviews accepted the mathematical statement under these
conditions; they did not establish priority or useful end-to-end improvement.
No human academic review or Lean verification is claimed.

## Closest controls and unresolved difference

Internal SR and martingale analysis of sum-product DAGs are established:
[Castro et al.](https://arxiv.org/html/2411.13601v2). Conditional precision analysis
is also established: [ProbLP](https://arxiv.org/pdf/2103.00216). Random normalized
posteriors, shared uniforms, Bernoulli races, and random-bit-efficient sampling
are older components. A47/A51/A56 preserve strong exact interval controls.

The possible own difference is narrower: the executed normalized law, its
bilateral envelope with this constant, and safe sharing inside an actual
grammatical circuit, with full bit costs. No complete antecedent was located in
the sources reviewed so far; that does **not** prove worldwide novelty.

A competent stochastic control is required. An elementary moment argument also
gives second-order bias: if \(E R_x=1\),
\(v=\sup_x E(R_x-1)^2\), and \(w=\sup_x E R_x^{-2}-1\), then
\(\operatorname{TV}(E Q_R,Q)\leq\sqrt{vw}\). For SR,

\[
v\leq(1+u^2/4)^K-1,\quad
w\leq[1+3(1+u)^4u^2/4]^K-1.
\]

This deduction came from the priority audit; it is not attributed to a located
publication. The asymptotic order alone is insufficient novelty.

## Frozen offline development protocol V1

This protocol is written before implementation or measurements. Its Git commit
freezes the choices below. These are development cases, not a neural benchmark,
an independent holdout, or a reopened gate from another attempt.

1. **Inputs.** Checked LL(1) languages: all binary words; the two constant-word
   modes; typed Dyck words over `(`, `)`, `[`, `]`. Binary lengths are 16, 64,
   256; Dyck lengths are 8, 16, 24. Include a distinct alias ID for `(` in every
   Dyck support. In addition, correctness fixtures include multibyte emissions,
   epsilon/unary source rules, pins and zero mass. All computational weights are
   explicit dyadics. For each length, use three head profiles: uniform; skewed
   integer weights sampled from 1..31; and near-uniform dyadics
   `2**(ceil(log2(n))+4) +/- 1`, normalized by a common power of two greater than
   or equal to their row sum. Profile RNG seed is 20261020. Original IDs, row
   order and unused mass are preserved. No source or seed is selected after data.
2. **Structure.** Compile through the existing LL(1) compiler without changing
   it. Build only root-reachable binary circuit gates. Conversions may share by
   physical position. Products of alternatives in one cell may share; levels
   within that cell's balanced sum tree may share. Cells follow the existing
   topological order. Verify group ordering and exclusivity structurally, and
   enumerate small fixtures independently. Refuse unsupported structure.
3. **Comparators.** One-output-per-new-head query, common cached structure:
   exact integers without outside/marginal work; SR with singleton groups; SR
   with verified groups; nearest using its sufficient TV precision; an exact
   interval/static-certificate sampler using ordinary binary64 and retained
   uniforms, with an exact fallback. All methods receive the same structural
   simplifications. Also report the precision supplied by the generic moment
   control above. Do not use the rejected A51 ticket method as the main control.
4. **Budget and RNG.** Numerical TV budget is 1/100. Derive p from K and the
   stated bound, before observation. Each timed query uses a new numerical
   evaluation, with an independently specified head; no outside computation.
   Sixteen queries per case/method, query seeds 2026102000..2026102015; one untimed
   initialization of the method. Report all trials, not just a favorable seed.
   The head for query j is regenerated by the same input rule with seed
   20261020+j. Numeric RNG is fresh for each output. Conditional choices use
   exact comparisons and randomness independent of SR. Finite PRNG trials
   exercise an implementation; the theorem's random-bit model remains explicit.
5. **Limits.** Maximum 200,000 circuit gates and 1,000,000 compiler alternatives;
   30 seconds per compilation; 10 seconds per query. Refusals/timeouts/zero mass
   are distinct and remain in results. No increase of these limits after data.
   Interrupted runs keep their partial output. A safety cap on RNG is a refusal,
   not a completed sample drawn from the claimed law.
6. **Record.** Source/protocol/input digests; S, N, K, groups and group sizes;
   compile and circuit-construction costs; p, exponent widths and bit bounds;
   actual message memory including intermediate products/reductions; graph,
   original inputs, buffers and group memory separately; query wall/CPU times,
   RNG bits, output validation, fallbacks and refusals. Python object memory and
   ideal packed payload are different metrics. Timing excludes no work unique
   to a method. Never relabel CPU RAM savings as VRAM savings.
7. **Correctness and stopping.** Exact small enumeration must verify the
   executed law and the claimed envelope, including shared-DAG and grouped-noise
   cases. Validate output IDs, pins, aliases and independent byte recognition.
   Fix correctness bugs with a recorded reason; do not change cases to improve
   a result. If structural or implementation obligations cannot be met within
   this small prototype, report incomplete rather than starting a model campaign.
8. **Decision.** A positive development result requires at least 20% lower
   median complete symbolic-query time **or** actual total resident memory than
   the best applicable control in at least two of the three language families,
   and no correctness failures or unresolved cases. This permits only further
   investigation, not a TCC claim, neural speedup or GPU suitability. Otherwise
   preserve the theorem and mark this development application nonpositive.
   Do not add cases, tune seeds, reduce controls or broaden the campaign to save
   this gate.

The source head, backbone, projection, transfer and neural policy are absent in
this offline experiment and cannot receive a measured improvement claim. Native
FP32, interval refinement and amortization across many samples remain important
objections even if a lower mantissa precision is theoretically sufficient.

## Reproduction

Implementation and results are pending. Use the producer commit for eventual
measurements. No changes are proposed to the maintained library or EPIC baseline.

## Prospective clarifications before any measurements

The written derivations and an improved generic stochastic control are preserved
in [theory.md](theory.md). The latter strengthens the audit's initial moment
constant by a factor of two; both moment precisions will be reported. This is a
theoretical comparison, not a change of cases, seeds, numerical budget or gate.
Sharing is not claimed to improve actual accuracy for every input.

For the development gate, each family's time statistic is the median of its nine
case ratios. A case ratio divides the candidate's median query time by the
smallest median among all applicable controls. No case is omitted. Memory
estimates from reachable Python objects and ideal payloads are diagnostic; they
cannot satisfy the actual total resident-memory gate without matched isolated
process measurements. If those are absent, that branch is inconclusive.

The query contract measures one fresh numerical evaluation per supplied head,
with structure cached. Uniform profiles intentionally repeat numerical heads;
these timings do not establish superiority over a service that caches equal
heads or amortizes an exact preparation across many outputs. A positive outcome
must resolve that limitation before promotion. Measurement instrumentation such
as recursive object-size accounting is outside query timers for every method.
