# A47 — Exact logit-weighted forest sampling: bit complexity before code

2026-10-12. Written before a prototype or observations. A44's failed neural
application is closed;45 is an open conjecture;46's generic proposals reduce
to known methods. The maintained rational API and article remain unchanged.

1. **Use:** sample ORIGINAL tokens from a frozen dLLM softmax conditioned on
   a checked unambiguous CFG, using the finite model logits as exact rational
   inputs. Preserve aliases/bytes/slots. Ideal exp(logit) probabilities are
   generally irrational; the operation differs explicitly from the maintained
   rationalized probability posterior and from native finite-PRNG EPIC.
2. **Difference:** exact-real/interval random sampling and Boltzmann grammar
   samplers are OLD. Investigate ONLY a complete expected-bit/work bound for
   finite positive forest circuits, independent of tiny valid mass and full
   enumeration of completions. It may be a direct known specialization; audit
   that first. Combining established tools does not establish novelty.
3. **Choice:** a genuine ideal-logit sampling guarantee without silently
   underflowing/pruning positive original events, with finite expected work.
   Competent controls include log-domain floating inference, arbitrary-
   precision fixed tolerance, certified interval Boltzmann/recursive sampling,
   exact rationalized inference (different declared law), and exact rejection.
   No universal physical speed or EPIC quality advantage is implied.
4. **Without code:** state the precise positive homogeneous forest, degree,
   binary decision expansion, relative enclosure oracle, random-bit model and
   expected precision/work. Include normalization cancellation, zero structural
   mass, original-token reconstruction and bit-cost of exp/range reduction.
   Exact-real termination does NOT itself give a useful expected cost.
5. **Experiments:** none until the theoretical distinction survives primary
   reduction. Minimal rational/exp interval oracles can refute an argument;
   no invented underflow case is a practical neural benchmark. A later real
   study must use all predeclared archived inputs and strong log-domain control.
6. **Cost:** tokenizer/grammar/forest preparation, all logit enclosures, circuit
   operations, refinement/reuse, exp computation, mantissa AND exponent bits,
   RNG/reconstruction and model forwards. Any reciprocal valid-mass factor or
   exponential logit-range cost must be exposed rather than hidden in an oracle.
7. **Objection:** Boltzmann exact interval arithmetic already handles recursive
   disjoint union/product; the precision bound may follow directly from known
   computable-distribution sampling. Ordinary53-bit float errors are usually
   tiny; a purer guarantee alone may have little practical advantage. Unknown
   grammar ambiguity, model evaluation and finite PRNGs are not verified.
8. **Publication:** need a distinct theorem/cost improvement against the actual
   interval-sampling predecessor and a useful operation, not just replacing
   rational arithmetic with a library. No novelty, acceptance, benchmarking
   win or implemented ideal-softmax sampler is claimed here.

Work is independent. This is a mathematical/prior-art investigation before
adding dependencies or rewriting the sampler.
