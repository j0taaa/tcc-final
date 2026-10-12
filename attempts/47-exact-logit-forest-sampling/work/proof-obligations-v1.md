# V1 candidate bound and exact-real caveats

2026-10-12. Written BEFORE implementation/model observations. This is a proof
outline and explicit obligations, not a complete bit-complexity theorem.

Let n finite original slots and rational logits ell_i(v) be declared, with
structural zeros explicit (e.g. a fixed mask ID excluded). Set w_i(v)=exp(ell).
Finite logits give strictly positive weights. Per-position softmax denominators
are constant across all full n-slot events and cancel on conditioning. An
unambiguous positive parse forest with unique original-event derivations gives
Z=sum_valid_y exp(sum_i ell_i(y_i)); tokens with equal bytes stay separate.
The maintained compiler's admission/normalization must not silently be assumed
verified; initially consider an explicitly supplied correct forest.

Replace multiway sum decisions by balanced binary sums. A sampler derivation
uses at most R binary choices (R=O(n log H) for a forest with H alternatives
and O(n) selected parse/token edges, under an explicitly bounded reconstruction).
Leaves must have certified MULTIPLICATIVE enclosures, not only absolute error.
For every positive homogeneous component of degree <=d (event/slot counts),
enclosing each weight by exp(+-eta) encloses its value by exp(+-d eta): every
monomial has that degree and all additions are positive. Normalized branch
probability endpoints thus have width <=O(d eta), independently of absolute Z.
This elementary positive-polynomial condition bound may already be known.

With one independent lazy uniform binary stream per binary decision, at b
revealed bits its interval width is2^-b. If a branch threshold enclosure has
widthO(d2^-b), the chance of an unresolved comparison isO((d+1)2^-b), regardless
of the branch's probability. A union bound over at most R selected choices
suggests P(any comparison needing more precision b)<=O(R(d+1)2^-b), hence
expected maximum precision O(log(R(d+1))). Adaptive traversal needs a careful
conditioning argument: future uniforms must remain independent of prior choices
and an enclosure for a reached node must be valid for EVERY adaptive history.

If a b-precision full-circuit enclosure costs C(b), charge its recomputation.
For polynomial C, the suggested exponentially decaying refinement tail gives
finite expected O(C(log(Rd))) up to degree-dependent constants, plus output/RNG.
This conclusion REQUIRES proving an actual leaf/circuit enclosure with that
cost, including exponent representation and logit input bit length. Ordinary
fixed-range floats/absolute rational intervals can fail the premise. Exp of
a rational input of bit length L can have a magnitude whose exponent needs
O(L) bits while its explicit numerator needs exponentially more; do not assume
that a generic arbitrary-precision rational library avoids this. Range reduction,
directed rounding, tiny summands and relative bounds must be analyzed.

Exactness is in the ideal IID random-bit model and the uncapped completed run.
A precision/time cutoff can be OUTPUT-dependent. Conditioning on completion
may bias outputs; returning FAIL and claiming exact conditioned samples would
be wrong without a separate argument. A deterministic rounding/fallback is
also not exact. No performance assertion about native finite CUDA RNGs.

Closest methods to inspect: Flajolet/Fusy/Pivoteau2007 exact interval arithmetic
for Boltzmann samplers; Duchon2011 safety intervals/precision discussion;
computable-discrete random-bit/remote-sampling algorithms; current interval
oracles for combinatorial samplers. A generic theorem that already proves this
cost bound closes this as a novelty candidate before implementation.
