# Exact finite cap: a practical corollary, not a new stopping principle

2026-10-11. Written BEFORE the added finite-cap check or real model heads.
Refinement of the existing eight criteria: this supplies a small deterministic
draw budget for the same unknown-probability original-payload operation. It
does not establish class signal, native speed or specific literature priority.
Ruin/parity/geometric-series calculations are classical.

Set barrier r=3, z=p(1-p), and deterministic cap n>=2. With L=floor(n/2),
the second-original-payload fallback of bounded-runtime-v2 has EXACT

    delta_n(p) = z^2 * sum_(j=0)^(L-2) z^j
               = z^2*(1-z^(L-1))/(1-z),
    E N_(2L)   = 3-z^(L-1),
    E N_(2L+1) = 3-2*z^L.

The empty sum for L=1 is0. Both full payload marginals remain original.

Proof of gain: a repaired mixed-class pair corresponds to a balanced positive
excursion below barrier3, beginning with two equal class bits. For each even
length2h>=4 exactly ONE positive excursion avoids3. Its probability is z^h.
The existing path-pairing proof therefore sums z^2,...,z^L. Odd termination
adds no balanced excursion and no gain.

Proof of cost: after the initial two bits,

    P(N>2h)   = z^(h-1)*(1-2z),
    P(N>2h+1) = z^h, for h>=1.

There is only one live alternating path per initial class. Sum survival
probabilities up to the cap; consecutive terms telescope to the displayed
expectations. For n>=3 their supremum over p in(0,1) is3 (approached at the
endpoints); no sample/continuation draw is omitted.

At p<=1/2, q=1-p and the normalized fraction is

    eta_n(p) = q^2*(1-z^(L-1))/(1-z).

Since3*q^2 >=1-z (difference=(2q-1)(q+1)) and z<=1/4,

    inf_p eta_n(p) = (1/3)*(1-4^(1-L)),

with equality at1/2; use symmetry for p>=1/2. In particular n=12 gives
`eta=341/1024`, which is1023/1024 of the SHARP expected-budget3 frontier1/3.
It loses at most1/3072 of the maximum class-preserving Fréchet improvement,
has expected total draws<=3, and deterministically consumes at most12.
This is a fraction of the normalized mathematical gain, NOT99.9% quality,
accuracy, latency or superiority over information-aware controls.

## A useful exact dominance inside this implementation family

Caps2L and2L+1 have the SAME joint output law, also for original payloads:
their binary joint laws agree and their within-class conditional payloads
are independent and original. Yet the odd cap consumes strictly more work:

    E N_(2L+1)-E N_(2L) = z^(L-1)*(1-2z)>0.

Thus an odd cap is strictly dominated by the preceding even cap for this
family's output law/call count. This is not optimality among all n-bounded
factories: the A32 bounded-budget construction may buy more gain with more
expected work. A full native adapter still charges disposal, copies, parsing,
every forward and continuation; draw-count dominance is not a hardware claim.

The sampler needs only first, original-second and current payloads. A native
implementation must CLOSE discarded generators as soon as the loop asks for
another draw, preserving RNG tapes; retaining all twelve GPU forests/head
tensors needlessly enlarges memory. Bound live payloads explicitly before a
real run. Do not call such basic resource management a new contribution.

The real application remains open. If draws already generate full outputs,
iid3 wins as full-cost-v3 proves. A count cap is not a physical-time deadline
fallback. Publication novelty and a useful native accepted partition must
still be established separately.
