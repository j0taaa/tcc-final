# Consumer-first reading,2026-10-16

This is reading only, not a new attempt/protocol or authorization to reopen
old campaigns. The scientific goal is still OPEN. No model weights, native
producer, inputs, outputs, labels, timings or candidate parameters were read
or generated in this inspection.

## PepTune: more specific than the earlier A56 introduction-only scope

Primary source: https://arxiv.org/html/2412.17780v2 . Additional actual scope:
§2.2/Table2, §2.5's first receptor example, §4.4's output/invalid-penalty
paragraphs and §4.5 evaluation/docking. This does not claim the full paper or
all underlying code was read.

The unconditional peptide-SMILES generator reports45% validity, assessed by a
peptide-specific filter. The guided MCTS method reports reaching100% validity
after about20 search iterations with its penalty. Its output is a Pareto set,
not a fixed native iid pair. Its validity test includes RDKit plus peptide
bond/side-chain checks. Docking uses Vina after Pareto selection and molecular
conformation preparation; this is a distinct expensive evaluation stage.

Consequences for our decision: do not treat45% as pure CFG syntax failure,
compare only with the unconditional method while omitting MCTS, or substitute
an easier grammar for the peptide filter. Do not infer a source/evaluator cost
ratio from method names. No such ratio was measured here. Docking scores are
computational proxy outputs, not experimental therapeutic efficacy.

An arbitrary pair of child rollouts in the adaptive MCTS is not automatically
a pair of iid calls to a common fixed oracle. A coupling theorem requiring
that contract must identify the complete sufficient state and the unchanged
future kernel, or explicitly operate on independent complete runs. Selecting
a Pareto set is also a different operation from unbiased distributional mean
estimation: we cannot impose a two-label evaluation objective solely to favor
a pool sampler. Predictor-based ranked-set sampling, control variates and
multifidelity evaluation would be mandatory in a genuine expensive-label use.

No molecular implementation, model download or timing/quality campaign is
justified by this reading alone. This closes an unsupported application leap;
it is not a positive contribution or a universal rejection of the domain.
