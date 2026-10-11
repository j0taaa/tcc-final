# A38: complete oracle work, variable-cost calls and decoder continuation

2026-10-11. This extends the written decoder corollary without claiming a
new native experiment. Counts alone are not physical-time measurements.

## Complete calls with costs correlated with their payloads

Let each fresh iid oracle execution return (Z_i,W_i), where W_i>=0 counts
its COMPLETE work: forwards, parser retries, reconstruction, statuses, copies
and all computation needed to obtain and retain that payload. W_i may depend
arbitrarily on Z_i. Assume w=E W_i<infinity and identical fresh executions;
an optional fixed prepared head/model is common and charged separately.
The coupler's decision to request call i is measurable BEFORE that call.
Since N<=4, no unbounded optional-stopping regularity is required:

    E sum_(i=1)^N W_i
      =sum_(i=1)^4 E[1_(N>=i)*W_i]
      =w*sum_(i=1)^4 Pr[N>=i]=w*E N.                       (W)

This is a standard finite Wald identity, not a new theorem. It includes
expensive failed calls; filtering them before defining P would change the
operation. Shared caches that change the iid per-call work violate the
identity's premise. Rebuild the cost model or measure them instead of
silently asserting independent timings.

## Same law, strictly less expected oracle work

The classical full-four grouped-rank coupler, v1's safe early version and
v2's adaptive version have the SAME joint original-payload law. Each selects
a nonfirst observed index using only canonical keys; conditional raw aliases
have independent P|key laws. The rank implementation must randomize within
key blocks and never select the same occurrence as first. Equality solely
of rendered text would not suffice for retained generator/RNG payloads.

Thus the expected complete oracle work is respectively

    4w; (4-c)w; (4-2c+s3)w.

The adaptive saving is (2c-s3)w versus full four and (c-s3)w versus safe
early four. It is strict for every nondegenerate canonical law with w>0.
Moreover v2's pointwise minimum-call theorem implies minimum EXPECTED
oracle work among its universal simultaneous atom-maximizers under the
same iid-cost model. Side information/informed controls remain outside
that lower-bound premise and are legitimate practical alternatives.

For any subsequent measurable processing of the retained pair, equality
of FULL pair law makes its expected work and output law identical too.
This includes continuing the original private native generators with their
retained state/RNG, adaptive later logits, checking the two final results,
and a common downstream cache whose behavior depends only on that pair.
It does NOT permit future processing to reuse a discarded helper's result
in one method only, or to depend on a different helper/RNG transcript.

With common setup B, expected downstream work Q and coordination overheads
h_full/h_adaptive, the expected total saving is

    (2c-s3)*w +h_full-h_adaptive.                           (C)

An improvement is therefore proved when the extra overhead is less than
the saved full-call work. Physical wall/CPU timing of this inequality still
requires measurement. Model loading/preparation is included in B for both;
auxiliary full generations are NOT free. For accepted-state callbacks with
one common head, the head belongs to B and all remaining parsing/retries,
head copies and generator state creation belong to W_i.

## Size and bit work

The reference stores at most four original payloads and four keys, executes
at most four key extractions and O(1) equality tests, and uses at most one
uniform2/uniform3 choice per adaptive pair. Exact uniform3 from fair bits
costs8/3 bits in expectation by two-bit rejection. The half mixture adds
one independent fair bit and invokes the adaptive rule with probability1/2.
No large integer weights, probabilities or approximate CDFs are constructed.
Key extraction/equality costs must include original byte/state lengths;
the payload itself is not O(1) bytes just because there are four references.

## Why the result is useful, and what it does not establish

This is an exact reduction in COMPLETE work while preserving the same
pair quality distribution of a competent classical method. It is distinct
from proposing a new local quality score. The cap4 minimax frontier adds
an optimal worst-case benefit/budget guarantee, rather than calling the
existing rank construction a new principle.

The mathematical operation applies to original CFG-constrained dLLM
samplers whose output/accepted-state probabilities cannot be cheaply
enumerated. It also applies to other black-box samplers; the general theorem
does not become specifically novel just because the oracle is a dLLM.
Its priority and significance for publication still need adversarial comparison.

Compared with iid2 it consumes extra oracle calls, albeit it preserves
marginals and improves pass@2 for every verifier. Compared with iid3/4 or
an informed coupling it can lose after complete resource accounting.
No general EPIC latency, semantic, pass@1 or sample-budget superiority is
claimed. No artificial slow verifier is introduced to manufacture a win.
