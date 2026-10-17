# Primary antecedents and real-consumer scope, before reference execution

2026-10-17. No exhaustive priority claim; exact read scopes below.

* [Gneiting/Raftery2007](https://sites.stat.washington.edu/people/raftery/Research/PDF/Gneiting2007jasa.pdf),
  Section4.2, Equations20/21 and divergence discussion read directly. CRPS,
  its expectation formula and strict propriety are antecedents. We use loss
  orientation, the negative of their initially oriented score. Proper-loss
  training is not our invention or a guarantee of good finite-data optimization.
* [Cortes/Haffner/Mohri2004](https://www.jmlr.org/papers/volume5/cortes04a/cortes04a.pdf),
  Definition3, weighted-automaton extension/Equation2, Sections4.1/4.2 through
  the final O(|T||A||B|)algorithm read directly. This ALREADY supplies exact
  min-kernel expectation via composition and DAG sums. A61 cannot claim this
  generic inference principle or its zero conditional sampling variance as new.
* [Roordink/Hess2023, Scoring rule nets](https://ecmlpkdd-storage.s3.eu-central-1.amazonaws.com/preprints/2023/research/lncs14170207.pdf),
  Section2.2/Definition1/Theorems1/2 read directly, not AppendixA's full proofs.
  It explicitly builds proper scores from observed-coordinate conditionals,
  including strict propriety for specified conditional chains. A61's
  category-log/conditional-mantissa combination is a specialization of known
  conditional-score principles, not discovery of conditional CRPS.
* [CALM2510.27688v1](https://arxiv.org/html/2510.27688v1), Sections3.2/3.3.1/
  3.3.2 read directly. It already trains a language generative head using a
  strictly proper energy score, estimated by samples of continuous vectors.
  That target differs from exact numerical value semantics, but it excludes
  claiming proper-score language training or the energy objective as new.
* [Regression Language Models for Code2026](https://proceedings.mlr.press/v306/akhauri26b.html),
  official PDF finally retrieved from its linked raw.githubusercontent.com
  source after web retrieval failed. Sections3/3.1/3.2/4.1/6.1/6.3 and
  AppendicesC/D.1 read as extracted text. It predicts code execution metrics
  using a frozen encoder and an autoregressive numerical decoder, with explicit
  sign/exponent/mantissa tokens and constrained sampling. Point estimates use
  64 samples. Its regression-head/codec ablations are substantive controls.
  This identifies a real numerical consumer, NOT an A61 dataset/model result;
  profiled labels and native compatibility have not been obtained/validated.
* [RegressLM author repository](https://github.com/google-deepmind/regress-lm),
  README read: existing library and code-metric examples. No repository code
  executed or dependency installed, no checkpoint/data availability assumed.
* [NTL2411.02083v3](https://arxiv.org/html/2411.02083v3),
  [SMMD2606.27731v1](https://arxiv.org/html/2606.27731v1) and
  [NTIL ACL2025](https://aclanthology.org/2025.acl-short.44.pdf) already had
  the method scopes recorded in A60/work/control-and-reading-v3.md. They are
  mandatory numerical/sequence-aware objective controls. Do not invent their
  absence or inherit A60's oracle/model evidence for A61.

An additional exponent-classification/mantissa-regression antecedent was
located: Regression Tree CNN for Estimation of Ground Sampling Distance Based
on Floating-Point Representation, Remote Sensing2019,11,2276. Publisher open
returned Internal Error; the full paper is NOT counted as read. Search snippets
already require caution about claiming that decomposition as new. Its full
method must be inspected before any promotion. No invented literature exclusion.

RLM-code cached original:3864291 bytes, SHA256
f7b76b1a9da974ddf412f6c93fcafdd0cad78ffc96d96da242e9964a672e0e21,
at /home/jota/.cache/tcc-final/a60-numerical-loss-reading/regression-language-models-for-code.pdf.
Cache is not redistributed in the attempt archive. Actual official download URL:
https://raw.githubusercontent.com/mlresearch/v306/main/assets/akhauri26b/akhauri26b.pdf.
These read scopes do not confirm A61 priority or substantial practical benefit.
