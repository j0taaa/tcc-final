# V9 — Reference support and competent state sampling, BEFORE prototype

2026-10-16. Addendum to visible-elbo-v9.md, before V9 code/heads/updates.
Ordered partitions, occupancy measures, binomial transitions and Jensen/KL
are CLASSICAL. This is a tractability/control clarification, not novelty.

## Full target-path support in this particular monotone decoder

If the final original-ID prefix is y, each visible action along that path
must commit a nonempty subset of its still-unfilled positions, with exactly
y's original IDs. An erroneous ID cannot be undone, and no committed ID can
be beyond y's EOS. Conversely, any ordered partition of y's positions is a
legal target path: each partial state admits y; positive gates/anchors and
positive current proposal probability of y make each next action positive.
Thus, under this strict domain and initial-empty canvas, the reference
covers ALL visible paths ending in y. With compatible initial fixed IDs the
same argument applies to the remaining positions. It is not a statement for
hard zero gates/support or remasking policies.

Consequently the second inequality in V9's displayed bound is equality here,
and the ordinary variational identity is

    log p_phi(y) - L_phi(y) = KL(R(h|y) || P_phi(h|terminal=y)).

The path posterior is not presumed tractable: its different partial canvases
need different neural heads. Computing the kernel at ONE given state does
not remove that exponential family of states or yield exact target MLE.

## Do not waste samples on absorbing time slots

The written fixed-L_y random-time estimator is correct, but a competent
control first samples the whole cheap reference path, obtains its actual
length N, then chooses J uniformly among its N nonabsorbing steps and uses
N times that step's log-ratio/gradient. This is also unbiased. Rejecting
absorbing times while retaining the OLD factor L_y would be wrong.
There is no free speed/variance claim from avoiding these zeros: the older
scheme sometimes needs no neural call, while the active scheme always does.

The reference also admits direct occupancy sampling, without constructing a
complete path. Given m unfilled target positions, its release count has law

    p_m(k) = C(m-1,k-1) gamma_m^(k-1) (1-gamma_m)^(m-k), 1<=k<=m,

with p_1(1)=1. This is precisely1+Binomial(m-1,gamma_m). Let v_L(m) be
the probability that a reference path starting with L unfilled positions
visits remaining count m. Every count is visited at most once. Descending
finite flow computes these exact rational numbers:

    v_L(L)=1;
    add v_L(m)*p_m(k) to v_L(m-k) for m descending and all k.

Let e_L=sum_{m=1}^L v_L(m)=E_R N. Conditional on visiting m, the fixed target
subset is uniform among subsets of size L-m, by permutation symmetry of R.
Sample m with probability v_L(m)/e_L, such a uniform fixed subset F, then
a reference action from R(.|F,y). For any state/action function f,

    e_L E[f(F,B)] = E_{h~R}[sum_t f(F_t,B_t)].

This yields an exact one-current-head supervised loss/gradient sample for
V9, plus any separately required root-feature head. It does not query the
denoiser at previous reference states. Its target length is SUPERVISED
information, not an inference-time oracle. All preparation and sampling costs
still count. Supervised CE/PAPL/grammar-marginal controls can and should use
the SAME competent state sampler; this mechanism is not a candidate-only
advantage. No general variance ordering between these different sampling
laws or training objectives is asserted.

The minimal independent oracle must compare all three representations of
the bound gradient (full reference paths, actual-length random time, direct
occupancy), exact target path support and a wrong absorbing-rejection factor.
It must also retain strict variational gaps rather than claiming exact MLE.
No pretrained forward, Tiny-A2D rescue or model update is authorized here.
