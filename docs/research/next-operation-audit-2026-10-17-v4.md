# Joint-temperature operation: a compact classical exact control

2026-10-17, AFTER the V3 actual-training-loss audit. Written mathematics and
original-source reading only, no new implementation or scientific run.
The real consumer is joint sampling at one frozen CoDD denoiser state.
The exact target here is P_beta(x)=P(x)^beta/Z_beta, beta>=1, not an entire
diffusion trajectory tempered after marginalizing all its histories.
Original token outcomes remain distinct. No quality/latency result follows.

## 1. The consumer and the exactness gap are already documented

CoDD v2 Section5.1 describes two approximate temperature strategies: tempering
conditionals within a sampled latent route, and tempering successive
conditional distributions in any order. Its authors explicitly acknowledge
the distinction from a power of the joint distribution. This is not a new
criticism of a claimed exact CoDD algorithm.

Long Horizon Temperature Scaling, ICML2023, already treats this general
joint-versus-local distinction and learns an amortized approximation. Its
existence prevents claiming invention of joint-temperature control. A possible
new algorithm would have to improve the exact operation at useful complete
cost, against competent circuit/rejection controls, not merely oppose exact
sampling to an approximate law without charging its extra work.

## 2. A classical norm-weighted mixture envelope

Normalize a smooth decomposable categorical PC at the frozen state. Its
latent-route expansion has

    P(x)=sum_z pi_z g_z(x),   sum_z pi_z=1,
    g_z(x)=product_(leaf l in z) g_l(x_l),

with each g_l normalized and product scopes disjoint. Routes need not be
enumerated. For ANY positive numbers u_z, define

    A=sum_z pi_z u_z,
    F(x)=sum_z pi_z g_z(x)^beta/u_z^(beta-1),
    C=sum_x F(x).

Weighted Holder gives the pointwise upper bound

    P(x)^beta <= A^(beta-1) F(x)=:E(x).                    (1)

Indeed, write pi_z g_z=(pi_z u_z)^((beta-1)/beta)
*(pi_z g_z^beta/u_z^(beta-1))^(1/beta) and apply Holder.
For beta=1, F=P and equality holds. Rejection from Q=F/C with acceptance
P(x)^beta/[A^(beta-1)F(x)] therefore gives EXACT P_beta, with expected attempts

    M/Z_beta,   M=A^(beta-1) C.                           (2)

Positive P implies positive F; proposal-zero points need not be tested.
This is ordinary rejection sampling plus a classical inequality, not a new
principle. A finite cap has a FAIL event of probability(1-Z_beta/M)^cap;
it does not preserve unconditional target equality on a space omitting FAIL.

Let Z_z=sum_x g_z(x)^beta. Minimizing the ENVELOPE FAMILY in1 over all u_z
(up to common scaling) gives u_z=Z_z^(1/beta) and

    M_*=(sum_z pi_z Z_z^(1/beta))^beta.                    (3)

This follows from Holder applied to sum_z pi_z Z_z^(1/beta), with equality
at those u_z. It is only optimality inside this specified Holder family,
NOT among all exact samplers, all mixture envelopes or all ways of using
known component densities. It is the classical Minkowski norm bound.
The choice u_z=1 gives the Jensen envelope M_J=sum_z pi_z Z_z, and
M_*<=M_J. That is a valid comparative fact but by itself not own novelty.

## 3. A competent compact control already avoids route enumeration

For product routes, Z_z=product_l Z_l and the minimizing weights factor:

    u_z=product_l u_l,  u_l=(sum_v g_l(v)^beta)^(1/beta).

Evaluate the ORIGINAL circuit on scalar leaves u_l to obtain A. Form F
with the SAME graph/sum weights and leaf functions

    f_l(v)=g_l(v)^beta/u_l^(beta-1).

Since sum_v f_l(v)=u_l, ordinary inside evaluation gives C=A. Ordinary
ancestral sampling of the normalized F circuit gives Q; point evaluation
of original P and F supplies1. Preparing these leaf tables and messages
costs O(circuit size + total explicit leaf entries) ARITHMETIC operations.
An accepted result needs the preparation plus M_*/Z_beta ordinary proposal/
point-evaluation costs. Shared nodes can use their standard cached messages.
No flattened exponential list of latent routes is necessary.

This is the strong CLASSICAL COMPACT CONTROL, obtained by ordinary leaf
reweighting, evaluation and sampling. It receives the same information,
representation and cached frozen neural potentials as any proposed wrapper.
Do not compare only with naive rejection, Jensen weights or route enumeration
and then claim an exclusive tractability/complexity advantage. This audit
itself has not independently established published priority for this exact
PC wrapper; a direct classical composition is already sufficient to defeat
that generic separating argument.

Arithmetic count is not bit cost or measured GPU latency. Fractional powers,
normalization, exact categorical choices and acceptance comparisons need a
declared real-arithmetic model or certified lazy arithmetic. Computing them
with ordinary floats and clamping is not a proof of exact native RNG law.
For beta=2 arbitrary positive rational u_l yield rational A,F,C and M=A*C;
exact ideal square roots are unnecessary for validity, although loose choices
can hurt cost. No implementation or bit-runtime bound is claimed here.

## 4. An impressive comparison with Jensen still fails the strong control

A constructed proof family makes the objection explicit. On M outcomes,
including0, let

    P=epsilon delta_0+(1-epsilon)Uniform_M,  beta=2,
    epsilon=1/k, M=k^4, k>=2.

The exact squared normalizer, Jensen envelope and ideal Holder envelope are

    Z=epsilon^2+(1-epsilon^2)/M,
    M_J=epsilon+(1-epsilon)/M,
    M_*=[epsilon+(1-epsilon)/sqrt(M)]^2.

Consequently M_J/Z grows as k, whereas M_*/Z tends1. Naive rejection with
bound1 costs1/Z of order k^2. This is a genuine mathematical improvement
against those TWO specified controls, not evidence against all competent
methods or a practical neural benchmark.

In fact an even simpler exact control beats the premise of that comparison:

    P(x)^2 = c0 delta_0(x)+cU Uniform_M(x),
    c0=epsilon^2+2epsilon(1-epsilon)/M,
    cU=(1-epsilon)^2/M.

Choose the two mixture branches with weights c0,cU and sample directly.
Its sum is Z; no rejection or domain enumeration is needed. A uniform product
representation and a point mass give a compact ordinary product/power control.
All scalar work and uniform-output bit/serialization costs still count.
Thus neither a favorable k-factor nor this family supplies an own useful
advantage over the strong compact comparator.

For this family, the latent-route conditional-tempering law retains the
original mixture weights and equals P; its total variation from P^2/Z tends1.
That illustrates an acknowledged approximation gap, not a counterexample to
CoDD's claimed exactness. The cheap exact two-component control still exists.
Higher likelihood under a chosen joint is not a semantic-correctness theorem.

## 5. Full-cost and representation objections before any campaign

The normalizer M_*/Z_beta can still be large. For example, expanding an
independent uniform n-bit distribution into deterministic latent leaves gives
M_*=1 and Z_2=2^-n for this GLOBAL rejection scheme. A compact product of n
binary-mixture circuits can have that latent expansion. Yet the SAME target
is sampled directly as independent fair bits, or by handling its disjoint
sum supports with the classical exact power rule. A competent implementation
must exploit product structure and deterministic sums rather than force that
global rejection schedule. This is a written adverse example, not timing.

For a real CoDD prior, all leaf/head projection, node normalization, proposal
preparation, candidates rejected, P/F evaluation, RNG, copies, synchronization,
backbone forwards and selected-step policy costs would be charged. One frozen
head is not an exact whole-decoder temperature law. Atlas2021's deterministic
real-power and structured integer-power operations remain direct controls.
WMB/OS*-style bounds and refinements are antecedents; no generic refinement
principle can be advertised as new. No trained prior, model logits, external
row, label, source code execution or competitive timing was obtained here.

## 6. Eight-criterion decision

1. Real operation: CoDD's joint-temperature sampling at a frozen denoiser state
   is a genuine externally documented use, unlike A69's engineered response.
2. Own difference: the proposed norm envelope reduces to classical Holder/
   Minkowski and ordinary PC operations; sufficient own novelty is absent.
3. Choice/comparison: a compact classical controller computes the SAME bound,
   proposal and law. The favorable proof family also has a better direct
   exact control. Do not claim victory from Jensen-only comparisons.
4. Mathematics: Sections2--4 are self-contained WRITTEN constructions and
   adverse comparisons, not a new mechanized theorem or tested sampler.
5. Experiment: no substantive prototype/campaign is selected from this lead.
6. Costs: Section5 retains full preparation and rejection/bit/model costs;
   cheap arithmetic counts and a shared head do not establish whole latency.
7. Fatal objections: compact classical equivalence, mixture-specific direct
   powers and potentially exponential global rejection costs.
8. Article: identify a substantive additional own useful consequence before
   a new attempt or implementation. Exactness alone and a missing public
   wrapper do not establish adequate scientific difference.

Decision: preserve this as an analytical classical control and do NOT open
A70 for the basic norm-weighted exact-temperature wrapper. This is not a
negative neural result or a proof that exact tempering cannot be practical.
The user's positive goal remains OPEN; older declined applications and all
frozen proofs/evidence remain unchanged.

## 7. Original-source scope and hashes

- CoDD2603.00045v2 Section5.1 reread; previous source hash/read scopes stay in
  V3. No original code/checkpoint or complete paper was audited here.
- Shih/Sadigh/Ermon, FINAL ICML2023 *Long Horizon Temperature Scaling*:
  https://proceedings.mlr.press/v202/shih23a/shih23a.pdf
  PDF1029970 bytes, SHA256
  57c0bbc4bed5556ba18d0e32ed04bcb38f4147dd71df32e80e3df06b4329582f.
  Read introduction/background and Sections4/4.1/4.2, Corollary4.1 and
  Proposition4.2 with displayed proofs. Experimental results/full appendix
  were not independently audited or reproduced. Their amortized model is
  an approximation, not the exact rejection operation derived above.
- Liu/Ihler, ORIGINAL ICML2011 *Bounding the Partition Function using Holder's
  Inequality*: https://icml.cc/2011/papers/459_icmlpaper.pdf
  PDF407643 bytes, SHA256
  d71c19c16b0fa68e726e0828e0cbc7541fd95d64b206f8ff5f340e4b773222d8.
  Read Sections2.2/3 including Algorithm1 and displayed weighted-Holder rule;
  adjacent4.1 was displayed but its complete theory/optimization proofs and
  experiments were not audited. It supplies a primary general-bound antecedent,
  not a claim that its original paper implements this exact PC wrapper.
  The retrieval/extraction succeeded; the combined reader command ended1
  because its final rg search for sampling/rejection had no match, not from
  a failed scientific run or missing PDF.
- Sun/Nicholls/Lee2601.22367v2 ORIGINAL AppendixE Gaussian-mixture paragraph
  read at https://arxiv.org/html/2601.22367v2 . It explicitly uses an exact
  mixture-envelope rejection control; not its full theory/code/experiments.
- A rendered historical R mixture-rejection source in hierarchicalFusion's
  documentation was inspected only as a lead. No original Git revision was
  pinned/audited, and it is not used to certify priority or infer an optimized
  PC algorithm. Search snippets are not absence-of-prior-art evidence.
