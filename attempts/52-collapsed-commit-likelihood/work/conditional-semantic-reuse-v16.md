# V16 — Conditional auxiliary reuse WITH the semantic baseline, BEFORE code

2026-10-16, AFTER V15's unfavorable16-path diagnostic. This is a separate
refinement, not a relabeling of those results. Rao--Blackwell, conditional
Monte Carlo, stratification, partial enumeration and baseline identities are
CLASSICAL. A17/GRAS/PAPL are antecedents, not ignored competitors. A17's small
top16/MDLM head-only negative timings do not become V16 evidence. No adequate
originality, practical benefit, training or publication is asserted.

## Eight criteria

1. Operation: estimate the SAME frozen-proposal reveal-policy reward gradient
   from a complete visible dLLM path, retaining the FULL semantic proposal
   baseline. Neither generation nor the grammar uses gold labels. Additional
   draws are posterior AUXILIARIES, not new decoder trajectories or forwards.
2. Candidate: V7's forced-anchor law gives a simple unary-weighted posterior
   over discarded proposal IDs, with terminal1/H_T. This tractable specific
   policy/query is the only possible distinction; the resampling principle
   itself is known. Sufficient scientific difference remains unconfirmed.
3. Potential benefit: average remaining hidden noise while reusing the current
   head/query and preserving the strong semantic control that a regular proxy
   alone need not project completely. May be useless if visible/future noise
   dominates or strong class/enumeration controls already remove hidden noise.
4. Prove posterior/disintegration, frozen-policy score mean and conditional
   covariance below. Ideal rational law only; no exact finite-RNG/CUDA claim.
5. FIRST ONLY small independent rational word/anchor/action/moment oracles,
   original aliases/fixed EOS/zero actions and classical correlated-strata/
   enumeration controls. No new neural head, real auxiliary campaign, gradient
   variance or timing follows from this written note.
6. Full cost includes conditioned query/backwards, full-V filtered-ID masses/
   CDFs, extra draws and verifiers, score/actor projection, storage/copy/cache,
   head/normalizers and baseline fitting. No extra forward is not free work.
   Online separate auxiliary RNG can avoid retaining past dense heads; count
   the actual memory/preparation costs. Never perturb decoder/future RNG.
7. Strong controls: cheap anchor/class/length/combined scores, raw semantic
   proposal controls for ALL estimators, exact regular proxy, state/horizon/
   RLOO and independent fitted mixtures. Also exact semantic projection where
   feasible, weighted partial enumeration and correlated/stratified replicas.
   Do not assume iid replicas are necessary or win over enumerable support.
8. Gaps: useful full-cost magnitude versus ALL controls, independently fitted
   baselines, actual updates/application, own sufficient originality and
   independent confirmation. No large campaign is justified by the identity.

## Original-ID posterior, for the SAME observed release B

At visible s let X be the first-EOS proposal prefix, drawn from P_s independent
of policy phi. Fixed IDs stay in X. Active anchor weights u_i>0 and strictly
interior gates g_i(v) may depend on frozen native confidences/state. With

    H_T=sum_{active i<T} u_i,
    S_B=sum_{i in B} u_i/g_i(x_i),
    q_B(x)=product_{active i<T} c_i(x_i)
             * product_{active i<T} g_i(x_i)^{1_{i in B}}
                                      (1-g_i(x_i))^{1_{i not in B}},

and indicator of original grammar/fixed/retained IDs, V7 gives

    Pr(X=x,B|s) = S_B*q_B(x)/(Z_s*H_T),
    Q_B=sum_x q_B(x)/H_T,
    Pr(X=x|s,B) = q_B(x)/(H_T*Q_B).

S_B uses ONLY retained IDs and cancels. Every fixed/retained ID precedes EOS;
the unused suffix integrates1. A zero observed-action mass is a refusal, not
a posterior to sample. No token ID/tokenization/empty alias is dropped.

The auxiliary anchor given X,B has probabilities

    rho_i = (u_i/g_i(x_i))/S_B, i in B,

which are INDEPENDENT of discarded X and T once B is known. Thus the cheap
anchor-integrated score F_A(X,B)=E[F|s,X,B] is available without another
grammar query or sampled anchor. It retains X, so E[b(X)F_A|s]=0 for the FULL
semantic verifier b. A weighted posterior sampler with unary factors and
terminal1/H_T supplies new X|B; this is standard weighted inference.

## Conditional reuse preserves the semantic control

For visible/fresh-future reward R, fixed state baseline v(s) and coefficient
lambda(s), put

    H_t(X)=(R-v(s_t)-lambda(s_t)*b_s(X))*F_A(X,B_t).

Given the COMPLETE visible path O (with absorbing padding to finite horizon),
latent posteriors factor over steps by V8's sufficient-state argument. Thus

    Gbar(O)=sum_t [(R-v_t)*S_t-lambda_t*C_semantic(s_t,B_t)],
    E[sum_t H_t(X_t)|O]=Gbar(O).

C_semantic is the FULL semantic projection, not the regular-subset C from
V11/V13. It need not be evaluated analytically for this identity to hold.
For M independent conditional replicas of the whole auxiliary sequence,

    G_M=(1/M) sum_{m=1}^M sum_t H_t(X_{t,m}),
    Cov(G_M)=Cov(Gbar)+(1/M)*E[Cov(sum_t H_t|O)].

The decoder's original X_t is ALREADY one draw from the posterior when O is
conditioned on; it may serve as replica1, with M-1 fresh conditional draws on
a separate auxiliary stream. The mean stays the SAME policy gradient. Future
model inputs/decoder draws cannot depend on these auxiliaries. All original
IDs/actions and neural calls remain identical, but wall/CPU cost can increase.
Ordinary correlated stratification of a common arithmetic unranking uniform
can further reduce variance; it is a classical control, not new theory.

For any common scalar projection with visible variance V and hidden variance
W, the iid variance ratio is (V+W/M)/(V+W). To reduce it by20%, one needs
W/(V+W)>=.2/(1-1/M). Full cost can erase even that gain. No positive lower
bound on W or useful speed follows for actual dLLM states.

## Exact-query/partial-enumeration controls

If exact semantic C is tractable, direct Gbar removes ALL auxiliary noise;
retain it, including small rational examples where enumeration is faster.
The regular event can also be an EXACT CONDITIONAL control:

    E[F_A-S|O]=0,
    E[b_regular(X)*F_A-C_regular|O]=0.

Every estimator using the same query may fit these controls independently,
with common costs. Replacing b_semantic by b_regular silently would change
the matched comparison. In particular, exact RS-C_regular plus a sampled
semantic remainder is a legitimate strong alternative; it can be poor at
finite M and must be compared, not presumed inferior. Weighted high-mass
partial enumeration and vectorized conditional samplers are mandatory too.

This proof does not establish advantage over those implementations, priority,
training utility or the scientific goal. The next authorized research step
is a MINIMAL rational oracle, not real-data draws/forwards/updates/timings.
