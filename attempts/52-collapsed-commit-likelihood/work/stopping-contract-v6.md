# V6 — Written stopping-law diagnostic, before its code or measurements

2026-10-16. V5 is CLOSED NEGATIVE. This is a new contract audit, not a revised
V5 result, semantic-success campaign or training authorization. No invention of
absorbing automata, suffix marginalization, length mixtures or monotone tilting
is claimed. Scientific originality/usefulness remain OPEN.

## Eight criteria, limited to a diagnostic

1. Operation: audit the probability law for a numeric JSON response consumed
   only up to its first true EOT. Native dLLM software trims there; a consumer
   does not require its sampled unused suffix to equal PAD. This matters before
   using a grammar-conditioned head as the environment of a learned release rule.
2. Difference: V4/V5 explicitly used another, legitimate FULL-WORD target,
   JSON EOT PAD*. Its correctness claims remain under THAT declared law. A
   stopped response marginalizes all unused suffix IDs instead. This is basic
   probability/automata semantics, not sufficient own scientific novelty.
3. Why audit: suffix PAD logits can systematically favor long prefixes and
   may explain V5's long nonsensical numbers. This is a hypothesis about cause,
   not a claim that a different law will improve semantic answers or training.
   Competent controls are direct stopped-prefix DP and the explicit length
   mixture; they implement the SAME target, not inferior invented baselines.
4. Proof: below, both laws, their exact length-marginal TV identity and a
   stochastic length ordering are derived before code. These are classical
   mixture/monotone-likelihood-ratio consequences. No speed gain follows.
5. Experiment: after small independent rational oracles, audit ALL8 cached
   V4 original initial heads, no new head, sampling, label access or update.
   Compare complete first-EOT mass vectors/log normalizers for both laws and
   an independent absorbing-DFA computation. All8 states remain in the report.
6. Cost: full original V151936 normalization, tokenizer/effect compilation,
   prefix/suffix mass passes and original ID provenance. This is not a timing
   contest; source freeze precedes the audit. Fixed rows are explicit original
   IDs. No inheritance of V5 timings or claims of a native iterative decoder.
7. Objections: simple termination mistakes are not a scientific contribution;
   no empirical cause or semantic gain is guaranteed by a length difference.
   Native generation laws are not replaced by a frozen head's product.
   EOS/PAD/fill conventions vary across model runtimes; verify concrete code.
8. Article gap: substantial own result and useful learning with competent
   controls/independent confirmation. A passing diagnostic only motivates
   designing a properly stopped consumer separately. It does not meet the goal.

## Primary source scope

Official ZHZisZZ/dllm snapshot ca176752fbceec49c6b4777a2c18ae88e4eb10ed:
dllm/utils/sampling.py sample_trim/infill_trim were read in full; both locate
the first response EOS/EOT and discard its suffix. The initialization portion
of core/samplers/mdlm.py and compute_loss's masking/loss portion of
core/trainers/mdlm.py were also read. The latter excludes labels=-100; this
does not prove the exact training-padding history of our checkpoint. No
claim that it never learned PAD is made. Exact file hashes/scopes are retained
before use. No upstream/vendor source was modified or executed in this audit.

## Declared finite law and identities

Let X_1,...,X_n be independent ORIGINAL IDs with normalized rows c_i over
the entire model vocabulary, including explicit aliases/empty IDs. E is the
true EOT ID and T is its first index. Event H says T<=n and the bytes strictly
before it form the declared JSON-number schema. Before E, use the exact same
literal-key JSON lexer as V4, including every original byte/empty emission.

The stopped target is the conditional full-word law P(X|H), OBSERVED through
prefix X_1:T. There is no restriction on X_(T+1):n: every original ID remains
in that latent suffix, including EOT/PAD/MASK/non-ASCII/undefined IDs. It can
be integrated rather than sampled because each unused row sums to1. This is
represented classically by an accepting absorbing automaton state with a
self-loop for EVERY original ID. Replacing tails by PAD in serialized output
AFTER sampling would not mean sampling their model PAD probabilities.

Write z_t = sum_(valid first-EOT prefixes of length t) product_(i<=t)c_i(x_i).
Then Z_stop=sum_t z_t and a particular prefix has mass W_prefix/Z_stop.
The V4/V5 full-word PAD target instead gives that prefix mass

    W_prefix * r_t / Z_pad,
    r_t=product_(i>t)c_i(PAD),   Z_pad=sum_t z_t*r_t.

Proof: sum the independent suffix. Its unrestricted mass is1, whereas fixing
every suffix ID to PAD contributes r_t. The conditional prefix law given T=t
is IDENTICAL in both targets. Consequently the entire prefix-distribution TV
is exactly the TV between their length distributions:

    TV(P_stop_prefix,P_pad_prefix)
      = (1/2)sum_t |z_t/Z_stop - z_t*r_t/Z_pad|.

This does not establish semantic TV or correctness differences. Since
r_(t+1)=r_t/c_(t+1)(PAD)>=r_t when positive PAD probabilities are<=1, the PAD
target is an increasing likelihood-ratio tilt of T. Thus

    P_pad(T>=k) >= P_stop(T>=k) for every k,
    E_pad T >= E_stop T.

One proof is Cov(f(T),r(T))>=0 for increasing f,r, by averaging
(f(T)-f(T'))(r(T)-r(T'))>=0 over independent T,T'. Use f=1[T>=k]. Strictness
needs positive masses at two lengths with a strict intervening PAD factor.
The two prefix laws coincide iff r_t is constant on positive z_t support.
Zero PAD weights may exclude some lengths; those cases need explicit support
handling, not division by zero. These are elementary classical results.

The distortion may be arbitrarily large: a positive-mass short valid prefix
and a longer one can have equal z_t, while the short one's extra PAD factor
is epsilon. Their stopped probabilities are1/2 each, and the short prefix's
PAD probability is epsilon/(1+epsilon). A JSON fixture can use one complete
numeric-object token versus two tokens for another object. This is a proof
object, not a constructed benchmark or evidence for a good neural model.

## Minimal next implementation/audit contract

First independent full original-word enumeration on tiny normalized rational
tables, with JSON parser, empty aliases, EOT/PAD/MASK/invalid bytes in suffix,
fixed original IDs, zero weights, full prefix masses, TV identity and stochastic
ordering. Preserve the old NumericJSON/FloatPlan and all frozen sources. Any
new stopped helper is separate. It must never infer active state solely from
ID==MASK: MASK is a legal ORIGINAL latent suffix ID in this law. A future
iterative consumer must keep an explicit fixed/active mask and expose its
attention/termination/score contract BEFORE new model calls. None is authorized
by this diagnostic alone.

Then a separately source-frozen old-head audit uses all8 V4 initial heads,
FULL original IDs, no new model calls. Compute first-EOT masses with forward
states that remove already stopped flow, and an independent absorbing-state
partition. Record Z_stop, Z_pad, every normalized first-EOT mass, TV, means,
survival probabilities and all discrepancies. Verify the old Z_pad against
the original PAD-DFA and direct prefix-times-suffix mixture. Use log-space
scales when masses underflow; no hidden epsilon mass flooring. Resource caps
as V4; all refusals/errors remain cases. No competitiveness or quality claims.

Predeclared diagnostic interest condition: at least6/8 heads have TV>=0.2
AND E_padT-E_stopT>=4 original-token positions. It only motivates writing a
new stopped-consumer feasibility protocol. Failure rejects this proposed cause
as a broadly large length effect in these states. Passing is no semantic gain,
new theory, independent confirmation, training result or fulfilled goal.
