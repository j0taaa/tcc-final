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

After freeze da3bd39, four V3 oracles PASS:8 complete triple laws,256 actions,
4864 score coordinates, both levels of collapse, fixed-anchor/position-only
analytic controls, original proposal marginals and confidence chain rule.
Five changed FAKE-head states yield12 observed paths from24 full paths, with
the exact return-gradient covariance identity. Combined15 oracles PASS1.374s;
full220 tests PASS73.333s; make check/focused Ruff PASS. No real new neural
head, parameter update, GPU timing or confirmed novelty/use. Evidence:
work/evidence/anchor-v3. The next consumer must explicitly handle model output
IDs beyond the tokenizer-defined domain; no hidden vocabulary truncation.

## V4 — bounded consumer/resource contract, before implementation and heads

[work/consumer-resource-v4.md](work/consumer-resource-v4.md) and its independent
question-only input copy fix8 KNOWN development GSM8K questions, the pinned
Tiny-A2D checkpoint,32 response slots, one gate config and at most9 real forwards
including warmup. No labels/updates/timing comparison; six correct completed
cases only permit consideration of a separate cost/variance protocol. ALL
original151936 IDs, including tokenizer-empty padded IDs if their decoding is
verified, must be retained; explicit numeric JSON EOT PAD semantics, independent
checks, raw data and resource refusals are fixed. The regular schema is not
evidence of recursive parsing novelty. Runner/source still need freezing before
any real head. Specific originality and useful complete-cost benefit remain OPEN.

V4's initial foundation now passes18 focused tests1.532s, including22608
independently parsed small words/class sums. The official tokenizer audit checks
ALL151936 IDs and4096 triples with zero errors; all266 undefined IDs remain
empty original emissions. Whole-V compilation has38 classes/22 states/92 valid
state-class arcs (2944 for32 slots), preserving every ID. Initial48 NumPy/Torch
CPU/CUDA score records match rational oracles, max log error1.78e-15. These are
correctness/resource prerequisites, not neural heads, timings or benefits.
See work/resource-foundation-v4.md and work/evidence/consumer-foundation-v4-initial.
The pretrained resource runner is still pending; no weight evaluation/update.

The final pre-head implementation is now frozen with19 focused oracles and
224 maintained tests PASS74.209s; make check/focused Ruff pass. Three synthetic
full-V32-slot actions fit421728768 bytes; refined48 toy CPU/GPU records include
discarded proposals. Five RANDOM-model calls verify bidirectionality, padding,
head cropping and explicit BF16 local loading. All are prerequisites, with ZERO
pretrained calls. See work/consumer-preflight-v4.md and the independently
versioned original/final evidence. consumer-protocol-v4.json freezes the actual
resource runner/runtime before its first pretrained call. No complete-cost
variance, quality, training, independent confirmation or novelty is credited.

The bounded real capture AFTER freeze854a733 now completes8/8 cases with9/9
pretrained forwards including warmup,32 independently valid original-ID JSONs,
zero refusal/error and<=422932672 bytes sampler peak. All logits, original
outputs, three scores, provenance and checks are archived; maximum CPU/GPU log
discrepancy3.553e-14. See work/resource-result-v4.md. These are resources and
correctness only; no semantic labels/update or complete-cost variance advantage.

## V5 — Stronger cheap control and actual-return foundation before code

work/two-stage-variance-v5.md reassesses ALL eight criteria. A classical reverse
collapse integrates the anchor in O(n+|B|), without grammar inference; its
anchor score ALREADY equals the fully collapsed method's. It is mandatory,
so anchor-noise wins against the full triple are insufficient. The note also
derives compact class derivatives for repeated planner scores, acknowledging
ordinary expectation-semiring/evidence inference gives the SAME construction.

A bounded two-stage consumer is frozen in writing before its code/heads:
all8 known initial states,16pilot+64eval draws each, at most641 new forwards,
fresh next-canvas model/grammar completion, ALL raw heads/IDs, no update.
Labels only after capture; strong scalar/zero/RLOO controls and a necessary
20% variance gate precede any complete-cost or training campaign. PUMBA and
x-Prediction Flow are additional primary alternatives within recorded scopes.
No V5 implementation, new head, variance win, sufficient originality or
fulfilled goal is claimed. Minimal reverse/compact oracles are next.

V5 implementation prerequisites now pass229 maintained tests74.834s, make
check/Ruff, including compact/reverse rational means, clamped-ID continuation,
unbounded numeric lexemes and exact RLOO group laws. Two RANDOM BF16 forwards
verify indexed cropping literally; V5 pretrained counter is stillZERO.
See work/two-stage-preflight-v5.md and consumer-protocol-v5.json. The actual
known-development capture is next; no variance/timing/learning benefit yet.

V5 is now COMPLETE and NEGATIVE after e01739d:640/640 valid original-ID
trajectories,629 new forwards including warmup, zero error/refusal; ALL640
terminal rewards are zero after the closed capture, independently confirmed
by Decimal. No ratios or variance wins are credited. Variation0/8 fails the
predeclared gate, so timing/training/independent branches are NOT triggered.
All heads, scores, labels and costs remain preserved. See work/two-stage-result-v5.md.
Padding/termination is only a new diagnostic hypothesis, not a changed gate
or a fulfilled scientific goal. No new implementation follows without its
separate written foundation and eight criteria.

## V6 — Separate stopping-law diagnostic written before code

work/stopping-contract-v6.md reassesses all eight criteria and distinguishes
the legitimate old full-word JSON EOT PAD* law from observing a response only
through first EOT, as the native upstream trimming helper does. Elementary
mixture/tilting arguments give a length-TV identity and stochastic length bias;
absorbing-state marginalization is classical and no novelty is claimed.
Only small independent oracles and then a source-frozen ALL8 OLD-head audit
are justified, without new forwards/labels/samples/updates. V5 remains closed
negative. No stopped iterative decoder or semantic gain is established.

V6's two rational stopping oracles pass, including fixed original suffix IDs,
zero PAD mass, full prefix-TV identity and stochastic ordering. Full231 tests
PASS74.457s and make check/Ruff PASS. The OLD-head audit source/protocol now
freeze before its mass/length computations; no new model call/sample/label.

The source-frozen V6 audit completes8/8 old heads: length-TV0.869119--0.999971
and extra PAD mean length6.475331--18.191402 original tokens, with all8 interest
conditions passing. Independent/archive partition checks agree within1.422e-13
in log space. ZERO new forward/sample/label/update. See work/stopping-result-v6.md.
This motivates a new stopped-consumer design only; it does not establish
semantic cause/gain, a new compiler/theory, training or fulfilled goal.

## V7 — Prefix-aware anchor contract before code

work/prefix-anchor-v7.md reassesses all eight criteria. Only active positions
within a proposed stopped prefix can be released; every fixed original ID
must stay in the returned prefix. The anchor's latent-length normalizer is
a terminal potential, with written action/occupancy/anchor-score/progress
identities. Classical weighted inference/conditional means are credited.
Cheap anchor-only, length-only, class-conditional and combined controls are
mandatory. Only minimal rational oracles are justified next, not new heads,
training or a revival of V5. Own originality/use and the goal remain OPEN.
work/prefix-head-chain-v7.md writes the additional original-softmax row-sum
term needed when prior/posterior prefix occupancies differ, before code.
Independent rational dual-number checks must include it; no detached shortcut.

After1ecf413/e686287, five V7 oracles PASS5.089s: five joint laws2701 triples,
484 actions31790 score coordinates; variable occupancy, exact dual head/gate/
anchor chain, old-policy fixed-stop equality and stronger partial controls.
The proof object has strict alpha/anchor trace reduction even versus the
combined control, with no real-head/gate-table/application claim. Thirty-five
FAKE-head states preserve IDs/path means. Full236 PASS84.581s, make check/Ruff
PASS. See work/prefix-result-v7.md. No new head, native sampler/update or useful
novelty is established; a written stopped-consumer resource design is next.
