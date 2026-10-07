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
