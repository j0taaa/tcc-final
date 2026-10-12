# A48 — Grammar versus factor representation: eliminate weak separations

2026-10-12. A primary/math audit before implementation. No new solver or data.

1. **Use:** exact original-token sampling/marginals for a frozen dLLM head
   constrained by recursive JSON/DSL syntax. Compare representations of the
   SAME law, not syntax checking against full probabilistic inference.
2. **Difference:** polynomial grammar circuits versus wide ordinary factor
   elimination are OLD. A candidate would need a specific new representation
   bound or useful hybrid operation, beyond citing high width of a natural
   encoding. Context-specific independence must be allowed to the competitor.
3. **Choice:** a proven useful cost/capacity improvement against FactorDLM and
   equally competent circuits/conditioning. Generic circuit reuse and inside/
   outside are not exclusive advantages. No improvement is established here.
4. **Without code:** formalize both representations including auxiliaries,
   domains, selection variables, bit costs and all preparations. A lower bound
   on ONE graph says nothing about every encoding of the same relation.
5. **Experiment:** none before a surviving distinction. Constructed relations
   serve as proof objects; do not benchmark a deliberately poor static encoding
   against a grammar that benefits from case-specific simplification.
6. **Cost:** compilation, circuit sizes/widths, current weights, normalization,
   all queries, reconstruction, tokenization and model calls. A large selector
   enumeration or unrolled parse-tree universe must not be hidden.
7. **Objection:** known case-factor diagrams already unify bounded-treewidth
   graphical models and polynomial grammar parsing. For a constant number of
   gated branches, ordinary conditioning can remove every inactive factor.
8. **Publication:** only an explicit surviving theorem/application would
   justify code. A CFG-versus-bad-MRF example, a renamed d-DNNF or a dLLM label
   does not. No novelty, EPIC advantage or editorial acceptance is claimed.

The independent audit is in work/primary-reduction-v1.md. The generic direction
is closed before implementation; a genuinely different operation needs a new
version/contract. Existing core, baselines, paper and all losses stay intact.
