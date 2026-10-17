# V8 — Application requirements after the stronger source-work theorem

2026-10-17. Pure written consequence, AFTER V7. No new model or readout
campaign. The eight README criteria remain active: the exact callback/minimax
theorem is positive, but source work alone is not a sufficient real use case.
This note refines criteria1/3/6/7 and does not invent an application or new
benchmark gate. All prior negative native/full-gradient cases stay closed.

## 1. Mean estimation with an expensive downstream score

At UNIFORM three-key masses, let W be within-key variance of a scalar raw
score F, B its between-key variance, V=W+B>0, and s=B/V. The known C6 kernel
gives pair-mean variance

    Var(T_A)=(V/2)*(1-delta*s), delta=26/81.

Let c>0 be the mean iid source/key cost and v>=0 the cost of one score
evaluation, with additive iid work and an identical pair-only consumer.
Ignore extra coordination/setup only to get an OPTIMISTIC necessary bound.
The candidate's cost is A*c+2v, A=386/81; iid2 costs2c+2v. Improving the
variance-times-cost efficiency therefore requires

    delta*s > (A-2)/(A+2r), r=v/c.                       (1)

Even with s=1 this is impossible unless r>2027/1053 (about1.925).
For s<1 the requirement is stricter. This is a written balanced-law condition,
not a measured source/evaluation ratio or a general law theorem. Actual
coordination, fitting and model setup can only make this optimistic threshold
more demanding. Known probabilities, direct noise stratification and biased
search are other legitimate controls when the consumer permits them.

Thus cheap verification of completed generations does not become a useful
mean-estimation application just because the sampler now uses fewer helpers.
A new training/quality campaign cannot be justified by the20.576% source-only
headline or the7.5449% comparison to the common-part control alone.

## 2. A concrete strong regression objection

Suppose, as an ORACLE comparison, that g(x)=E[F|key(x)] is available cheaply
from legitimate prior information. This is extra score information, NOT given
by A63's unknown-score/unknown-law contract. With six iid proposals and the
classical full matching, evaluate F at the two selected original positions
X,Y and use the classical finite-pool regression estimator

    T_CV=(F(X)-g(X)+F(Y)-g(Y))/2 + (sum_(i=1)^6 g(Z_i))/6.

Conditional on the unordered original pool, each matching endpoint has the
empirical-pool marginal. Hence the estimator is unbiased for E F without
knowing the class masses. For the oracle conditional mean, its residuals have
zero mean in every class, independent across the two selected positions:

    Var(T_CV)=W/2+B/6=(V/2)*(1-(2/3)*s).

Its full source/score cost is6c+2v, before its own coordination/preparation.
Compare normalized variance-times-cost values after dividing by V*c/2:

    iid: 2+2r,
    A63: (1-delta*s)*(A+2r),
    CV6: (1-(2/3)*s)*(6+2r).

For EVERY r>=0 and0<=s<=1, whenever A63 improves on iid, CV6 improves on
A63. To see this set s0=(A-2)/(delta*(A+2r)). The difference CV6-A63 is
6-A-s*K with K=(2/3)*(6+2r)-delta*(A+2r)>0. At s0 it equals

    4-[(A-2)*(2/3)/delta]*(6+2r)/(A+2r)<0,

since (A-2)*(2/3)/delta=224/39>4 and6>A. For s>s0 it decreases further.
If s0>1 the candidate never improves on iid in the first place.

This is an explicit ORACLE obstruction, not a theorem that a practical fitted
CV with unknown means always wins. Learning g costs evaluations; wrong fitted
means change the variance, and an unrelated bank oracle is not a native
unbiased estimator. Nevertheless cheap prediction/two-phase regression/RSS
are mandatory competent controls in a proposed mean-loss application. Do not
declare them unavailable merely to preserve the coupling's advantage.

The source-count optimizer remains useful for the exact pair-law operation.
The above objection concerns a DIFFERENT final task, unrestricted estimation
of E F, which need not consume an unweighted original pair. Both contracts
must be presented accurately; the regression control does not simulate the
specified raw pair distribution.

## 3. Consequence for the next real-operation investigation

An admissible application must independently justify why original pair outputs
or score-oblivious simultaneous guarantees are consumed, or demonstrate a
complete-cost advantage in an unrestricted estimation task with strong
regression/stratification controls. Unknown masses alone are insufficient.
Expensive downstream evaluation and informative classes cannot be presumed.

Read-only A44 SOURCE inspection confirms its old rows stored a scalar masked
NLL in addition to full gradients, but no scalar observation values were read
or recomputed for A63 here. A scalar NELBO application would be distinct from
the CLOSED full-gradient branch and needs a separate prospective protocol,
including native count-known controls and CV, before inspecting those scores.
An unbiased normalized NELBO estimate is not an unbiased estimate of its
exponential/perplexity, nor of the model's exact marginal likelihood.

MDLM's [official repository](https://github.com/kuleshov-group/mdlm) documents
a perplexity-evaluation workflow; this establishes a real class of consumers,
not a useful A63 effect or permission to call stored gradients new forwards.
No arbitrary two-output cap may be imposed on best-answer generation. No
fresh semantic/model/data/label/update/timing campaign has been triggered.
Priority, sufficient useful own effect and the original user goal remain OPEN.
