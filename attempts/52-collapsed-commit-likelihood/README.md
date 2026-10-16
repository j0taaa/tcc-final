# A52 — Likelihood of the action actually committed

2026-10-16. Contract/proof BEFORE prototype, training, new heads or timings.
This is a limited tractability/variance investigation following the NEGATIVE
A51 operational gate. It does not revive A17's Plackett–Luce campaign or claim
that ordinary weighted counting, conditional scores or Rao–Blackwellization
are new. No practical advantage or sufficient originality is established.

1. **Real use.** Auditing/optimizing a grammar-conditioned dLLM transition:
   propose a complete original-ID word, retain positions selected by sampled
   token confidence, discard the other proposals. Software consumes the new
   canvas and its transition probability/score. Mosaic's published LLaDA2
   threshold/fallback rule is the concrete consumer. Its choice depends on
   sampled tokens, so it is not a position set fixed before token sampling.
2. **Difference/significance.** Candidate distinction is a tractable EXACT
   observed-action likelihood for this existing confidence rule, including
   discarded proposals and grammar dependence. DUEL selects positions before
   sampling; MAPG changes selection to stochastic Plackett–Luce. Neither is
   falsely described as failing its own contract. A17 concerns that different
   PL law. A35's hard greedy/MWPC accepted-tag law is also different. The new
   reduction uses CLASSICAL unary evidence on a weighted grammar; an article
   requires a distinct useful application beyond this direct composition.
3. **Why choose it.** The collapsed score is the conditional mean of the full
   proposal score, so it has no greater covariance for action-measurable
   rewards. A connected checksum family gives unbounded reduction against
   the full-proposal estimator, even its best state-only scalar baseline.
   This is a proof object, not a constructed performance benchmark. Strong
   controls include full-proposal scores with optimized baselines, direct
   exact enumeration/conditional expectation, component elimination, ordinary
   compiled evidence inference, and existing exact trajectory methods under
   THEIR own policies. No dominance over all those controls is claimed.
4. **Proof before code.** See work/theory-v1.md: threshold/fallback or top-k
   preimages are Cartesian per-position filters once retained IDs are known.
   One filtered partition divided by the base partition is the action mass.
   Two outside passes give the difference of token marginals. Conditional
   score/variance and the quantitative connected-family separation are written.
   These statements concern original words, not derivation multiplicity.
5. **Validation.** First independent rational full action laws, scores, aliases,
   fixed IDs, threshold equality, stable ties, impossible actions and EOT/PAD.
   Exhaustive enumeration is a correctness oracle. No timing/training campaign
   before actual numerical feasibility, stronger controls and a frozen
   complete-cost protocol. A small passing oracle is not sufficient novelty.
6. **Complete cost.** Original head and backward, tokenizer/grammar compilation,
   base plus filtered inside/outside, confidence arrays, all latent proposals,
   updates, memory, rational bit costs and output count. Same neural Jacobian
   may dominate both estimators, making extra inference affordable, but this
   has NOT been measured. No extra neural pass is mathematically necessary
   to score one cached transition; changed policy weights still require their
   actual new model outputs. Storing a stale head is not on-policy training.
7. **Objections.** Classical evidence inference may subsume the whole method;
   useful variance may be small; complete neural cost or stronger analytic
   controls may erase the effect. Deterministic confidence rules have moving
   decision boundaries: the gradient theorem holds ONLY in locally stable
   comparison cells. It is not a globally smooth policy or a license to ignore
   support changes in PPO. Native floating RNG law is NOT automatically the
   ideal grammar-conditioned product. GPU top-k ties are not assumed stable.
8. **Article gap.** Distinct originality, real native numerical-law scope,
   significant cost-times-variance improvement on external states, actual
   parameter updates/useful results, competent training controls and independent
   confirmation remain open. No human review, publication, semantic gain or
   achieved user goal is asserted. Only the minimal independent oracle is
   currently justified, not a large training implementation.

Primary reading scope/hashes and previously rejected naive training directions:
[work/primary-audit-v1.md](work/primary-audit-v1.md). The frozen maintained
decoder, old attempts and article are unchanged.

## First independent reference, after the written freeze

Proof/contract producer238a356 precedes reference code. Six rational oracles
PASS0.980s:108 complete laws,1372 observed actions,15092 coordinate scores,
full2x2 covariance identities, original aliases/fixed IDs/JSON EOT PAD*,
impossible actions and four connected checksum sizes including the optimized
full-score baseline. A separate exact counterexample has true gradient-21/100
where retained-token-only scoring gives zero; its purported action masses sum
to17/10. The full-proposal estimator remains CORRECT, just potentially noisier.

The moving-boundary counterexample passes too: no global differentiability
claim is rescued by correct finite probabilities. Full maintained suite211
tests PASS72.391s; make check and focused Ruff PASS. Evidence is in
work/evidence/rational-v1. No new neural head, parameter update or competitive
timing. This is a minimal law oracle, not an implemented training decoder or a
new protagonist. Classical evidence inference supplies the same reduction;
specific novelty and a useful complete-cost consequence remain unresolved.

## V2 — a separate smooth policy contract, still before code

[work/smooth-policy-v2.md](work/smooth-policy-v2.md) writes a DIFFERENT policy:
joint grammatical proposal and token-dependent Bernoulli release, conditioned
on a nonempty mask. A two-state positive OR calculation avoids subtracting
near-equal partitions. The observed-action partition has fixed support and
smooth scores; this does not preserve V1/Mosaic's law or the original word
posterior after conditioning. Restarting only bits for a fixed word is an
explicitly different, inadmissible shortcut for this target.

All eight criteria are reassessed in that note. dUltra and Learning Unmasking
Policies already use Bernoulli planners and are mandatory primary antecedents;
the position-only variant is a cheaper competent control. Classical CRF/evidence
inference may subsume the entire construction. Only the minimal rational joint/
action-law oracle is justified; no new model, update, timing or sufficient
originality is asserted. V1's result and its moving-boundary counterexample
remain unchanged in their archive.

V2 now has five independent rational oracles after freeze651b8dd:8 joint laws,
256 actions4096 score coordinates,31 changed FAKE-head states52 observed paths88
auxiliary paths, full covariance identity, true confidence chain rule, tiny
exit mass and wrong bit-only retry. Combined11 oracles PASS1.224s; full216
tests PASS73.155s; make check/Ruff PASS. No neural head/update/timing. The new
primary addendum recognizes MD4's existing token-dependent schedules as well
as Bernoulli planners; token dependence cannot itself be claimed as novel.
Only a written cost/consumer refinement precedes further implementation.

## V3 — written auxiliary-anchor refinement before code

[work/anchor-policy-v3.md](work/anchor-policy-v3.md) selects an anchor from the
current state independently of the complete grammatical proposal, forces that
position and uses token-dependent Bernoulli gates elsewhere. It explicitly
preserves the CURRENT proposal marginal and guarantees progress, while changing
the exposed policy. Summing the hidden anchor is a retained-only scalar times
one ordinary filtered partition. The note gives all three score adjoints,
confidence chain rule and expected release count; standard mixture/evidence/
conditional-mean principles are credited. Fixed-anchor and position-only
reductions must receive cheaper correct implementations. All eight criteria
are reassessed. No V3 code, new head, update, timing, specific novelty or useful
neural consequence is established by this written foundation.
