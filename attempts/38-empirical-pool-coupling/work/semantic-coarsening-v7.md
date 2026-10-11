# A38 v7 — observation coarsening improves coverage and complete-call cost

2026-10-11. NEW mathematical refinement, written BEFORE its implementation
or new timings. The v6 pilot has completed: its results are development
evidence, not measurements of this refinement. The construction of the
four-draw empirical coupling remains classical. Specific priority of this
coarsening theorem and the sharp budget frontier remains to be checked.

## Operation and precise comparative theorem

Let P be any law on original payloads, including unsuccessful executions.
The first output is the literal first iid oracle payload. The second has
the same full marginal P. Run the adaptive C4 reference with a fixed key k,
or the independent mixture of C4 and iid2 with weight lambda in [0,1].
The reference never rewrites tokens, removes failures or consults a gold.

Let l=phi composed with k be a COARSENING of the keys. This identity must
hold on ALL admitted payloads, not just a neural sample. A semantic verifier
f takes values in {0,1} and is measurable with l: it has the same value on
each coarser class. Both samplers use the identical original oracle P.

**Theorem.** Replacing k by l:

1. preserves both original full-payload marginals and the literal first;
2. never reduces pass@2 for ANY such verifier f;
3. never reduces the distribution of the best of two scores, in first-order
   stochastic order, for ANY real score measurable with l;
4. strictly reduces the expected number of complete oracle executions
   whenever two positive-mass fine classes are merged and lambda>0.

This compares two samplers delivering the SAME individual original law.
It is not a comparison of different diversity metrics. The consumer's
observable l and its verifier/score are held fixed on BOTH sides.
It does NOT say variance of the mean of every real score improves.

## Proof: all Boolean consumers, without knowing the correct answer

Write p_i=P(k=i), a=P(f=1), q=1-a, and

    C_A=sum_(i:f(i)=1) p_i^2,
    C_B=sum_(i:f(i)=0) p_i^2.

The written C4 covariance identity in v1, applied to g_i=f(i)-a, yields

    pass2_C4 - pass2_iid2
       = (1-C_A-C_B)*(q^2*C_A+a^2*C_B)
           +(q*C_A-a*C_B)^2
       = q^2*C_A+a^2*C_B-C_A*C_B.                 (1)

No correct-answer label is needed by the sampler: f enters only this proof.
Since f is constant on coarser classes, coarsening merges classes WITHIN
A or WITHIN B. It increases C_A and C_B. Always C_A<=a^2 and C_B<=q^2.
The expression in (1) has partial derivatives

    q^2-C_B>=0,       a^2-C_A>=0.                (2)

Therefore coverage cannot decrease. The mixture's improvement is lambda
times (1), since its other branch is exactly iid2 under both partitions.
The marginal law and literal-first property hold for each fixed key by v1/v2.

For one merge of two successful classes of masses u,v, the coverage gain
increases by 2*lambda*u*v*(q^2-C_B). For an unsuccessful merge it increases
by 2*lambda*u*v*(a^2-C_A). Strictness is conditional: the opposite Boolean
side must still contain at least two positive-mass fine classes. For example,
merging multiple correct spellings when there is a single wrong class can
save work while leaving coverage exactly equal. Constant verifiers have
no coverage gain and must never be reported as strict improvement.

For countably many classes, apply finite merges and pass to the limit.
Nonnegative sums converge by monotone convergence and total probability
is one; C_A and C_B converge to the coarser squared masses. Equation (1)
is continuous in these two bounded scalars. There is no finite-alphabet
or benchmark restriction in the coverage statement.

## Proof: best-score stochastic dominance

For each real t, use the Boolean verifier 1[score>t]. It is measurable with
l. The previous result says

    Pr[max(score(X_l),score(Y_l))>t]
       >=Pr[max(score(X_k),score(Y_k))>t].         (3)

This is precisely first-order stochastic dominance. Consequently the
expectation of each bounded nondecreasing utility of the best score cannot
decrease. Extensions to unbounded utilities require the usual integrability
assumptions. This is a BEST-of-two result, not a claim about the joint sum.

## Proof: complete oracle executions and costs

For C4 write c=sum p_i^2 and s3=sum p_i^3. V2 gives

    E N=4-2c+s3.

Merging fine masses u,v changes this expectation by

    -4uv+3uv(u+v)=uv[-4+3(u+v)]<=-uv<0.         (4)

The mixture has expectation 2+lambda*(2-2c+s3), so its change is lambda
times (4). Sequential merges and dominated convergence give the countable
case (N is bounded by four). Within this family, the consumer's coarsest
sufficient observable is thus optimal in BOTH coverage and call count
against every finer map through which that observable factors.

If fresh iid oracle executions have arbitrary payload-correlated complete
work W with finite mean w, finite Wald from v4 makes the oracle-work saving
equal to -w times the change in (4). It includes unsuccessful generations,
all forwards, parsing/retries and reconstruction. Common preparation and
common measurable processing of the retained pair must also be counted.
The two pairs need not have the SAME joint law after coarsening, so the
v4 equal-law cancellation of downstream work DOES NOT apply automatically.
Charge the actual downstream operation or justify an invariant cost.

Semantic-key computation and comparison can cost more than syntactic keys.
The total-time advantage requires the saved complete-call work to exceed
the additional key/coordinator/downstream cost. There is no unconditional
hardware latency theorem, nor improvement over generating more iid outputs.

## Important counterexample: not all real-score variances improve

Take four fine classes of mass1/4 and scores (0,0,1,-1). Merge only the first
two, which have identical scores. The mean is zero. The C4 negative covariance
has magnitude3/32 before merging and5/64 afterward; it becomes LESS negative.
Thus the variance of the two-score mean increases by1/128. The mixture
scales this increase by lambda. Both samplers still have nonpositive
covariance, and the best-score stochastic dominance remains true.
Do not turn the Boolean/maximum result into a universal real-score-variance
claim or a Loewner-order claim.

## Application: executable recursive JSON, with a sound observer

A dLLM plus the unmodified EPIC/CFG decoder supplies complete original
arithmetic JSON payloads. A deterministic rational interpreter is the real
consumer. Its observation is the computed rational value, or a single FAIL
value for incomplete/invalid/unexecutable/resource-refused payloads. All
original token IDs/text/statuses remain in the retained samples. Gold-free
evaluation groups DIFFERENT trees which execute to the same value.

Every semantic correctness verifier comparing the result with an external
correct value is measurable with this observer. The theorem therefore
improves or preserves its pass@2 without being told that correct value.
Numeric-distance scores also give the best-score statement, with the
failure score and integrability specified. This is translation of language
to an executable tree, not using a dLLM to invent Boolean rules.

For an implementation, define the fine key with the SAME raw-text length
limit as the interpreter BEFORE canonical JSON parsing. Its typed AST
normalizes rational numeric literals and rejects duplicates/non-JSON
constants. The observer's depth, node, intermediate-bit and arithmetic-error
rules are deterministic functions of this normalized AST. The raw-text
guard matters: without it, whitespace variants of one AST can straddle
the interpreter's length budget and violate l=phi(k). This must be fixed in
the NEW observer wrapper, not silently added to frozen v6 measurements.

Exact rational tree evaluation costs polynomial bit work in the explicit
tree and numeric literals; the implementation additionally declares hard
length/depth/node/intermediate-bit limits. These are observer outcomes,
never discarded samples. A finite neural run has a finite output domain;
do not transfer the infinite-domain exact minimax value without the v5
finite-M correction or another argument.

## Eight criteria before another implementation

1. **Use:** return original structured dLLM proposals to a consumer of their
   executable result. Improve semantic coverage and complete-call work versus
   the SAME coupling keyed only by syntactic JSON identity, without golds.
2. **Significance:** the candidate is a distribution-free Pareto theorem
   plus the sharp budget frontier. Semantic grouping, empirical ranks and
   arithmetic interpretation themselves are known; priority of these precise
   comparative statements remains OPEN, and publication is not guaranteed.
3. **Choice:** any positive-mass semantic alias merge saves full oracle calls
   in expectation; every observer-measurable verifier is no worse. Cheap iid
   and biased novelty search remain competent practical controls and may win.
4. **Math:** equations(1)--(4) and their proofs do not depend on code or
   benchmarks. This is comparative benefit, beyond sampler correctness.
5. **Experiments:** validate sound coarsening and exhaustive raw laws first.
   A subsequent protocol must freeze inputs, controls and full costs BEFORE
   new outputs. V6 is already observed development, not held-out evidence.
6. **Full cost:** charge ALL full native helper executions, observer work,
   preparation and downstream processing; no fictitious expensive verifier
   or relabelled v6 timing, no claim against all EPIC policies or pass@1.
7. **Objection:** iid3 may dominate best-answer search at similar generation
   cost, and informed couplings can be stronger. The real-score variance
   counterexample above limits the theorem. No speed claim without costs.
8. **Article:** still needs exact-priority audit, independent algebra/code
   checks and a convincing full-cost consumer. No human review or acceptance
   is invented; this file alone does not achieve the user's publication goal.

