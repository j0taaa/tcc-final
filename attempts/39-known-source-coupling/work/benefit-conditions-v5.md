# Comparative magnitude, beyond duplicate-seed avoidance

2026-10-11. Algebraic consequences of v1, not native empirical results,
new independent principle or a benchmark family chosen for a victory.

For ANY full-source finite score f let `V=Var(f)` and let `B=-Cov_C4(f)`
computed by equations3--4. Iid2's unbiased mean has variance `V/2`;
uniform seed derangement has `V*(1-1/(M-1))/2`; C4 has `(V-B)/2`.
Thus the exact condition for C4 to improve that STRONG control is

    B > V/(M-1).

No assumption that this always holds. Both means preserve the original
decoder expectation. Pair best-score coverage satisfies the same covariance
comparison when f is a Boolean threshold. Neither implies semantic
calibration, pass1 improvement or all-function dominance over derangement.

For TWO observation classes of sizes t and M-t, with mean scores h0,h1,
let `r=t*(M-t)` and `delta=r*(r-4+6/M)/(M)_4`. V1 gives

    B = delta*(h0-h1)^2 + sum_i J_ii*sigma_i^2/(n_i-1).

An absent/singleton within-class term is zero. Consequently the easily
interpretable sufficient condition is `delta*(h0-h1)^2>V/(M-1)`.
If the class proportions tend to p and1-p in(0,1), with bounded scores
and nonzero stable class-mean difference, delta tends to `p^2*(1-p)^2`.
This improvement is constant instead of vanishing as1/M. If the conditional
means are equal, or the partition has a rare/uninformative key, the proposed
benefit can disappear. This is a CLASS-information condition, not an
assumption that the answer is known or written into the grammar.

Native corollary: at the audited first-yield boundary, both unbiased outputs
have the same expected neural-forward work as iid2/derangement. The helper
prefix cost still exists. For one fixed repeated-request application with
expected complete cost W_iid and W_C4, independent batches and variance V>0,
the variance-times-expected-work comparison is

    C4 improves iid2 iff W_C4/W_iid < V/(V-B).

For a predeclared n independent batches, variance is divided by n and
expected work multiplied by n, so this product comparison is exact. It
does not assert unbiasedness after stopping at a fixed elapsed-time budget
when cost and score are correlated. Shared one-time preparation must be
included as amortized cost under the same n for all controls.

This is an expectation/Monte Carlo efficiency condition, not a confidence
interval or latency guarantee inferred from two measured repetitions. Full
preparation, copies, decoding, failures, output and precision must enter W.
The native pilot must assess whether ANY useful terminal score/consumer
has this benefit, against more iid outputs/biased search as well. A generic
unbiased two-sample result alone does not establish that application.
