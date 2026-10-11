# A39: terminal guarantees at equal expected neural-forward work

2026-10-11. Written BEFORE adapter/forwards. This is not a wall-time theorem.

## Original native boundary and complete retained states

Use the unchanged pinned EPIC LLaDA generator at its FIRST yield, including
an unchanged/unsuccessful terminal yield. Preserve the literal generator,
all control locals, original token IDs and private CPU/CUDA/Python/NumPy RNG
states. Do not call a failed yield an accepted completion, filter it or
redraw it. Original continuation is advanced to exhaustion only for the
two retained payloads. This gives a deterministic finite-seed original
trajectory map under the declared deterministic inference/source policy.

For the pinned source, one block128/steps16 has eight transfer attempts in
the first step. With classifier-free guidance disabled, the first model
query uses the common initial mask canvas. The fast compatible branch
yields after commits; the fallback either commits and yields, completes
and eventually yields, or yields and RETURNS on its failure guards.
Those guards and retries do not query the model again before the first
yield. Any error is an original outcome, not omitted. A per-candidate
query/forward audit must verify this property for the actual adapter.

An immutable common initial prediction is prepared and CHARGED equally
to all methods, including independent/seed controls. Every native caller
receives its own logits clone, preserving mutation behavior. Each helper
first-yield query then needs ZERO additional neural forwards. It still
allocates buffers, samples dense GPU noise, performs softmax/argmax,
parsing/rejection, copies logits/state and creates a private generator.
Those costs and peak memory remain charged.

## Theorem: final-output marginals and comparative guarantees

Let source s range uniformly over M seed values. The original full result,
including failure, is Z(s), and its number of neural forwards AFTER the
common initial prediction is H(s). The first-yield key is k(s); original
hidden state/RNG is retained, not reconstructed from k. Apply the finite
source coupling to first-yield queries and continue its two selected
literal generators.

Uniform full source marginals imply EXACT original final-result marginals,
even when subsequent logits depend arbitrarily on the retained states.
The full-source covariance theorem applies to f(Z(s)) for ANY terminal
verifier/finite score. Hence pass@2 and best-score distribution are no
worse than two iid original EPIC runs. Pass@1 is unchanged. No gold or
assumption about future logits stability is used.

With no cross-trajectory future cache (equally for all comparators),

    E total new neural forwards = 1 + 2*(sum_s H(s)/M),

the SAME as two independent runs using the same common initial prediction.
The equality is marginal linearity, not optional stopping or an empirical
timing estimate. If independent future randomness remains, replace H(s)
by its conditional expectation and model the key law appropriately: do
not automatically use deterministic finite-population formulas when
repeating one source can produce different keys.

This is a conditional mathematical improvement in RESULT per NEURAL work,
not proof of reduced total physical computation. Extra auxiliary sampling,
head clones, grammar checks, peak memory and coordination must be measured.
More iid outputs/biased search and seed couplings are competent controls.
The source model is the actual finite-seed original decoder policy, not
an exact idealized continuous-softmax dLLM or an infinite alphabet.

## Same-law pool comparison with arbitrary query costs

For full-four, safe-early and adaptive C4, the retained FULL source-pair laws
are identical. Their common future processing therefore has the same
distribution and expected work. On a common virtual four-source tape,
adaptive N<=early N<=full N pointwise. Omitting query four saves its
nonnegative ACTUAL first-yield work, including key-correlated failures.

Without replacement, the next query cost need not be independent of the
stopping decision. DO NOT write saving=(2c2-c3)*mean-query-cost using iid
Wald. The exact saving is E[1_(adaptive stops at3)*W4] versus full and
the corresponding subset event versus early. A positive uniform lower
bound on W4 gives a lower bound by its skipped-query probability; overhead
and different compiler preparations still have to be added explicitly.

The preceding seed-pair-law equality does not permit only one method to
reuse discarded helpers in future computations. A common future cache
depending solely on the retained pair has the same law for the three pools;
it can differ between a pool and independent seeds and must be measured.

## Mandatory cheap source-aware countercontrol

Uniform source derangement chooses first uniform and second uniform among
the M-1 other indices, preserving each original seed marginal with TWO
native trajectories. For every full score its covariance is-Var(f)/(M-1).
It has no extra first-decision helpers and can beat the candidate on some
scores. Deterministic half-seed rotation is also a control, but has no
arbitrary-verifier negative-covariance guarantee. Include BOTH.

The candidate's point is nonnegligible decision-class dependence when the
initial native lookup is cheap relative to continuation, while preserving
original marginals and explicit full-source guarantees. This requires a
real useful case, not an invented slow verifier. No native adapter, data,
competitive wall-time victory, human review or publication claim is made.
