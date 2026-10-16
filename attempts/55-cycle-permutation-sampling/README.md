# A55 — Transient-cycle proposals for weighted permutations

2026-10-16. Written before code, new matrix queries, samples or timings.
A52/A53/A54's negative applications remain closed. This is a separate
candidate, not a new CFG parser or a change to the native EPIC law.

1. **Use.** Sample a complete one-to-one assignment with probability
   proportional to a supplied nonnegative matrix's assignment weight. A
   dLLM reranker supplies one identifier distribution per rank (DiffuRank
   §4.3); data-association particle filters also consume this operation
   (AdaPart §6.3). For a fixed finite identifier set the permutation language
   is regular, hence context-free, but its subset automaton can be exponential.
   This target is a PRODUCT-CONDITIONED permutation, explicitly different
   from DiffuRank's native greedy/assignment decoder. Neither consumer's
   need for random posterior permutations or favorable matrices is presumed.
2. **Difference.** The candidate is an explicit rational-draw implementation
   of a Markov loop-soup rejection envelope, with a checkable rejection-cost
   certificate for diffuse near-permutation matrices. Cycle gases, Poisson
   exclusion, MacMahon/Vere-Jones/Le Jan, Ewens/negative-binomial mixtures,
   Boltzmann sampling and rejection are CLASSICAL. Own sufficient novelty is
   OPEN. In particular, Li–Zheng2022 Theorem1.2 already gives the occupation
   law; Armendáriz–Ferrari–Frevenza2019 §3 already conditions independent
   Poisson SIMPLE cycles on exclusion and constructs a loss network. Merely
   reprinting either law is not a contribution. The operational candidate
   avoids listing all simple cycles using cheap closed-walk proposals.
3. **Choice.** If a detected base assignment yields off-diagonal ratio
   matrix R with maximum row sum r<1 and maximum entry at most a/n, the
   written proposal has acceptance at least 1-a²r²/[n(1-r)²] when positive.
   It can have linear expected draw work after matrix preparation while
   ordinary independent-row rejection has exponentially small acceptance.
   This comparison is ONLY against that control. Strong mandatory controls
   include SCC factorization, symmetry/low-rank shortcuts where applicable,
   exact subset DP, Huber–Law, AdaPart/DeepAR/new nesting bounds, and
   cycle-gas/perfect-simulation methods with their actual feasible oracles.
   No superiority over all of them or full dLLM generation is yet established.
4. **Proof first.** work/theory-v1.md specifies the target, dominating soup,
   rational negative-binomial/Ewens realization, acceptance law, return-count
   certificate, a connected diffuse family and a bad disconnected family.
   Bit costs, unlimited versus capped sampling and postselection are explicit.
   It is an independently written derivation, not Lean or human peer review.
5. **First validation.** Only minimal rational finite oracles: permanent law,
   soup/occupation coefficients, Ewens mixture, matrix invariance and the
   rejection certificate/counterexamples. No arbitrary neural campaign from
   passing correctness. Any real-matrix feasibility/timing stage needs a
   separate predeclared protocol, immutable source/input hashes and ALL
   competent applicable controls. No case selection by favorable timing.
6. **Whole cost.** Matrix acquisition/model head, original identifiers,
   base matching, ratio conversion, row categorical preparation, all geometric
   draws/Ewens construction/walks, rejected soups, bit arithmetic and output.
   A cheap entry/row-sum certificate avoids an inverse; an optional exact
   Green-diagonal certificate costs a matrix inverse. SCC decomposition is
   shared with controls. A supplied posterior matrix is not a free neural
   forward. Exact rational weights are not ideal softmax or native float RNG.
7. **Objections.** r>=1 refuses this implementation; early dLLM heads may
   all fail. Concentrated local ambiguities cause exponentially many global
   retries; split actual SCCs first. Loss-network/cycle samplers may already
   obtain equal or better costs. Ranking's useful output may be a deterministic
   assignment, already cheaply solved by Hungarian. A synthetic asymptotic
   family alone cannot justify a new real application. Simple composition of
   known methods may leave insufficient originality even if correct and fast.
8. **Article gap.** Audit the distinct algorithm/cost claim against original
   loop-soup/Boltzmann/perfect-simulation sources; validate a real consumer
   needing THIS law; prove or measure a substantial benefit against all
   applicable strong controls including preparation. Independent evidence is
   needed before promotion. No new neural work, useful measured benefit,
   priority, publication/admission or achieved goal is claimed at this freeze.
