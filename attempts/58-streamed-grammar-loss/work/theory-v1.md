# V1 — Class statistics and a full neural-head backward

Written2026-10-16 BEFORE prototype or measurement. The identities are
classical differentiation/CRF/quotient rules. The hypothesis is a systems
implementation with a useful complete-cost consequence, not new algebra.

## Existing operation and exact mathematical contract

At a masked denoiser state, active slot i has hidden row H_i and classifier
rows W_v in ORIGINAL token-ID order, optionally bias b_v:

    ell_iv=H_i dot W_v+b_v,     p_iv=exp(ell_iv)/D_i.

Structural zero logits may be -infinity; every active row has positive total
mass. Fixed IDs have singleton weight1, not an evaluated head. A fixed class
map c(v) partitions ALL original IDs, including rejecting tokens. Acceptance
of original prefixes depends only on the unique class path. No parsing
ambiguity may duplicate an original word in the partition.

Let x range over grammatical completions through FIRST EOS at length T,
matching fixed IDs, with T>max(F). Let

    P(x)=product_(active i<T) p_i,x_i,   M_G=sum_(valid x) P(x)>0.

Unused suffixes have weight1. An existing positive weighted-prefix grammar
inference routine computes M_G and occupancy marginals

    nu_iC=Pr_G(i<T,c(X_i)=C),     a_i=sum_C nu_iC=Pr_G(i<T).

We do not invent that inference routine. In general a_i<1; it is NOT a
normalized token marginal after EOS. A sound support superset does not give
the exact same objective. All fixed original IDs/empty aliases remain literal.

For a supervised target with known original IDs t_i and nonnegative weights
w_i (zero outside its active target prefix), consider the KNOWN objective

    L=sum_i w_i[-log p_i,t_i] + lambda[-log M_G], lambda>=0.

Weights/noise mask/lambda are supplied constants. This is ordinary weighted
token CE plus semantic loss. No standard diffusion ELBO or quality theorem is
claimed for its regularized form. There is no new objective being advertised.

## Sufficient statistics, normalization and derivatives

Set z_iC=logsumexp_(v:c(v)=C) ell_iv, z_i=logsumexp_C z_iC, and
pi_iC=exp(z_iC-z_i). Empty-support classes have zero mass and zero occupancy.
The class probability rows pi, fixed-ID constraints and unchanged grammar
compute M_G and nu. Original target logits ell_i,t_i supply the CE numerator.
Thus z[N,C], target[N] and the grammar messages suffice; N*V logits need not
be retained. z_i is recovered from ALL classes, not only accepting ones.

Differentiate the prefix product. For a realized original prefix, its log
probability has derivative1[i<T](1[x_i=v]-p_iv). Summing against the
conditional grammatical posterior gives

    d log M_G / d ell_iv = nu_iv-a_i*p_iv,
    nu_iv=nu_i,c(v)*exp(ell_iv-z_i,c(v)).

Consequently

    dL/dell_iv = w_i*(p_iv-1[v=t_i])
                 +lambda*(a_i*p_iv-nu_iv).                    (1)

This includes grammatically rejecting IDs through the softmax normalizer.
When the valid length varies it is WRONG to replace a_i by1 or to assume the
position normalizers cancel. The sum of (1) over v is0 in every active row,
as required by invariance to shifting all logits in that row.

Equivalently the adjoint of the class statistic and separate target logit are

    d_iC=(w_i+lambda*a_i)*pi_iC-lambda*nu_iC,
    e_i=-w_i,
    dL/dell_iv=d_i,c(v)*exp(ell_iv-z_i,c(v))+e_i*1[v=t_i].   (2)

No ratio0/0 is formed: if z_iC=-infinity, its softmax/nu/adjoint are zero;
those original logits have zero derivative. Positive targets are required
whenever w_i>0. Infinite loss or zero valid mass is an explicit refusal, not
a successful zero-gradient training example.

More generally (2)'s second line is the exact backward for ANY differentiable
downstream function F(z,target), with arbitrary supplied class adjoints d
and target adjoints e. They can have mixed signs and need not be small.
Therefore a small original p_iv does NOT alone justify discarding a gradient
tile: exp(ell-z_class), and its arbitrary adjoint, can be order1 even when
the GLOBAL probability is tiny. No CE-specific filtering assumption transfers.

The head chain rule is ordinary dense differentiation, performed in tiles:

    dH=G*W,      dW=G^T*H,      db=sum_i G_iv,

where G denotes (2) but is NOT materialized. This produces full classifier
gradients; it is not a one-bias probe. If weights are tied to input embeddings,
autodiff must also ADD the gradient through the model's input-embedding branch.
An optimizer still stores its ordinary parameters/gradients/state.

## Proposed execution specialization, not a new inference primitive

Compile each class's original member IDs once. Divide a class into panels
of at most B vocabulary IDs. Each panel names exactly one class. Let

    K=sum_C ceil(|C|/B) <= V/B+C.

Forward: a row/panel tile directly gathers W at the original IDs, performs
H*W_panel^T and stable LSE within that panel on chip. Store only N*K panel
LSE values, then reduce panels belonging to each class. Indexed target dots
are computed once. Do NOT materialize a permuted V*D copy of W. Metadata is
immutable with respect to parameters; gradients scatter to the original IDs.
Using a small-class grouped dispatcher is allowed only after its own written
layout/validation; it is not silently credited to the first padded design.

Run the SAME grammar inference on pi. Return loss and class/target adjoints.
Backward recomputes each logit tile, scales by its cached class LSE/adjoint,
adds the target contribution and contracts to dH/dW/db in tiles. Accumulation
order and float atomics require numerical validation; real-arithmetic
equivalence does not imply bitwise GPU gradients. Do not cache a full N*V G.

Work is O(N*D*B*K) per projection/contraction scale, including padding up to
C*(B-1) columns. Extra activation/summary workspace is O(N*(C+K)+tile), plus
grammar messages, O(V) indices, targets and original H/W. Full dW storage is
O(V*D), dH is O(N*D), db is O(V). Those MUST be counted in memory reports.
Backbone activations/optimizer/distributed buffers and input-head copies
are not included in the head-only workspace expression. No claim of a new
asymptotic bound over all exact implementations is made.

## Competent controls and falsifiable benefit hypothesis

1. Dense equally optimized GEMM, class LSE, SAME grammar/loss, dense autograd.
2. Vocabulary-panel GEMMs with class reductions and checkpointed recomputation,
   returning the same z/targets; custom backward avoids keeping every panel.
   It may have the SAME asymptotic memory. Grant all metadata/preparation reuse.
3. CCE/linear-LSE applied to class submatrices plus indexed targets, with all
   filtering OFF, arbitrary upstream class adjoints and all relevant batching/
   small-class grouping. Charge gathers/copies equally; do not force a copy
   if an indirect implementation is available. This is the closest kernel
   template, not a different loss that we can beat by changing its objective.
4. Any existing grouped/segmented linear-LSE implementation that supplies
   the same operation with lower cost. A generic port is not sufficient own
   novelty. An equally optimized adaptation of CCE can defeat the candidate.

The plausible own advantage is one grouped indirect execution instead of
many launches or global logit/scatter panels. It is NOT the streaming identity
itself. Padding/gather traffic can reverse the advantage. Initial validation
is arithmetic correctness only. A separately frozen bounded GPU resource
screen must compare these controls BEFORE real training. No synthetic speed
result may be relabeled as whole-model or downstream semantic improvement.
If only the classical algebra survives, no broad neural campaign is triggered.

## Primary antecedents and limited actual reading

* Cut Cross-Entropy, https://arxiv.org/html/2411.09009v1, introduction/§§2--4.3
  including Algorithm2 and backward adjoints, and §5.3 read here. Original
  scalar linear-LSE and recomputed backward are the DIRECT mechanism template;
  vocabulary reordering is not ours. This is v1, not a claim that every later
  version or the current complete implementation was read. The final ICLR
  abstract and official https://github.com/apple/ml-cross-entropy were also
  inspected. No stronger novelty claim without checking current source.
* Xu et al.2018, https://proceedings.mlr.press/v80/xu18h/xu18h.pdf: semantic
  loss is an antecedent, not a new regularizer. Exact sections/definition must
  be read and recorded before implementation; locating the PDF alone is not
  reading it. CRF/weighted counting and neural grammar differentiation are
  also mandatory antecedents, not inventions.
* A28's inference-only reservoir and A36's sparse projection do not supply
  training measurements here; their negative decisions remain unchanged.
* MONOIDREDUCE OpenReviewFopv5Hpm1C was located; forum and PDF both returned
  browser-verification HTML. Its content was NOT read. A possibly relevant
  generic compiler cannot be excluded from title/search alone. Retrieve an
  original copy before any priority/promotion decision, not a secondary recap.

The next permitted step is primary/source comparison and a minimal independent
gradient oracle. No real head, model update, performance or priority follows
from writing this note.
