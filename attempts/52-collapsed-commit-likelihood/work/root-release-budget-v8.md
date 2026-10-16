# V8 foundation — Frozen root feature for a small release budget, before code

This is a written refinement of V7, not a revised V5 outcome. Its eight
criteria remain mandatory and are reassessed in the separate resource contract.
No new head, update, useful effect or novelty is asserted. Sigmoid calibration,
expectation semirings and monotone root finding are classical.

For a CURRENT fixed proposal P_s, let m(T)=|I(T)| and use V7 anchor pi_i(T).
With g_iv(a)=sigmoid(a+log(c_iv)-log(.01)), the expected release count is

    C(a)=1+E_(X,T) sum_(i in I(T))(1-pi_i(T))*g_i(X_i;a).

Proof: the forced anchor replaces its ordinary Bernoulli bit by1; average
1+sum eligible gates-g_A over A and the proposal. Differentiation gives

    C'(a)=E sum_(i in I(T))(1-pi_i(T))*g_i*(1-g_i).

It is positive if P(m(T)>=2)>0 with positive u/g; otherwise C=1. As a goes
to minus/plus infinity, the respective limits of C are1 and M=E[m(T)]. Thus any k strictly between
1 and M=E[m(T)] has a unique finite solution. This is an elementary monotone
calibration, not a new decoder theorem or a total-runtime guarantee.

For a resource consumer, compute a feature a0 ONCE from the fixed all-mask
INITIAL head, default u_i=1, beta=1 and no learned offsets, with

    k=min(2,(1+M)/2).

If M=1, gates are irrelevant to release count; use a0=0 and explicitly mark
that degenerate case. Otherwise k is interior. Keep this SAME a0 for every
later step of that trajectory; do not recalibrate on outcomes or later heads.
Later expected counts need not equal k or2. The head/gates use ORIGINAL full
probabilities. A root-defined feature is a fixed input under the current
frozen-backbone planner, not a learnable value silently differentiated away.

A possible future trainable family is
h_iv=a0(prompt)+alpha_i+beta*log(c_iv)-log(.01), with independent anchor logits r.
The root feature is computed using the DEFAULT policy and FROZEN base model,
then held fixed even if alpha/beta/r change. No gradient of that fixed feature
is then required for planner updates. Updating the base model, redefining the
feature from current learned parameters, or recalibrating it at each step
would require its TRUE implicit/input derivative and a NEW contract; those
operations are not implemented or authorized by this resource design.

For default uniform prefix anchors, pi_i(T)=1/m(T) on eligible rows. Therefore
C(a)-1=E[(1-1/m(T))*sum_(i in I(T))g_i]. A conventional expectation-semiring
pass accumulates the sum of gates on occupied active token edges, and multiplies
the newly terminating flow by1-1/m(t). Accepting tails are identity edges and
add no gate. This avoids enumerating prefixes; it still pays all original-V
gate/class reductions at each scalar trial. Fixed-ID rows have gate contribution0.

For floating implementation, bracket a in[-64,64] and take48 deterministic
bisections. Record bracket/count residual and final a; require absolute count
residual<=1e-8 and strictly finite0<g<1 on every ORIGINAL active ID used. If
the finite range cannot bracket an interior target or numeric support is lost,
REFUSE rather than floor probabilities or tune the range after outputs.
No speed or exact native finite-RNG law follows from this finite calculation.

Only a minimal rational expectation/monotonicity oracle and the separately
frozen bounded resource consumer are justified. Training, competitive timing,
quality superiority and independent confirmation remain untriggered.
