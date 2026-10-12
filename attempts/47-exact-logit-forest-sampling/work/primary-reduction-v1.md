# V1 decision: the generic interval/precision argument is established

2026-10-12. No prototype, dependency installation, model run or performance
measurement. The maintained rational posterior and paper remain unchanged.

Actually read Duchon, *Random generation of combinatorial structures:
Boltzmann samplers and beyond*, WSC2011, section6 in the original
<https://www.informs-sim.org/wsc11papers/011.pdf>. It discusses repeated
approximation errors, safety intervals for union/product decisions, logarithmic
precision for expected object size, and exact samplers under refining certified
upper/lower oracles with logarithmic expected refinement counts. It explicitly
leaves the stronger numerical oracle as a premise/work in progress there.

Actually read Brassard/Devroye/Gravel, *Remote Sampling with Applications to
General Entanglement Simulation*, arXiv:1807.06649, sections2 and4, Algorithms2/4,
Theorems1/2 and the final random-bit bound, original
<https://arxiv.org/pdf/1807.06649>. Certified approximations and progressively
revealed independent fair bits yield exact samples; refinement tails and
expected precision are explicitly analyzed. Their general construction
initially prepares a vector over every outcome: it is not itself an efficient
exponentially large forest implementation. Applying its decision comparison
to each binary forest choice, however, is a standard specialization. Section3's
quantum application and its dependencies were not audited here.

Flajolet/Fusy/Pivoteau2007, *Boltzmann Sampling of Unlabelled Structures*,
DOI10.1137/1.9781611972979.5, remains a primary lead for exact interval arithmetic.
The original PDF could not be retrieved from the two university mirrors in
this session; their abstract/search excerpts are not a full reading. Denise/
Zimmermann1999, DOI10.1016/S0304-3975(98)00323-5, is another primary lead on
floating-point recursive generation with exactness/expected costs. Its abstract
and author catalog, not the complete proof, were read. Do not claim to have
eliminated every possible specialized numerical contribution from these leads.

The homogeneous-positive-polynomial enclosure in proof-obligations-v1.md is
elementary: multiplicative leaf bounds multiply along a degree-d monomial and
sum without cancellation. The subsequent small-threshold-interval/random-bit
tail is the established adaptive-comparison argument. Thus generic exact-real
forest sampling plus logarithmic expected precision is not a new principle.

What remains unwritten is a complete bit-cost oracle for arbitrarily large
rational logits, mantissas/exponents and intermediate rounding. Completing
that obligation could produce a correct specialized algorithm; it does not
automatically create a scientific advantage against existing certified
Boltzmann/recursive samplers. Ordinary log-domain inference already handles
range issues competently; fixed-range underflow is an inadequate opponent.

**Decision:** do not promote or implement the generic A47 outline as the new
protagonist. Close that novelty claim before adding numerical infrastructure.
A distinct oracle/cost improvement would need a new version and an actual
practical justification. No ideal-softmax solver or publication win is claimed.
