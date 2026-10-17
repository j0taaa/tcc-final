# Training-operation audit before another implementation

2026-10-17. AFTER A69 V4, whose present application expansion is declined.
This is an operation/literature/math audit, not a selected A70, a model
experiment, a new algorithm or an achieved positive goal. No source, loss,
training loop or old frozen scientific file is changed.

## 1. The proposed shortcut must preserve the actual loss

Question examined: can a grammar certify a zero-gradient corrupted example
before running the denoiser, so training skips the entire neural forward?
The qualification is essential: a uniquely valid completion does NOT give
zero loss or zero gradient for the operation currently preserved in A58.
That operation is ordinary token CE PLUS nonnegative semantic regularization,
not a normalized grammar-conditional likelihood.

An exact one-slot counterexample suffices. Vocabulary={a,b}, target=a,
G={a}, p_theta(a)=s(z), p_theta(b)=1-s(z), where s is logistic. Take CE
weight1 and semantic-loss weight lambda>=0. The existing loss is

    L(z)=-log s(z) + lambda[-log Pr_theta(G)]
        =-(1+lambda)log s(z),
    L'(z)=(1+lambda)(s(z)-1).

At z=0 this is -(1+lambda)/2, despite there being exactly ONE valid
completion. Discarding it as zero would change the expected gradient.
This is a WRITTEN elementary counterexample, not a new finite oracle run.

For a DIFFERENT loss, -log Q_theta(a) with
Q_theta(x)=P_theta(x)1[x in G]/Pr_theta(G), Q_theta(a)=1 and the loss and
gradient really are zero. Equivalently the conditional loss ADDS log Pr(G)
to CE; it does not add the nonnegative semantic-loss term of A58. That
conditional objective can be sensible, but it is a model/objective choice,
not a loss-preserving accelerator of the existing operation. Do not inherit
A58's failed cost gate, validity checks or training claims for this new loss.

Original token IDs also matter. One valid BYTE string can have several
original-ID tokenizations/aliases, leaving a nontrivial conditional law.
The zero-gradient certificate would need a singleton in the actual modeled
sample space, not merely agreement after rendering or canonicalization.

## 2. The generic conditioning argument is classical

Suppose some independently justified loss DOES have gradient G=0 off an
event A determined without the expensive neural evaluation. Let a=Pr(A)>0
be KNOWN, independent of theta, and assume square integrability. Drawing
conditionally and returning G*=a G|A gives the standard identities

    E G*=E G=:mu,
    Cov(G*)=a Cov(G)-(1-a)mu mu^T <= a Cov(G).

These follow by expanding first/second moments. They are classical
conditional Monte Carlo, not our invention or a quality/convergence theorem.
A cheap rejection loop that tests A BEFORE evaluating the model produces
the SAME conditional sampling law. It is a mandatory competent controller;
comparing only with an implementation that always runs zero-gradient
examples would not establish an own benefit.

All proposal/parsing/rejection/normalization costs must be charged. Exact a
cannot be replaced silently by an acceptance-rate estimate; an adaptive
optimizer's entire path is not preserved merely by preserving one expected
gradient. If a=0, the objective's gradient contribution is identically zero
under these hypotheses; conditional sampling is undefined and unnecessary.
These observations do not select an extensive implementation.

## 3. Closest original structured-training consumers

The original CoDD paper already trains a normalized product of a structured
probabilistic-circuit prior and context-dependent unary denoiser potentials.
Sections4.1--4.3 therefore defeat a generic novelty claim for replacing
independent CE by a structured normalized denoising objective. Using a hard
prior requires support and representation checks; it does not turn the
normalization rule into a new principle.

A separate real consumer, Diffusion-MF, already puts a linear-chain CRF
inside the denoising loop. Its published formulation uses categorical
replacement noise, which does not reveal the clean label wherever a symbol
is observed. Thus a visible label is NOT a monotone fixed pin as it is in an
absorbing-mask model. A singleton-canvas argument cannot simply be transferred
to this noise process. Its V3 training discussion also explicitly separates
posterior and direct denoising terms; a skipped-example argument would have
to cover the ACTUAL complete objective, not only one convenient component.

The original2026 results are THEIR reported results, not reproduced or
validated here. No dataset row, label, code execution, trained model, neural
forward, optimizer update or timing is credited by this audit.

Sources:
- CoDD v2: https://arxiv.org/html/2603.00045v2 , Sections4.1--4.3.
- Diffusion-MF v3: https://arxiv.org/html/2606.18856v3 , Sections1/2.

## 4. Adjacent exact-inference leads do not yet provide an own difference

A chain-structured denoiser can be combined with independent corruption
channels by ordinary latent-chain inference. Sampling the clean joint and
then its local corruption channels is an exact mixture sampler. Likelihood
of a fixed previous sequence is another chain partition with local evidence.
This is a classical hidden-state construction, not a new exact-denoising
principle. It also does NOT automatically make an expectation of a logarithm
tractable, or prove better learning/latency than equally optimized controls.

CoDD's displayed Section5.1 explicitly recognizes the hardness of general
word-level temperature powers and proposes approximate samplers. A new
method would need an own useful guarantee beyond ordinary product-power
closure on deterministic circuits, integer replicas or generic rejection.
The old A57 audit already records Atlas2021's power/product/integration
antecedents. No exact-tempering prototype is selected from this observation.

Nor is making the prior depend on the noisy canvas by itself an own novelty:
CoDD AppendixE already outlines latent-space modulation. The initial E.1
construction was inspected, not independently implemented or validated here.
Do not infer from its being an appendix/future direction that the idea is
unpublished. These boundaries help direct the next search, not an application
performance claim.

## 5. Decision against the eight research criteria

1. Operation: training structured denoisers is real; no demonstrated unmet
   need in the preserved CE+semantic-loss operation is solved by the shortcut.
2. Own difference: structured normalization and zero-event conditioning have
   primary/classical antecedents; no sufficient own mechanism is identified.
3. Comparison: the cheap before-forward rejection controller has the same
   conditional law, while the existing loss has the nonzero-gradient example.
4. Mathematics: the counterexample and covariance identity above are written
   and self-contained; they reject a broad shortcut, not supply new theory.
5. Experiment: no new experimental gate or prototype is justified yet.
6. Costs: parsing/proposal/normalization, aliases, backbone/head/backward and
   optimizer remain charged. A changed objective cannot inherit old timings.
7. Fatal objections: different loss, wrong pin interpretation under replacement
   noise, classical conditional sampling, and existing structured denoisers.
8. Article: an additional own useful consequence and an actual equivalent
   consumer/comparator are still required. Do not build a new training stack
   merely because the conditional loss can have zero-gradient states.

The zero-gradient shortcut is NOT selected as the next practical contribution.
No A70 is opened from these facts. A69's theorem remains preserved without
expanding its declined application; A58 and other negative gates remain closed.
The positive user goal stays OPEN. The next substantive implementation needs
a distinct useful claim that survives its competent classical control first.

## 6. Exact original-reading scope and retrieval provenance

- CoDD ORIGINAL PDF explicitly requested at /pdf/2603.00045v2,1381800 bytes,
  SHA256 734e0d9de571b81818dea82d07bf5a2ab4730881cfae429b4a987990314e013d.
  Read Sections4.1--4.3 and displayed5.1, selected6.2 text, AppendixD's soft-
  evidence statement and initial E/E.1 modulation construction. Not the
  complete experiments, proofs/appendices or implementation. Original HTML
  v2 method paragraphs were cross-read; no complete-paper reading claim.
- The initial structured-labelling HTML opened /html/2606.18856v1. The later
  unversioned PDF resolved to V3, *Diffusion-MF*, dated6August2026,488408 bytes,
  SHA256 379dd1bddd646daa867b8c2004d32bc86887b2fbb18b7e3052154265c0f88db5.
  Its header/version were inspected; Sections1/2 and the beginning of3.1 were
  read, including the V3 hybrid-loss description. Pinned V3 HTML was then
  opened to confirm the current version/model equations. V1's snippets are
  not relabelled as V3, and the V3 PDF is not attributed to V1. No original
  artifact/code, later ablation tables or full appendices were audited here.

Hashes identify the actually read documents; they do not prove originality,
review, practical gains or an experiment that was never run.
