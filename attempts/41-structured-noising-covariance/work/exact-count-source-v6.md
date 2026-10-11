# Exact rational count-noising source, BEFORE any model output

2026-10-11. V5 used a declared finite128-bit seed map; it did NOT equal the
ideal count-noising law. Preserve v5, which has ZERO external forwards.
This refinement makes the current operation exactly the known count-NELBO
target, with no numerical integration over continuous time. It is a standard
uniform-ticket embedding/combinatorial unranking, NOT a novelty claim.

For n clean token positions let L=lcm_(k=1..n) choose(n,k), M=n*L. A uniform
source address s in0..M-1 determines k=floor(s/L)+1. Its remainder in0..L-1
determines a subset rank r=floor((s mod L)/(L/choose(n,k))) and a latent
alias. Unrank r lexicographically into a k-subset. Every k has probability
1/n and every subset has conditional probability1/choose(n,k), EXACTLY.
Thus its normalized mean masked NLL has expectation the original normalized
time-INDEPENDENT denoiser's continuous NELBO by the known Beta integration.
Its output-bias gradient has the same expectation by finite differentiation.

The C4 law operates on original uniform addresses, keeping every alias
separate. It preserves actual masks and their scores/gradients; aliases that
render the same corruption do not create new text/token choices. Classifier
is fixed before addresses, even if fitted on past independent observations.
The universal arbitrary-score covariance theorem therefore applies to the
ORIGINAL target, not merely a128-bit approximation to the mask distribution.

The LCM and binomial integers use polynomially many bits: each binomial
has at most n+1 bits and L is no larger than their product, so log2 M is
O(n^2+log n). Construct only n such integers, never enumerate M or2^n masks.
Uniform ticket draws and O(n) unranking decisions have charged bit arithmetic.
More refined binomial-LCM identities are unnecessary for this safe bound.
All raw preparation/classification/teacher/CPU/neural/output costs remain.

The source's transparent aliases and known mask-count probabilities are extra
information. The opaque arbitrary-map minimax lower bounds MUST NOT be claimed
optimal for all specialized count-noising algorithms. Analytical count
stratification, mask inverses, source/INPUT caching, exact proxy expectation,
Rao-Blackwell, importance, learned-order RSS and equally lazy pivotal controls
are still legitimate. Preserving a target is correctness, not novelty/speed.

Refines README criteria1/4/6/7: actual mathematical target and scope are clearer,
but the distinct query theorem's priority/significance and real benefit remain
open. Freeze new producer/protocol before ALL six real information records;
the known-bank audit is still DEVELOPMENT and NOT a comparative victory.
