# V2 — Check admitted words, keep the original normalizers

Before executing the oracle, the reference's point-density path was found to
multiply the token weights without checking grammar membership. The theorem
defines density zero outside F. A caller supplying a draft that is NOT a
sample from Q must be rejected, not assigned a positive density. The initial
draft is preserved at 7f0fbdd and is UNVALIDATED, not a successful producer.

The correction adds a Boolean forest-membership pass to every point query.
Its full O(H) work is paid. No source/grammar/target distribution is changed.
The reference also refuses n=0 and invalid tail tolerances, because its
sampling accuracy is specified as 1/(4n). The eight README criteria and written
theorem are unchanged; neither this fix nor a passing oracle confirms novelty.

The prospective oracle exhausts small rational tails and original-token
assignments using an independent JSON parser/stack recognizer. It reconstructs
all proposal and accepted probabilities, checking pointwise envelopes and
both coupling marginals. It includes singular supports, equality, an invalid
draft, aliases, token prefixes, fixed positions and rational perturbations.
No model/timing/quality campaign follows merely from passing these checks.
