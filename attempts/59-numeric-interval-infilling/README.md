# A59 — Complete numeric intervals for bounded structured infilling

2026-10-16 local date. Written BEFORE a prototype, new model inputs or timings.
A58's kernel/resource family stays CLOSED negative. This direction changes the
operation to semantic numeric constraints, not another head implementation.

1. **Real use.** Fill missing token regions in an existing JSON numeric tool
   argument/configuration while retaining every fixed token. The accepted
   exact decimal value must lie in a declared interval. Scientific notation,
   arbitrary fraction precision and exponent leading zeros are legal JSON.
   For example, fixed `1.5e-` can be completed into [0.01,0.02) by `2`.
   Rewriting the existing prefix is unavailable to an infilling consumer.
   A dLLM already supports fixed/masked regions; the proposed compiler would
   supply a constraint representation to an existing mean-field projector.
   No deployed consumer/model benefit is claimed yet. An external corpus and
   concrete integration still need to establish practical relevance.
2. **Difference.** Current pinned llguidance and XGrammar numeric-range
   routines emit restricted numeral forms. The candidate is a byte-budgeted,
   complete scientific-notation interval compiler with an unambiguous finite
   automaton and an explicit size bound, preserving ORIGINAL token IDs.
   Counting, exact decimal comparison, suffix DAGs, automata, semantic guards
   and weighted inference are CLASSICAL. Own priority and a substantial useful
   systems distinction are OPEN. Missing functionality alone is not a claim
   of a new general parsing theorem or sufficient publication novelty.
3. **Why choose it.** Capability: complete infilling even when fixed bytes
   contain scientific notation or more fractional digits than a restricted
   range frontend admits. For a fixed positive finite interval, the written
   construction has O(L) states/edges and is sound globally, complete for
   every numeral of at most L bytes. For [1,2), a matching Omega(L) bound holds
   even for NFAs. Compare complete numeric register/digit-DP compilers,
   length-bounded regex construction/minimization, exact parsing plus search,
   symbolic/SMT methods and factor-based encodings. Out-of-box restricted
   frontends are capability diagnostics, NOT sufficient performance controls.
4. **Proof first.** work/theory-v1.md proves the unbounded [1,2) numeral
   language is not context-free, then gives the POSITIVE bounded compiler,
   unambiguity, size, bounded-completeness and original-ID inference corollary.
   The closure/fooling-set arguments and sum-product corollary are standard
   tools, not claimed inventions. A proof of a compiler's correctness does
   not establish originality or useful full-generation speed.
5. **Validation.** Only a minimal independent exact oracle initially: JSON
   syntax plus rational numeric evaluation, all small strings/token tapes,
   aliases/fixed holes and word-path multiplicity. No benchmark selecting
   favorable prefixes or real-model campaign before the operation, strongest
   complete controls and a separate resource/input protocol are frozen.
6. **Full cost.** L is a conservative BYTE bound from the token budget and
   maximum admitted token byte length; fixed context bytes count. Account for
   bounds' bit length, state/edge construction, epsilon closure, tokenizer
   lifting, dense/sparse storage, mass/marginals/sampling, model forwards,
   preparation and output. Linear byte-level graph size is NOT linear neural
   inference time or a promise that token-lifted tables remain sparse.
   Exact decimal semantics is separate from binary64-rounded validation.
7. **Fatal objections.** An existing complete numeric compiler may already
   give the same representation. Generic semantic register automata/digit DP
   might make the construction a routine specialization. Token lifting or
   epsilon closure can destroy the apparent resource advantage. A real input
   corpus may not need excluded forms. Canonical regeneration is a strong
   control when fixed-prefix preservation is not required. A match by a
   competent classical compact encoding must be acknowledged, not excluded.
8. **Article gap.** Specific antecedents, an audited own difference, exact
   independent validation, real external numeric-infilling data and dLLM
   integration with complete controls/costs. The written capability/size
   result is a research candidate; no model quality, trained model, sufficient
   novelty, publication acceptance or fulfilled user goal is established.

Primary source pins and actual reading scope are in work/primary-reading-v1.md.
The first implementation, if justified by this audit, is deliberately a small
compiler/oracle for [1,2), not an extensive new decoder or GPU optimization.
