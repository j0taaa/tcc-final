# V18 pre-data addendum — All-pair mean-gap estimator is primary

2026-10-16, AFTER the initial cross-half oracles/full277 tests, BEFORE ANY V18
real auxiliary draw or variance calculation. The original written contract,
prototype and logs are retained in conditional-probe-v18-cross-initial.
No gate threshold, candidate/control family, question or draw count changes.

For independent conditional replicas H_q0,H_q1 of equal count n=64, let
their sample means be m0,m1 and let

    W=.5*(trace(sampleCov(H_q0))+trace(sampleCov(H_q1))).

Use as PRIMARY mean-gap estimator

    D_U=.5*||m0-m1||^2-W/n.

Its expectation is .5||mu0-mu1||^2, since the sample-mean squared gap has
additional variance W/n. Equivalently it uses all distinct within-path pairs
and all cross-path pairs. It is the usual U-statistic/Rao--Blackwellization
of the cross-half construction over independent random partitions. No new
statistical principle is claimed. The nonnegative full-data paired estimate
D_U+W=.5||m0-m1||^2+(1-1/n)W avoids unnecessary cross-half partition noise.
D_U and D_U+stratified_noise may still be NEGATIVE; never clip them. Preserve
the cross-half estimate as a DIAGNOSTIC for every method/question/block too.

Every fixed configuration/family uses D_U in the SAME frozen development
decision, without selecting between estimators after seeing real data.
Moment formulas/stratified batch treatment, original-visible-path uncertainty,
RLOO limitation and zero-extra-cost20% rule remain as written. Independent
finite-law oracles must verify this estimator before any real V18 samples.
