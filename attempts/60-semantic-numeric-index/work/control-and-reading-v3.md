# V3 — Classical machinery, numerical consumers and the remaining difference

2026-10-17. After the first tiny oracle, before any resource/model campaign.
The eight README criteria remain active. No comparative win is established.

## 1. A complete generic control can reproduce this index

Supply a generic weighted-transducer implementation with the written relation
N_L from V1, not just a DFA recognizing a subset of canonical numerals. Expand
the ORIGINAL-token source to a byte DAG, compose it with N_L using a correct
epsilon filter, and project its output. Initial-header ownership is an allowed
specialization of that filter. Keep parallel paths and sum their weights;
do not determinize or require one source spelling per numerical value.

The same product states, digit-emitting edges and suffix masses as A60 are
then available to classical weighted-prefix queries. After any prefix u, let
alpha_u be its forward vector immediately after the last nonempty output edge.
Its next-event masses are

    terminal(u) = sum_q closure(alpha_u)(q) final(q)
    block(u,c) = sum_(q--c/w-->r) closure(alpha_u)(q) w beta(r).

They are IDENTICAL to the candidate's events, including alias sums. Memoizing
these vectors at visited prefixes yields identical sharing across quantile
queries. A complete register program emitting digit events can likewise store
its finite syntax/order/mode snapshots; sharing snapshots is the classical
finite-state representation, not a new algorithmic advantage for the index.

This is an analytical construction, not an independently implemented control,
measured timing, or a lower bound on every other algorithm. It establishes
that a generic own inference/quantile speed claim is unjustified by V1 alone.
It does NOT prove that the specific O_I(L) numerical relation already appears
in a publication: Mohri's generic algorithms still need that relation as input.
The remaining candidate is the SPECIFIC relation/operator and its useful
application, not weighted composition, prefix caching, or inverse CDF itself.

## 2. Closest numerical consumers actually read

* [LLM Processes2405.12856v2](https://arxiv.org/html/2405.12856v2), Section2,
  AppendixA.1/A.2 andH.1 read directly. They derive numerical densities from
  digit-prefix/bin likelihoods plus a terminal token; explicitly distinguish
  this from exact bin mass of the sampling distribution, and compare with
  1000 samples per target. This is a substantive prior for direct numerical
  distribution readouts. A60's exact pushforward of a finite weighted source
  is a different target, not an established improvement over their regression.
* [NTL2411.02083v3](https://arxiv.org/html/2411.02083v3), Section2 through its
  Wasserstein definition/discussion read directly. Mapping numeric-token
  probabilities to numerical losses, absolute-error transport and CDF losses
  are antecedents. A60 cannot invent numerical supervision by adding a loss.
* [SMMD2606.27731v1](https://arxiv.org/html/2606.27731v1), Section3.0--3.3 read
  directly. It conditions on a numeric TOKEN sub-vocabulary, parses its values,
  and uses value-distance kernels/MMD and residual smoothing. That is not the
  complete multi-token scientific-spelling distribution; this difference by
  itself proves no own speed, training quality or academic priority.
* [NTIL's official ACL2025 paper](https://aclanthology.org/2025.acl-short.44.pdf),
  Sections3.1/3.2 subsequently read directly in the same work unit. It weights
  digit EMD by position and constructs a multi-token numerical prediction
  with a Gumbel-softmax approximation, then applies relative/magnitude losses.
  Sequence-aware numerical discrepancy is an antecedent; exact weighted-source
  integration is a different contract, not an automatic own training benefit.
  No training extension is implemented or triggered by these observations.

The LMCS CWidth Theorem5.3 proof was re-opened/read directly after context
recovery. It materializes polynomially many assignments to a constant number
of spans of a FIXED document and their binary multiplicities before aggregation.
This is not automatically A60's potentially exponential support of numerical
values from a weighted source. Conversely, that contract difference is not
an exclusion of every theorem or extension in the paper. No priority result.

## 3. Canonical-only conditioning is a different law

For V1's four-word source, the pushforward has P(1)=3/5 and P(90)=2/5.
Restricting the source to the canonical strings1 and90, instead of summing
all equivalent spellings, produces probabilities3/7 and4/7 respectively.
Its median changes from1 to90. This is the standard distinction between
conditioning and a pushforward, not new probability theory or model evidence.
Canonicalize AFTER an admitted original draw to preserve its numerical law;
canonical-only grammar conditioning generally does not. If a real consumer
can freely choose a different prediction law, the canonical decoder remains
a legitimate practical comparator and its quality/cost must be measured.

## 4. Decision and smallest useful next work

Four tiny oracles justify retaining the mathematical reference. They do not
trigger full-V/native implementation, head capture, training or a cost campaign.
Before expansion, investigate the specific bounded numerical relation against
complete numerical-register/transducer antecedents and identify a substantive
own consequence for an actual consumer. If a complete classical encoding
already provides it, credit that result and move on; more precision or more
oracle counts would not resolve novelty. If a specific useful difference
survives, write a resource protocol with complete cached and generic controls
before collecting data. The original positive user goal remains OPEN.
