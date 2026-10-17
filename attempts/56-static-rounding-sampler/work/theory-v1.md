# Guarded positive-circuit enclosures before implementation

This is STANDARD forward-error analysis, written before the new reference.
The systems candidate is the possible GPU artifact/cost, not these identities.
The eight README criteria apply. No real neural inputs or timings yet.

## Target, arithmetic and guards

Inputs are nonnegative finite original binary64 numbers in[0,1], including
zeros/aliases/fixed one-hot rows. A positive arithmetic circuit uses conversion,
addition and multiplication, plus division by a positive OBSERVED floating
scale. Each such scale is treated as an exact constant in the mathematical
circuit. The target beta is the true original-weight inside mass divided by
the SAME sequence of observed scales. They therefore cancel in normalized
conditional choices; no assumption that an observed max is the true max.

Use an explicitly specified IEEE-style round-to-nearest binary format.
The permitted rounded operations must individually satisfy

    (1-e)*v <= fl(v) <= (1+e)*v, 0<e<1,                 (A)

for their nonnegative exact operation result v. For binary32, conservatively
take e=2^-23 and require every nonzero rounded result to be finite NORMAL.
If an exact-positive operation rounds to zero, REFUSE the fast certificate.
A rounded zero is certified exact only from previously certified exact zeros:
sum iff both inputs zero, product iff an input zero, conversion iff input zero.
Subnormal nonzero outputs and overflow/NaN also refuse this fast certificate.
There is no pruning or relabeling of these original target contributions.

Normal-output guarding is deliberately conservative. The usual half-ULP
absolute rounding bound, including the boundary below the smallest normal,
gives relative error <=u/(1-u)<2u=e with u=2^-24. No denormal-flush assumption
is allowed. Actual GPU operations/guards must be audited against their PTX;
the mathematical statement does not prove an unexamined compiler's behavior.

## Static exponent theorem

Associate each computed value xhat with its exact circuit value X and integer K:

    (1-e)^K*X <= xhat <= (1+e)^K*X.                    (B)

An exact literal starts with K=0. Conversion adds1. Guarded positive sum uses
K=max(Kleft,Kright)+1. Guarded positive PRODUCT uses

    K=Kleft+Kright+1.                                 (C)

Division by an observed positive exact scale adds1. This rule does not apply
to division by an uncertain target expression; no such ratio is inserted into
the positive inside circuit. Guards ensure all uses of(A), and exact-zero
propagation handles zero operands without invalid relative division.

Proof is induction. For addition, replace both lower exponents by their
maximum, and similarly both upper exponents. The positive sum preserves the
inequalities; apply(A). For product multiply both input enclosures and then
apply(A), giving(C). Conversion/division follow(A) directly. This remains true
when the same subexpression is shared: no independence of arithmetic errors
is used. If a GPU reduction tree differs from the assumed tree, its K must
be conservatively bounded/verified; declaring a balanced tree is not a proof.

Exact enclosures recovered from one stored rounded value are

    X in[xhat/(1+e)^K, xhat/(1-e)^K].                  (D)

Finite GPU multipliers must enclose these factors outward, and the final
multiplications also round outward. Precompute factors by exact integer
arithmetic and directed representable rounding, or provide another proof.
`exp`, `pow` or a math-library ULP guess is not a certificate. Constants may
overflow or give loose intervals; that is fallback/refusal, not clipping.

## Normalized choices and original words

Apply(D) to original class sums and scaled suffix beta values. Form edge
weights with outward interval products and use the CLASSICAL CDF prefix
enclosure[Alo/(Alo+Bhi),Ahi/(Ahi+Blo)]. A chosen original edge/block/ID is
certified only if its entire independent uniform-prefix interval lies inside
the inverse-CDF interval for all enclosed true masses. Exact suffix zeros
and nonaccepting terminals stay zeros. Original IDs, all blocks and all graph
arcs remain; aliases never disappear. A correct deterministic graph compiler
is a separate obligation, already independently audited in the earlier code.

On ANY failed numerical guard, ambiguous decision or unproved positive root
mass, use the competent directed interval pass and/or arbitrary-precision
exact sampler. Keep the SAME revealed uniforms for each position/phase and
reveal extra independent bits only if needed. Restarts with fresh uniforms
after outcome-dependent ambiguity can bias the output. With unbounded resources
the disintegration law is exact for the original declared weights. Finite
resource limits produce explicit FAIL and may censor successful-output law;
no unconditional exactness under such censorship is asserted.

## Cost and comparison obligation

Budgets and constants depend on the actual reduction graph and all conversions,
products, sums and scales. A naive operation count is safe but may be useless.
One ordinary arithmetic stream replaces two directed streams only BEFORE
guard, factor, interval-read, synchronization and fallback costs are counted.
The deterministic compiler and target are shared with the dual-directed
control. Both must receive equal layout/reduction fusion and the same prefixes.
If enclosures are materialized, account for their full buffers as well.

The first gate is independent exact proof/refusal testing. Any later cost
campaign must be frozen separately before reading real weights or timing.
No theorem above supplies a priori20% physical speedup, sufficient novelty,
useful whole-model benefit or the user's requested achieved goal.
