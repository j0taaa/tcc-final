# Full cost, more iid outputs, and the necessary application boundary

2026-10-11. Written AFTER the negative A32/v4 pilot and BEFORE any A34
native experiment. Companion to theory-v1; no new measurements. These are
mathematical conditions, not asserted properties of the deployed model.
Wasan1964 Section3 already trades observation cost and variance: that general
principle is a precedent. The sharp output-pair frontier is still a candidate.

## 1. A real two-stage operation, and costs without hidden work

The consumer requests TWO complete original-law JSON/DSL candidates for later
selection, execution, auditing or human review. A native structured decoder
first draws an accepted transition U from a frozen head; the two retained
transitions are then independently continued and consumed. The binary class
must depend on an ACTUAL accepted transition, including its failure status,
not an ignored or rejected raw proposal. The verifier used to evaluate final
coverage need not be available to the sampler.

Let F be the common preparation/head cost, c the mean cost of ONE complete
transition draw, and v the mean remaining continuation/consumption cost per
retained draw. All costs use one declared additive resource (e.g. CPU work),
not a mixture of CPU and wall units. c includes noise, parser calls, rejections,
recovery and state copying; v includes subsequent forwards and required output
work. Loading amortization is separately stated. Parallel latency is not
automatically the sum of these costs.

For iid draw costs C_i and an integrable stopping time N, Wald's elementary
identity gives E sum_(i<=N) C_i = E N * c: the event N>=i is determined before
draw i, even when its cost and class correlate. Preserved payload marginals
give expected continuation cost2v. Thus the ruin pair at barrier r costs

    C_pair = F + r*c + 2*v,
    C_iid2 = F + 2*c + 2*v.

This is an EXPECTED-work statement. Worst-case and physical timeout require
the separately proved count cap, which changes the joint law. An auxiliary
transition requiring additional model forwards charges those forwards to c;
a cached head does not make all subsequent work free.

## 2. Exact coverage and throughput condition

For a terminal event, let mu_j be its conditional success probability after
an original transition of class j, p=P(class1), and mu=p*mu_1+(1-p)*mu_0.
Independent continuation and theory-v1 give

    h_iid2 = 2*mu-mu^2,
    h_pair = h_iid2 + Delta,
    Delta = delta_r(p)*(mu_1-mu_0)^2.

No semantic monotonicity is assumed. A class with mu_1=mu_0 has ZERO gain and
is a bad choice regardless of how cheaply it can be classified.

If 0<mu<1, cost per covered request is lower than iid2 EXACTLY when

    (r-2)*c < (F+2*c+2*v)*Delta/h_iid2.

For r=3, p=1/2 and a perfect class signal (mu_1=1,mu_0=0),
delta=1/12, h_iid2=3/4, h_pair=5/6. The condition is
`2*v+F>7*c`. These values are examples of the theorem, not a dataset/result.

## 3. A competent same-budget iid comparator can generate more outputs

Do NOT compare only against iid2. With r=3 and the SAME expected resource
budget after F, iid can afford expected terminal count

    kappa=(3*c+2*v)/(c+v)=2+alpha, alpha=c/(c+v).

Allow iid to choose any integer K with E K<=kappa BEFORE seeing outputs or
the unavailable verifier. Concavity of1-(1-mu)^K on nonnegative integers
shows its maximum coverage is the adjacent-count mixture: K=2 with
probability1-alpha and K=3 with probabilityalpha. This is not a deliberately
weak implementation or an assumption that iid must waste its spare budget.
The optimal iid coverage under THIS nonadaptive-count contract is

    h_iid_budget = h_iid2 + alpha*mu*(1-mu)^2.

Consequently the pair beats ALL such iid output-count plans iff

    delta_3(p)*(mu_1-mu_0)^2 > alpha*mu*(1-mu)^2,
    delta_3(p) = [p*(1-p)]^2/[1-p*(1-p)].

For the balanced perfect-signal example this is simply v>c/2. A uniform
sufficient condition on p in[a,1-a] and |mu_1-mu_0|>=d is

    alpha < (27/4)*[a*(1-a)]^2*d^2/[1-a*(1-a)].

Proof: delta_3 increases with z=p(1-p), and mu*(1-mu)^2<=4/27.
This exposes the actual application requirement: cheap transition draws,
expensive retained continuations, and nontrivial class signal. It is not a
claim that arbitrary real model predictions satisfy those inequalities.

## 4. Objections that cannot be hidden

If an oracle draw ALREADY produces and verifies the entire candidate, v=0.
For a perfect class signal and ANY p in(0,1), THREE iid outputs have STRICTLY
higher coverage than the expected-three-draw ruin pair:

    [1-(1-p)^3] - h_pair = p*(1-p)^4/[1-p*(1-p)] > 0.

Thus applying this scheme to expensive complete-output oracles merely to
return two outputs is not a competitive proposal. The cheap-prefix boundary
must be demonstrated faithfully, not asserted by omitting forwards.

If a reliable verifier is available during generation and an unbounded
sequential retry policy is allowed, iid can stop at its first success; in the
balanced perfect-signal case its expected cost is2(c+v), with coverage1.
That is a DIFFERENT and potentially better operation. The pair is not a
universal optimal verified-retry algorithm. Fixed two-output batches, delayed
verification and latency/resource constraints must be real requirements.

Probability-aware maximal coupling, raw-noise stratification, deterministic
and mixed-temperature alternatives remain mandatory practical comparators.
The sharp sample-only theorem excludes their extra information; A35's counting
observation does not prove that every good coupling must calculate p.

## 5. Refinement of the eight criteria

The use/consumer is a two-candidate batch before final verification. The
candidate contribution remains the sharp regular sample-only pair frontier,
with this exact cost/coverage corollary; the two-stage cost principle is known.
Choice is justified ONLY under the displayed class-signal/cost conditions.
All comparisons above are written mathematical statements, not timings.
The next experiment must measure an ACTUAL native accepted-transition kernel,
charge all work, preserve iid's extra-output budget and raw-information
controls, and select classes from inputs/development only. Cheap prefix and
class signal are the strongest objections. Specific priority, meaningful
native application and publication significance are still unresolved. No
claim of a useful general EPIC win follows from this note alone.
