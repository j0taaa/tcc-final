# V4 — All original-token residual masses in one inside/outside analysis

2026-10-13. Written before changing the reference. V3's corrected oracle
passes482,657 tail checks with6,480 actual merges,700 independent word
densities,4,560 prefix/threshold enclosures,15 full proposal/coupling laws
and240 valid residual samples. Its setup failure stays separately preserved.
These checks establish finite correctness, not priority or useful latency.

## Missing efficiency obligation

V1 pays q fresh profile constructions for every sampled position. That can
make its polynomial bound unsuitable for a dLLM vocabulary. Ordinary scalar
outside differentiation does NOT give positive-part residual marginals:
the payoff is nonlinear in the two original word weights and compression
does not preserve original event identities. Use a distribution-valued
outside message with a separately proved error bound instead.

This is an algorithmic candidate. Inside/outside, monotone measures and
automatic differentiation are antecedents. The possible own statement is
the simultaneous, zero-preserving RELATIVE enclosure of every original-ID
residual mass, with a full cost and an exact-correction consumer. No novelty
or speed gate is passed merely because an outside pass is implemented.

## Exact event identity

For a forest node v, a context is a root derivation with the occurrence of
v replaced by a hole. Because every nonempty child scope is consumed once
and ORs are word-disjoint, marking a particular original token-closure edge
counts each compatible root event exactly once across all such marked edges.
Contexts from distinct OR alternatives remain disjoint MARKED events. The
object is not obtained by forgetting all marks and deduplicating assignments.

Let I_v be the exact inside measure of ratios A/B and integer B-masses;
let O_v be its context measure on B-positive events. At the root O_root is
the atom (1,1). For a binary alternative (v -> l,r), add O_v tensor I_r to
O_l and O_v tensor I_l to O_r, where tensor multiplies ratios and masses.
Sum all incoming alternatives before compressing a context list.

In parallel compute exact scalar outside values for A and for A restricted
to B-positive leaves. These are ordinary positive inside/outside passes.
They are needed for singular-support contributions and use no approximate
subtraction of nearly equal numerical quantities.

For a choice term (i,j) in node v, with leaf weights a,b and ratio r=a/b,
its common-support contribution to the residual marginal is

    b/Z_A * integral (r*x - Z_A/Z_B)_+ dO_v(x),     when b>0.

The singular contribution is

    a/Z_A * [outside_A(v) - 1[b>0]*outside_A_common(v)].

If evidence forbids the original ID, set BOTH leaf weights to zero. Sum
these expressions over every marked choice term with the original (i,j).
This returns the UNNORMALIZED residual marginal; original Z_A,Z_B stay fixed.
No fresh grammar construction per token is needed. A token emitting many
bytes receives exactly one closure mark, and aliases remain distinct IDs.

## Approximation proof

Inside exponents e_I(v) are as in V1. At each outside product the exponent
is e_O(parent)+e_I(sibling)+1 (the one is product compression). At an outside
sum/compression it is max of the incoming exponents plus one. The root
outside exponent is zero. The recurrence is evaluated in reverse topological
order; it is not the inside height or the number of distinct DAG nodes.

S1 and the Stieltjes product lemma from V1 imply by induction

    T_true(O_v)/(1+eta)^e_O(v) <= T_hat(O_v) <= T_true(O_v).

For fixed nonnegative r, x -> (r*x-Z_A/Z_B)_+ is nonnegative, nondecreasing
and zero at zero. S2 therefore gives the same enclosure for the common
choice contribution. The singular contribution is exact and nonnegative.
Take d_all=max(d_inside,max_v e_O(v),1). With eta=xi/(2*d_all), multiplying
every lower marginal by c=(1+eta)^d_all supplies an upper marginal, and

    lower_(i,j) <= residual_(i,j) <= upper_(i,j) <= (1+xi)*lower_(i,j).

Zero is preserved FOR EVERY original token, including ones with tiny
residual mass even though the full norm/TV is large. This is why the argument
does not just differentiate an approximate scalar certificate. Summation
over marked edges needs no additional approximation and does not incur a
factor equal to vocabulary size.

For a CNF byte parse tree of length B_bytes, inside siblings along one
root-to-mark path are disjoint. Their expanded operation counts together
are O(B_bytes). The context path has O(B_bytes) nodes, each adding at most
two new compressions. Consequently d_all=O(B_bytes), independently of DAG
sharing; one may use the conservatively computed exponents instead of this
asymptotic shortcut. General source admission remains a separate obligation.

## Complete cost and consumer

Let W_star bound bit lengths of ALL exact integer inside/context B totals.
Expanded derivations are polynomially bounded; even counting distinct marked
contexts gives at most H^O(B_bytes) events times products of original weights,
so W_star is polynomial in original bits, log H and B_bytes. All represented
mass lists remain positive integer measures. Representatives remain rational
products on disjoint physical scopes. Put M=O(1+W_star*d_all/xi).

Both profile passes cost O(H*M^2*log(H*M+2)) arithmetic operations and
O(H*M+M^2) atoms. Evaluating every closure marginal costs O(C*M), where C is
the number of marked choice terms and C<=H. Writing all n*q entries costs
O(n*q), including zeros. Rational arithmetic/GCD and scalar bit costs remain
polynomial and are charged explicitly. Wide fan-in sums/temporary lists and
refusals count. No input reading, full output or model forward is sublinear.

For one sequential proposal, recompute this analysis after each of at most
n choices and use the row of current-position lower marginals. The pointwise
proposal envelope and exact rejection proof from V1 are unchanged. This
removes the q-factor in the number of FULL profile analyses per attempt,
while retaining output/closure costs and the <2 conditional expected attempts.
The comparison is against separate queries of the same residual operation,
not a theorem that no other shared inference algorithm can do this.

## Adversarial validation, before measurements

Keep V3 as an independently frozen version. Reconstruct every new marginal
from all words using JSON/stack recognizers. Compare with V3's individual
clamped queries where appropriate, but do NOT require the same lower endpoints:
different controlled compressions may give different valid intervals. Enumerate
all proposal densities and accepted laws under the new algorithm; checking
only the total residual or that samples look valid is insufficient. Preserve
all aliases, prefixes, fixed positions, singular/equal laws and tiny weights.

No new model campaign or publication claim follows from a passing oracle.
The README's significance/prior/cost objections remain mandatory. A50 is an
exact local correction primitive, not a measured faster dJev or native EPIC.
