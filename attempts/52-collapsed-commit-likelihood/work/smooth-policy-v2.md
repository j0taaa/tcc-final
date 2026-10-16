# V2 — A different, smooth action law, before implementation

2026-10-16. This changes the policy EXPLICITLY. It is not a repair of Mosaic,
not its native finite-PRNG law, not PL, and not preservation of V1's action or
word marginals. V1's written proof, moving-boundary objection and numerical
reference remain independently archived. Bernoulli planners already exist in
dUltra and Learning Unmasking Policies; weighted counting/OR products and
conditional-score variance reduction are classical. Specific originality and
practical significance of the token-conditioned/grammar-collapsed application
remain open. Only a minimal independent oracle is justified at this stage.

## 1. Joint law, including guaranteed progress

Use V1's finite unambiguous original-ID language L, active positions M, positive
differentiable weights w[i,v], and positive partition Z. Fixed IDs, aliases and
true EOT/PAD semantics are retained. Let g[i,v] be a differentiable probability
STRICTLY between0 and1: release position i conditional on proposing original
ID v. It may use the probability of THAT token rather than the row maximum;
actual normalization and differentiation through that confidence are charged.
No independent full neural forward is needed to read already-produced logits.

For x in L and bits b over M, define the unnormalized joint weight

    K(x,b)=W(x)*product_(i in M) g[i,x_i]^b_i (1-g[i,x_i])^(1-b_i).

Condition the JOINT pair on b being nonempty. Its partition is

    Zplus=sum_(x in L) W(x)*(1-product_(i in M)(1-g[i,x_i])) > 0.

The policy draws (X,B) with law K/Zplus, exposes the nonempty action (B,X_B),
and forgets ALL unretained IDs. The next neural input/control depends only on
that action and the old sufficient state. Therefore each transition progresses;
at most |M_initial| transitions complete a bounded canvas. Each is extendable
to an L-word, so the final original word belongs to L. Do not stop on a newly
exposed EOT while earlier positions remain masked; termination is an explicit
completed-canvas/block policy, not an assumed shortcut.

This law can equivalently draw X from W/Z, then independent Bernoulli bits,
and restart BOTH after an empty mask. The word on the accepted trial has law

    Pr(X=x | nonempty) = W(x)*(1-product_i(1-g[i,x_i])) / Zplus,

which is generally NOT W(x)/Z. Restarting only the bits for a fixed X instead
divides each word's weight by its own nonempty probability and gives a DIFFERENT
law. That superficially similar conditional-bit implementation is forbidden.
If min g>=epsilon, expected whole-pair attempts are at most
1/(1-(1-epsilon)^|M|). Without a lower bound this rejection implementation can
be arbitrarily bad. Direct positive DP below has no such trial-count factor.
Any finite attempt/time cap adds resource failure and must be accounted for;
it is not permission to time-censor successes or substitute a biased fallback.

## 2. Two-state positive arithmetic, no near-equal subtraction

At an active original-ID leaf use masses w*(1-g) for bit0 and w*g for bit1;
inactive fixed leaves have bit0 mass w and bit1 mass0. Augment the circuit by
a bit recording whether ANY active leaf was released. For a binary product of
disjoint scopes, with child masses (u0,u1),(v0,v1), use

    parent0=u0*v0,
    parent1=u1*(v0+v1)+u0*v1.

Sum nodes add like-indexed masses. Root bit1 is Zplus. The three bit1 cases
(1,0),(1,1),(0,1) are disjoint, so no multiplicity is introduced. A sequential
original-ID DAG carries the same seen-bit automaton. Backward/top-down sampling
on root bit1 returns the correct joint pair. All arithmetic is nonnegative;
Zminus is not subtracted from Z near cancellation. This is a CLASSICAL product
with a two-state OR automaton / finite semiring, not a new parsing theorem.

For a circuit/DAG of size C, the augmented numeric work/storage is O(C), with
a constant factor and the full original-ID gate/class reductions charged.
Rational bit work depends on length and input precision. Arbitrary gates within
a token class may require reduction over EVERY original ID; grouping does not
justify replacing token-dependent gates by class representatives.

## 3. Exact observed-action likelihood and scores

For a nonempty observed action a=(B,t_B), define unary rows

    w_a[i,v] = w[i,v]*g[i,v]*1[v=t_i] for i in B,
    w_a[j,v] = w[j,v]*(1-g[j,v])       for j in M\B,

and retain fixed inactive rows. Let Z_a be the ordinary grammar partition on
these rows. Summing the hidden proposals gives

    pi(a)=Z_a/Zplus.

The compatible action support is the same for ALL finite parameters with
w>0 and0<g<1. It is a finite globally differentiable kernel; V1's comparison
cells are not required. The nonempty bit is not an uncharged selection event.
A smooth parametrization can fail numerically by rounding a gate to0/1; that
must be detected or enclosed, not treated as proof of this hypothesis.

For independent log weights l[i,v]=log w[i,v] and gate log-odds h[i,v], the
score equals a difference of two conditional expectations under K:

    d_l log pi(a) = Pr(X_i=v | a) - Pr(X_i=v | nonempty),

    d_h log pi(a) = Pr(X_i=v | a)*(1[i in B]-g[i,v])
                   - Pr(X_i=v,B_i=1 | nonempty)
                   + g[i,v]*Pr(X_i=v | nonempty).

Proof: differentiate log Z_a-log Zplus. The log local gate factor has derivative
1[X_i=v]*(b_i-g[i,v]). The observed bit is fixed by a; the base joint expectation
comes from augmented inside/outside. All shared-parameter, confidence and gate
dependencies require the actual chain rule. Detaching the confidence while
updating its producing model is NOT this gradient. Using a bounded gate
epsilon+(1-2epsilon)*sigmoid(r) requires its own log-odds chain derivative.

Given an accepted full pair (X,B), the score of K(X,B)/Zplus is a valid strong
control. The collapsed score above is its conditional mean given a. For every
action-only multiplier, classical total covariance gives a nonnegative variance
reduction. The complete observed-path statement follows under the same Markov
sufficiency/fresh-randomness argument as V1, now without moving comparisons.
This is NOT equality of clipped PPO objectives computed on different latent
spaces, nor marginal likelihood of final text summed over all action paths.

## 4. Mandatory reductions and competing operations

If g[i,v] is independent of v, the mask is independent of the grammatical
word before nonempty conditioning. One may sample the nonempty Bernoulli mask
first and the original grammar word second. This is a STRONG simpler control,
closely related to known dUltra/Learning Unmasking Policies. It must not be
forced to pay a token-dependent auxiliary inference it does not need.

With no grammatical coupling, all sums factor analytically. With a small
language, enumerate exactly. With a compiled grammar, generic positive evidence
inference implements precisely this construction and receives equal caching,
precision and component elimination. Additional conditional samples with one
averaged neural adjoint, learned/state-optimal baselines and iid budget tradeoffs
are admissible. A covariance identity alone is not speed or semantic gain.

V1's connected-family argument does NOT automatically transfer to this different
mask law. It requires its own example/oracle. Deterministic threshold and PL
remain strong behavioral/training alternatives. Exact progress/likelihood and
variance safety do not imply fewer forwards or better answers than those methods.

## 5. Eight-criterion reassessment

1. Use: train or audit a joint grammar/commit policy with sampled-token-dependent
   release, exact observed-transition likelihood and an explicit consumer
   canvas. This is a proposed new dLLM policy, not an implemented native decoder.
2. Difference: positive grammar inference marginalizes ALL discarded token
   proposals and nonempty conditioning for a smooth token-aware mask. Independent
   Bernoulli heads/standard CRF inference are antecedents. Whether their direct
   combination is sufficiently original remains unresolved; code size is irrelevant.
3. Choice: same-policy collapsed gradients have no greater covariance than
   accepted-full-pair gradients. Direct OR inference avoids an inverse rare-exit
   trial factor. Useful complete-cost/semantic advantage against all competent
   controls above is not established, and token awareness itself may not help.
4. Proof: joint law, positive two-state compiler, fixed support, smooth observed
   likelihood, score chain rule and conditional variance are written above.
   These are classical operations; no lower bound against all samplers is claimed.
5. Experiment: first independent complete rational joint/action laws, direct
   expected-score derivatives, exact nonempty conditioning/restart-only-bits
   counterexample and Markov path collapse. Freeze any external neural/state
   cost/variance and training protocol BEFORE new heads/updates/timings.
6. Cost: full model forward/backward or frozen-head planner gradient as applicable,
   original-V gate reductions, compilation, augmented+filtered inside/outside,
   RNG, ALL restarts, memory, original-ID output and fresh numeric work. Joint
   root positivity does not erase cancellation/underflow or finite-bit trust issues.
7. Objections: known compiled CRF/evidence machinery may subsume the whole idea;
   position-only masks may be cheaper/better; full-pair scores with good baselines
   may already suffice; grammar size/gates may dominate the neural application.
   Do not convert a familiar compositional proof into a new theoretical discovery.
8. Article: priority audit, realistic numerical implementation, measurable useful
   full-cost signal, actual parameter updates and external independent confirmation
   remain necessary. No new forward, trained model, competitive result or goal
   achievement follows from this version. Only the minimal law oracle is next.
