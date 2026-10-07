# M34 — Exact recursive grammar conditioning at a frozen dLLM step

## Decision and preserved contract (before new measurements)

The M31 exact stack counter defeated the generic probability partitioner on
every completed pair. We keep that result and investigate a different
capability: exact, non-enumerative conditioning under recursive grammars with
multiple kinds of nesting. The existing MWPC strategies remain unchanged.

For the original finite token rows, fixed canvas and supplied rational
probabilities, define `q(y) = product_i q_i(y_i)`. The target is exactly
`q(y) 1[bytes(y) in L(G)] / Z`, when `Z > 0`. This is a frozen mean-field
prediction, not the neural model's complete generative distribution, factual
confidence or an optimal future decoding trajectory. Top-K inputs retain
`exact_on_support`; probabilities are never renormalized at the input boundary.
The first implementation supports ABSENT EOS and nonempty compositional byte
emissions. Other control semantics must be refused, not approximated.

Unlike max-plus parsing, sum-product parsing counts derivations. An ambiguous
grammar can therefore change the target distribution. We require a checked
LL(1) source grammar, including FIRST/FOLLOW conflicts and nullable left
recursion, and verify that its deterministic normalization is the grammar of
the actual input. A caller's assertion that a grammar is unambiguous is not a
certificate. Unsupported grammars, zero probability and work limits are
different outcomes. This restricted grammar class includes standard recursive
structured formats; it does not include every CFG.

## Primary antecedents and specific comparison boundary

- Goodman, *Semiring Parsing* (1999),
  https://aclanthology.org/J99-4004/: algebraic weighted parsing is established.
- Stolcke (1995), https://aclanthology.org/J95-2002/: probabilistic CFG parsing
  and prefix probabilities are established.
- Rivaud and Pachet (2017), https://arxiv.org/abs/1711.10436: exact Markov
  sampling under unambiguous CFGs is explicitly tractable. A position-dependent
  product prediction is an easier case. We do not claim to invent this result.
- DINGO (2025), https://arxiv.org/abs/2505.23061: regular-language constrained
  dLLM MAP is an antecedent.
- EPIC (2026), https://arxiv.org/abs/2606.00722: efficient CFG completion tests
  and parallel heuristic commitment. Its stated limitations include abstract
  mask gaps and finite-budget validity. It does not claim exact sampling from
  the grammar-conditioned frozen prediction.
- Dang and Ermon (2026), https://arxiv.org/abs/2607.07026: exact constrained
  mean-field sampling with automata; its limitations explicitly exclude CFGs.
- FactorDLM (2026), https://arxiv.org/abs/2609.32900: exact factor inference,
  compact relation encodings and alphabet quotienting are antecedents. A CFG
  can also be encoded with auxiliary variables/circuits. We do not prove that
  every factor encoding is inefficient or that this project beats FactorDLM.

The candidate contribution is a small, reusable, ambiguity-checked dLLM
posterior compiler over original byte-emitting tokens, with finite-slot
certificates, exact marginals/samples and no stack enumeration. Its primitives
and underlying CFG tractability are old. The search establishes these
antecedents and a plausible integration gap, not world priority.

## Proof obligations

1. **Token-path bijection.** In each physical slot, share only proper byte
   prefixes. A token closes on a separate last-byte edge carrying its original
   identity and probability. A prefix can both continue and close; byte aliases
   have distinct closing edges. Every complete path chooses exactly one token
   per slot and vice versa. Fixed rows are singleton choices. Put the weight
   on the closure, never on a shared prefix.
2. **No parse-count bias.** LL(1) parsing chooses a unique production from
   lookahead. Nullable/unit elimination, terminal isolation and private
   right-binarization admit a lifting of every normalized tree to a source
   tree; distinct normalized trees lift to distinct source trees. Because the
   source has a unique tree per word, each accepted token path has exactly one
   start-symbol tree. Deduplicating identical intermediate productions cannot
   add a tree. CNF empty acceptance is separate and the nonempty-emission
   finite canvas has no empty complete path.
3. **Exact inside/outside.** Terminal alternatives take their edge weights;
   a binary alternative multiplies its two child masses. Sum alternatives in
   increasing topological span. Induction on span gives the total derivation
   weight, hence `Z` by (1–2). Reverse differentiation gives each closure's
   accepted mass. A path contains one closure per slot, so row marginals sum
   to one whenever `Z > 0`. Zero-weight choices have zero marginal.
4. **Exact sampling.** At each tree node choose an alternative in proportion
   to its inside contribution. Products telescope to path weight divided by
   `Z`; (1–2) identify that path with one original token sequence. Integer
   categorical choices implement rational probabilities without float rounding.
5. **Polynomial arithmetic work.** With `v` DAG vertices, `e` edges, `r`
   binary rules and `h` heads, chart construction has at most `O(r v^3 + e h)`
   alternatives and `O(h v^2)` cells. Evaluation/reweighting and outside passes
   are linear in the compiled forest. These are arithmetic-operation bounds;
   rational bit cost and compiled-forest memory must also be reported. No
   bound claims that cubic parsing is always fast.
6. **Scoped automaton separation.** For properly nested two-type delimiters,
   consider the `2^d` distinct length-`d` opening stacks and each stack's unique
   reversed closing suffix. Matching concatenations are valid; a mismatched
   concatenation is invalid. The resulting fooling set requires at least
   `2^d` states even for an NFA recognizing this finite-length slice. A fixed
   LL(1) grammar recognizes all such slices, and the finite-token DAG/inside
   computation above is polynomial. This separates *explicit sequential state
   encodings*, not all circuits, factor graphs or all specialized algorithms.

The established parsing/automaton facts are credited. Formal Lean coverage
must state precisely which finite implications are mechanized; compiler,
tokenizer, Python and model code are not automatically verified by Lean.

## Predeclared falsification and application protocol

The following are required before a favorable verdict; failed/losing cases
remain in the report.

- New focused offline tests, not restoration of M32's deleted suite. Enumerate
  original token products and use an independent stack/JSON recognizer. Compare
  every accepted mass, per-token marginal and finite sampling branch law using
  rational/integer distributions, including aliases, prefix tokens, fixed
  positions, missing support, reweighting and zero mass. Test rejection of
  ambiguous grammars, mismatched inputs, malformed probabilities, unsupported
  controls and deterministic work limits.
- Include one-type arrays from M31, where the compact exact counter is expected
  to remain cheaper. Replay all 18 archived original-probability cases rather
  than choosing successful cells. Numerical equality is required; runtime
  improvement on this class is not a success criterion.
- For two-type nested structure, compare an independently written reachable
  stack transfer on the exact same token rows/probabilities. Freeze lengths and
  work limits before timings. Uniform/random distributions are openly labeled
  mathematical scaling probes; they are not neural-model predictions or a
  semantic benchmark. Record where sparse stack transfer wins as well as where
  its representation exceeds the declared budget.
- Freeze that mathematical scaling grid now: two-type Dyck delimiters at
  4, 8, 16, 24, 32, 48 and 64 original one-byte token slots; both uniform
  unaries and positive integer weights from seed 20261006, normalized per row.
  Also fix every opening half to a declared alternating stack (a control
  favoring direct stack transfer). The stack controller must prune states whose
  depth exceeds the remaining slots. Both compilers get 200,000 cells and
  1,000,000 transitions/alternatives, and a 30-second job deadline. Include all
  outcomes. Uniform total masses additionally have a Catalan-number oracle.
- External grammar conformance: pin JSONTestSuite before running the sampler.
  Run every declared `y_`/`n_` syntax case of at most 128 bytes, retaining all
  statuses; `i_` cases have intentionally implementation-dependent validity and
  are reported separately, without a correctness assertion. The size bound is
  declared before retrieving/selecting the files; no case is removed by its
  outcome. Use singleton byte-token rows for a grammar-conformance check, not
  a neural-quality or runtime superiority benchmark.
- Use external structured inputs and genuine saved/fresh dLLM predictions for
  application evidence. Constraint declarations must not prescribe a hidden
  target answer. Report support truncation and valid probability explicitly.
  A grammar-valid sample is evidence of the capability, not semantic accuracy.
- Record construction, evaluation, marginal, sample and independent checking
  times separately, immutable config, original input hashes, producing code
  commit, seed, tokenizer/model revisions, hardware and statuses. No cherry
  picking by success, no relabeling a local reimplementation as EPIC/FactorDLM.

Failure of exactness blocks use. If the proposed capability is already
implemented by a close antecedent, or offers no defensible useful distinction,
continue the search. Favorable measurements cannot manufacture novelty. The
representation theorem, not a chosen win rate, is the candidate mathematical
reason to use this approach for recursive grammars.

## Additional direction rejected by primary literature

After the first grid we investigated a polynomial all-different MAP backend
instead of generic factor elimination. DiffuRank already formulates dLLM
permutation generation as Hungarian assignment (2026,
https://arxiv.org/abs/2602.12528, section 4.3.1). Merely adding that algorithm
would not fill a new dLLM capability gap. No assignment backend is added or
described as an invention. FactorDLM's trip-planning difficulty also includes
connectivity and date windows; plain assignment does not solve that problem.

## Fresh model application protocol (fixed before its forwards)

Supplement the archived predictions with all nine combinations of 4, 8 and 16
free original token slots and these fixed surrounding byte strings:

| Input prefix | Input suffix |
| --- | --- |
| `{"params":` | `}` |
| `{"payload":{"items":[` | `]}}` |
| `{"message":"` | `"}` |

Use the same pinned official CPU MDLM/GPT-2 artifacts as M31, its audited CPU
kernel adapter and full-row F64 softmax excluding MASK. Retain top 32 original
tokens per free position, original probabilities normalized over the *entire*
non-mask vocabulary; fixed surrounding tokens have probability one. No extra
answer/grammar tokens are injected. The declared constraint is the complete
recursive JSON syntax grammar, not a prescribed completion. State exactness
on this support and the original discarded mass explicitly. This is a syntax
application demonstration, not a semantic task/quality benchmark. Every
refusal, zero mass and timeout stays in the record. Save full logits locally,
compact original inputs and lineage in the audit archive, and independently
validate every returned JSON sample. Limits remain those of the frozen grid.

## Exact implementation refinement after the initial complete audit

Retain every original result. The rational implementation finishes six fresh
JSON cells and fails three 16-slot cells by explicit budgets/deadline. This
motivates two semantics-preserving refinements, not case replacement.

**Integer unaries.** Choose a common positive denominator `d_i` for each
original row and set `a_i(t)=d_i q_i(t)`, without renormalizing retained mass.
Every complete graph path chooses one closure per row; therefore its integer
weight is exactly `D q(y)`, with the same `D=product_i d_i` for *all* paths.
The integer inside root is `N=D Z`. Outside closure totals divided by `N`
give the same conditional marginals, and integer-weight tree sampling gives
`D q(y)/N=q(y)/Z`. This remains true with aliases, fixed slots, zero unaries
and discarded original mass. The optimization would be invalid for paths that
consume different row sets. The independent stack controller receives the same
integer scaling benefit; comparing against a needlessly rational controller
cannot substantiate a speed claim.

**Binarize before nullable expansion.** Replace each long source body by its
own private right-associated chain before eliminating nullable symbols. Each
source tree has one forced expansion through that chain and each transformed
tree collapses to one source tree. Language and multiplicity are preserved.
Nullable expansion now considers bodies of at most two symbols, avoiding the
exponential optional-subset expansion of a long body. Terminal isolation/unit
elimination remain the established normalizer's operations. Check the original
input against the original normalized source before applying this internal
encoding; do not silently alter the declared constraint. All external syntax
and original-token probability oracles must continue to agree.

The follow-up replays the exact saved inputs of all 28 scaling cells, 18 M31
canvases and nine fresh model cells. No model forward, logits, support, answer
or case is replaced, and previous outcomes remain attributed to their producing
commits. The refinements are classical exact arithmetic/grammar transformations,
not a claim to invent their principles.

## Reuse and rejection follow-up (added after the complete integer audit)

Reweighting may also contract token rows and commit previously free positions,
without changing the grammar, tokenizer, number of physical slots or existing
commitments. Align each new row by original token identity to the compiled row,
assigning exactly zero to excluded choices. Surviving token paths and their
weights are unchanged, so inside/outside/sampling compute the new posterior
without recompilation. Expansion, undoing a commitment or changing grammar
requires a new compilation. Fixed tokens receive probability one according to
the existing conditional-input contract. This is exact restriction of an
arithmetic circuit, an established principle specialized to this interface.

Add a transparent follow-up on **every** saved model input (18 arrays + nine
JSON canvases), not just successes: independently draw from normalized retained
rows with integer categorical choices, recognize bytes without project parsing,
and reject up to 10,000 attempts or 30 seconds with seed 20261006. Let
`Q=product_i sum_t q_i(t)` be represented mass. Acceptance probability is `Z/Q`
and the expected independent trial count is `Q/Z`. Using `1/Z` here would
unfairly charge this control for omitted tokens it never draws. Report first
sample costs including compilation for the new method; low-constraint cases
may favor rejection. This is a local classical control, not an EPIC execution.
Reuse checks commit half the originally free positions from an actual witness,
compare exact mass/marginals to fresh compilation and independently validate the
result. No further model forward or semantic/trajectory guarantee is inferred.
