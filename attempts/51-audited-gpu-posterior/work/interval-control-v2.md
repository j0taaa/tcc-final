# V2 — competent interval control before GPU work

2026-10-16. Same consumer/target/eight criteria as V1; no change to frozen proof.
This is an established interval recursive sampler, NOT a new invention. It is
mandatory because it can avoid the scalar exact correction A51 pays every word.

For a categorical choice whose true nonnegative branch weights v_i have certified
enclosures [l_i,h_i], true prefix C_j=sum_(i<j)v_i/sum_i v_i lies in

 [ A_l/(A_l+B_h), A_h/(A_h+B_l) ],

where A sums the prefix, B its complement. Endpoint0 and final endpoint1 are
known exactly; zero/undefined denominators cause refinement, not a guessed draw.
Let U be an infinite fair-bit uniform with observed interval [u_l,u_h]. Select j
only if upper(C_j)<=u_l AND u_h<=lower(C_(j+1)); endpoint ties can be left
ambiguous to refine. These inequalities imply the true inverse-CDF choice for
ALL values of the unknown masses and remaining bits. Exact hits on boundaries
have probability0. Repeatedly refine arithmetic and/or random bits until a
choice is proved. Finite rational fallback recomputes exact messages and uses
the SAME revealed uniform prefix. Redrawing after an ambiguous decision can
bias the whole output: the ambiguity event depends on the target choice.

Apply per edge, token-class, block and original ID with independent uniforms;
with exact conditional branch weights, their disintegration yields P. Interval
backward sums/products, fixed IDs and EOT/PAD follow the same true graph as V1.
A GPU kernel can resolve most intervals without any host scalar arithmetic.
Ambiguity triggers charged CPU/high-precision fallback, preserving random bits.
With finite resources, return explicit FAIL; wall-time censorship has V1's
limitations. Resource refusal does not prove zero grammar mass.

Both controls may share compiled graph, dense head and class partition and
use the SAME directed basic arithmetic reductions. Neither gets approximate
math-library ULP tables as an unproved certificate. A51 uses max-ratio/lower
passes and exact word correction; this control uses lower/upper inside passes
and certified CDF comparisons. A51's potential advantage is fewer ambiguous
branch refinements/less synchronization; a fused GPU interval implementation
could remove it entirely. Only measured full cost can decide, and normal FP64
remains a legitimate accuracy/cost alternative for the real user.

Decision: primitive tests and a small shared numerical frontend may be developed
to determine feasibility. Do not undertake a neural performance campaign before
both controls exist, pass independent oracles and have a frozen protocol. No
new theory, priority, speed or fulfilled goal is inferred from this construction.

## Reading-scope correction

V1's primary-audit referred too broadly to the institutional2009 source's Moore
sampler section: only its background, ordinary RS and displayed interval excerpts
were retrieved successfully; the later open/download returned Internal Error/403.
The independent original preprint arXiv:math/0612819v2 sections2–3 and appendix
interval statements were then read on2026-10-16:
https://arxiv.org/pdf/math/0612819 . It explicitly gives the validated-envelope
and acceptance-ratio mechanism. Do not claim a full reading of all2009 proofs
or of the phylogenetic numerical application. This correction strengthens the
antecedent attribution; it supplies no new performance/publication evidence.
