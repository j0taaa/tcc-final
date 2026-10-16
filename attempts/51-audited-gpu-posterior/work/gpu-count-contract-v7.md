# V7 — concrete count/proposal packet before GPU implementation

2026-10-16. V6's classical telescoping proof and all README criteria apply.
This is engineering feasibility, not a new theorem, performance win or publication.

Use V4's identical block-refined graph and V3 frontend. Copy its beta uppers into
positive potentials (replace zero by binary32 minimum subnormal), accepting
leaves1. Save EXACT observed binary32 scales. This clipping is not support pruning
and can force refusal if the count budget is poor. The decoder uses actual model
confidence; no exact conditional-marginal claim.

Construct token, block and edge categories with explicit upward binary64 division
and upward integer conversion of V6's ratios times2^40. Products of two original
binary32 factors in the edge ratio are exact in binary64. Block/token denominators
zero with ALL numerators zero can use unit counts: such a category cannot lie on
a positive target trace. Denominator0 with positive numerator is ERROR/refusal.
No out-of-range float is converted blindly to int64. Invalid elements use a dummy
one ONLY to finish validation, and an explicit error flag forbids sampling.

Segmented integer prefix sums are local to ONE category and use int64; length<=1024,
every element<=2^41, so even a rejected category's sum is <=2^51 (no overflow).
Then check EVERY total A<=2^41 and all counts positive before drawing. Record
per-layer maxima for all three phases, and form exact rational M from V6, using
maxA/2^40 times g=2^23/(2^23-1). This slightly loose g is itself exact rational.
The bound uses ALL category maxima, including singletons and inactive blocks.
L/M is an admission certificate only; the small arbitrary-potential rational
reference does not establish this certificate will be good on real heads.

For each phase provide two uniform32 words and combine to a uniform64 integer.
Use actual mul.hi.u64 and binary search of integer CDFs, never Torch multinomial
or a float uniform. Return ORIGINAL word IDs, selected original binary64 weights,
and each selected category's (A, startCDF, endCDF) as a small host packet. Density
is the exact ceiling-preimage formula with H=2^64. The scalar acceptance uses
that density, ORIGINAL weights and M with exact integers/Fraction. Reject ratio>1
as ERROR, never clamp. Zero-weight proposals are ordinary internal rejections.

All original word weights and ticket probabilities are dyadic. Their numerators
and powers-of-two denominators can be multiplied as integers and reduced ONCE in
the scalar acceptance; arbitrary precision and RNG cost are still fully charged.
One uniform source and one independent acceptance stream per trial are required.
Repeated frozen-head retries need no model forward. A fixed per-word trial cap
returns explicit FAIL; first accepted in fixed order has the original query law
conditionally on query success, with the trajectory/time-censoring caveats in V1.

Before any real-head/performance study, verify ALL count premises against Fraction
on independent tiny graphs, EVERY valid-word W/Q against M, original aliases/
JSON/EOT/PAD/fixed IDs, GPU versus CPU finite-ticket proposal walks, recorded packet
endpoints, exact scalar acceptance and budget refusals. Strong retained-uniform
interval control, exact rational CPU, approximate sparse/layered/native GPU and
other applicable exact/envelope controls must remain in a later full-cost protocol.
No independent neural campaign is triggered by correct primitives or by the V5
control's240 successes. Outstanding systems novelty/consumer significance remains
open; a substantial own advantage has not yet been demonstrated.
