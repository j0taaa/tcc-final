# V1 primary reduction and strong-control obligation

Actually read McAllester/Collins/Pereira, *Case-Factor Diagrams for Structured
Probabilistic Modeling*, UAI2004, original arXiv reprint1207.4135:
<https://arxiv.org/pdf/1207.4135>. Scope: introduction, definitions/linear
Boolean model, PCFG encoding in section4, CFD semantics and sections6--8's
size/inside/Viterbi/inside-outside constructions. Not the entire appendix.

The original already explicitly contrasts exponential standard-MRF inference
on a natural PCFG encoding with polynomial grammar parsing. CFDs and recursive
conditioning exploit context-specific independence. Its polynomial parsing
circuit and bounded-treewidth-model representation are established; inferential
operations are linear in the compiled diagram. This defeats the broad claim
that adding a grammar circuit to factor inference is a new principle.

Important scope: that PCFG example distributes over PARSE TREES of a supplied
word. Our original-token completion law needs unique-event derivations and a
token lattice. Do not turn its statement into a theorem about ambiguous-word
counting; A46 and the maintained LL(1) admission still apply. The difference
does not resurrect generic circuit/representation novelty.

Re-read FactorDLM arXiv:2609.32900 sections3.1--3.3 and related-work paragraph
"Exact inference over learned scores" in the original HTML:
<https://arxiv.org/html/2609.32900>. It explicitly credits variable elimination,
treewidth and knowledge compilation, uses finite-domain auxiliary encodings
and compares direct/sequential constraints. Circuits beyond declared width
are named as extensions. Do not describe it as denying all compact parsing.

A tempting separation is a selector choosing among a constant number of
noncrossing equality patterns. The union of gated factor scopes can be wide,
although each selected pattern is cheap. A competent control conditions on
the selector, simplifies inactive factors, computes each branch partition and
mixes using their actual masses. If there are k branches, it pays k branch
queries, not an exponential dense table on the unsimplified union. Thus this
example cannot establish superiority over competent alternatives. No formal
encoding-independent lower bound has been proved here.

AAAI2024's *Encoding Constraints as Binary Constraint Networks Satisfying BTP*
and Quimper/Walsh's2011 grammar/s-DNNF work are additional primary leads.
Their searchable excerpts, not the full proofs, were obtained in this session;
do not claim that all their model-counting hypotheses were reviewed.

**Decision:** close the generic grammar-versus-wide-factor example before
code. No benchmark, neural head, graph compiler or main-paper claim. A useful
hybrid syntax/relational operation would still need its own nontrivial theorem
and comparison against the actual compact/context-specific predecessor.
