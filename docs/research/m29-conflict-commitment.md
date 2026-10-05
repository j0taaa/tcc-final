# M29 — Certified conflict-guided budgeted commitment

## Scientific and behavioral contract

The objective is exactly M26's `OPT_B`: jointly choose a represented grammar-
valid full token completion and at most B free physical positions to commit,
maximizing the sum of all positive duplicate proposal weights at those positions.
Weights are exact binary rationals. The original input, bytes, fixed slots,
EOS/PAD, support scope and all distinct solver statuses remain mandatory.

The new solver learns forbidden sets of **position/token choices**, not proposal
IDs or emitted bytes. A conflict is accepted only with an independently checked
original-input infeasibility proof. A subset of a feasible batch is feasible;
therefore a forbidden set forbids all its supersets. The master optimizes the
position budget and represented positive rewards while excluding learned
conflicts. Its first CFG-feasible optimum is the true budgeted optimum.

Each master proof partitions allowed batches by excluding one member of a
violated conflict. Every feasible batch is covered by at least one child.
Leaves use the sum of the B best allowed per-position rewards as an upper bound.
An empty certified conflict proves that no completion exists at all. The
independent checker validates this cover and upper bounds without importing or
calling the new optimizer. It also validates the final original token witness.

Conflicts can be reused only if the new feasible completion set is contained in
the certified source set: identical grammar, token meanings and EOS/PAD; same
slot count; support rows only shrink; old fixed positions remain fixed. Changing
proposal weights or budget does not invalidate conflicts. Expanding support,
remasking, changing grammar or token meanings invalidates this reuse rule.

## Primary antecedents and novelty boundary

The general strategy is established implicit hitting-set/constraint
optimization, not a new invention:

- Davies and Bacchus (2011), *Solving MAXSAT by Solving a Sequence of Simpler SAT
  Instances*, DOI 10.1007/978-3-642-23786-7_19.
- Saikko, Berg and Järvisalo (2016), *LMHS: A SAT-IP Hybrid MaxSAT Solver*:
  https://www.cs.helsinki.fi/u/mjarvisa/papers/saikko-berg-jarvisalo.sat16.pdf
- Demirović et al. (2024), certifying dynamic programming:
  https://drops.dagstuhl.de/entities/document/10.4230/LIPIcs.CP.2024.9
- EPIC's exact check establishes extendibility, with confidence-ordered
  heuristic subset selection; it does not solve this joint budget objective:
  https://arxiv.org/html/2606.00722v1#S4.SS3
- FactorDLM's exact constrained MAP and subsequent confidence commitment solve
  a different objective: https://arxiv.org/html/2609.32900v1#S3.SS2

The incremental contribution under evaluation is a certified, tokenizer-aware
specialization for joint commitment, avoiding a resource-indexed weighted chart
when few conflicts suffice, and supporting mathematically safe conflict reuse
across changed logits and retained-support states. This audit does not establish
worldwide priority. A maximum is never presented as a semantic-accuracy theorem.

## Frozen experiment protocol

Reuse **all 72 inputs** (36 source states, two reward profiles) of the existing
M28 frozen configuration, with its original hashes and budgets 0, 1 and 2.
Compare the same exact rational objective, slots, grammar and support using:

1. M26 resource DP, solving the common frontier once;
2. classical descending-score exhaustive proposal-subset enumeration;
3. certified conflict-guided optimization, cold cache;
4. the same conflict engine with its internally validated cache retained across
   budgets and source states when the containment rule actually holds.

Run three repetitions for the new engines and one fresh DP frontier per input.
Historical M28 timing is supplementary, not the primary fresh time comparison.
The score checks use M28's independently verified archived rational certificates.
Timing includes required internal proof construction/checking; independent
external archive verification is also reported separately. No model forward is
executed and no GPU speedup is inferred. Source order, cohorts and failures stay
visible. All scripts emit source/config hashes, git commit, revisions, hardware,
statuses and exact rational scores. Timeouts remain unresolved outcomes.

The ranked-subset comparator considers every represented positive position/token
batch of cardinality at most B, in decreasing rational reward, and queries the
same finite CFG oracle. Its first feasible batch is exact. It is deliberately a
classical exact comparator, rather than a weaker confidence heuristic.

## Theorems

### Exact master and independently checkable cover

Aggregate all positive duplicate rewards for each represented free-position
token choice. A master batch contains at most B choices and at most one choice
per position. For a set E of excluded choices, let U(E) be the sum of the B
largest allowed per-position maxima. Every batch avoiding E has reward at most
U(E), and selecting those maxima attains U(E) in the relaxed problem.

For each independently CFG-infeasible conflict C, every feasible batch omits at
least one member of C. Therefore the subproblems E union {c}, for every c in C,
cover all feasible batches in the parent subproblem. Their maximum upper bound
is a valid upper bound for the parent. An empty conflict has no children and
proves there is no feasible completion. These statements follow directly by
set containment and addition of non-negative rewards; they do not assume
pairwise conflicts, unambiguous grammars or a complete set of learned conflicts.

The master recursively branches whenever its relaxed best batch contains a
known conflict, and otherwise returns the relaxed best batch. Induction on the
number of excluded choices proves that it computes the exact optimum of its
current relaxation. At each branch a currently allowed choice is removed;
recursion terminates. Every terminal leaf records U(E); every branch records
the member-complete cover and maximum of child bounds. An independent checker
can verify these local inequalities without performing the master search.

### Exactness and termination of conflict-guided commitment

All genuinely feasible batches obey every independently certified conflict,
so the master optimum upper-bounds `OPT_B`. When its batch has a finite-slot
CFG witness, independently recomputing the original reward gives a matching
lower bound. Consequently the returned batch attains `OPT_B`. If the master
has no surviving batch, the same certified cover proves infeasibility.

When the current master batch is CFG-infeasible, deletion tests produce an
inclusion-minimal infeasible subset C. Each deletion changes the set only after
an exact `INFEASIBLE_ON_SUPPORT` answer. The existing zero-budget resource
checker independently certifies C on the original restricted support. The new
conflict is contained in the current batch, which avoided all known conflicts;
therefore it was not already known. There are finitely many choice subsets, so
each successful iteration removes a new master candidate and termination is
finite. A deadline or unknown oracle status proves no new conflict or optimum.

### Conflict-parameter bound

At budget B, every newly learned core has size at most B. Along a master branch,
excluding one member permanently discharges its selected core, so with h
applicable cores depth is at most h and branching factor at most B. For B >= 2,
the number of nodes is at most sum(d=0..h) B^d; B=1 gives h+1; B=0 has one node.
Each node scans/sorts m represented rewarded choices, using O(m log m) work.
This is an upper bound in conflict structure, not an improvement of the CFG
parser's worst-case complexity. Many conflicts can make this method expensive.

Learning H new conflicts uses at most H failed main queries, B*H deletion
queries, and one final successful main query: at most (B+1)*H+1 oracle calls.
If an empty core proves infeasibility, that last query is unnecessary.
Certificate construction/checking has its own cost and is included in measured
solver time. The bound is on calls, not wall time or certificate bytes.

### Safe transport and amortized use

Let F' be the new feasible completion set and F the source set. The implemented
retained-support check implies F' subset F: each new token is an old represented
token, fixed tokens remain fixed, and identical grammar/bytes/EOS/PAD accept the
same emitted strings. Thus a choice set with no witness in F has no witness in
F'. Already fixed matching conflict members can be discharged; a contradictory
member makes that conflict irrelevant. This discharging preserves the same
forbidden conjunction. Proposal scores and the budget occur nowhere in this
containment argument, so changing logits does not invalidate retained conflicts.

For T completed calls with budgets at most Bmax along a valid retained-support
sequence, if H distinct new conflicts are learned, total feasibility queries
are at most T+(Bmax+1)*H. A learned conflict cannot be learned again: any selected
superset would already violate its retained/discharged master constraint.
No amortized saving is asserted when support expands or token semantics change.

### A strict reuse separation, independent of benchmark frequency

Take two slots, tokens a/b, and the fixed regular language {ab,ba}. Give choices
(0,a) and (1,a) higher reward than (1,b), and budget two. Every cold conflict
solve first queries the infeasible aa pair, performs two deletion tests and
then queries a feasible master optimum: four calls. Once the aa conflict is
certified, every later solve with these priorities uses one main feasibility
query, including when the positive weights change. Over T solves this gives
4T calls cold and T+3 with retained conflict learning. This exact infinite
family proves a reusable computation saving under the stated oracle policy;
it estimates neither the frequency in real logits nor semantic quality.

Implementation: `conflict_certificate.py` checks the original input, conflict
proofs and cover; `conflict_commit.py` implements the master and deletion loop;
`conflict_proof.py` serializes portable proofs. Existing resource parsing and
Rust CFG feasibility remain independent. Exhaustive seeded tests compare all
token/subset choices, resource DP and the conflict result, including token
aliases, duplicate scores, EOS/PAD, split UTF-8 and fixed-position discharging.

## Follow-up: two-sided proof reuse

After the complete conflict-only/ranked runs (before fresh DP timing finished),
a further engineering improvement was specified: retain full feasible token
witnesses as well as infeasible conflicts. `m29_proof_reuse_real_v1.json` freezes
the same complete 72-input cohort and budgets, three repetitions of two-sided
reuse and a witness-only ablation. This is development on the same known inputs,
not a new held-out statistical confirmation. No input, weight or support changes.

A previously valid full witness can survive support expansion, provided its
tokens remain allowed, its fixed positions agree and it passes original-input
grammar/byte/EOS validation. In contrast, an infeasible conflict is retained
only under the contraction rule. These two transport directions are asymmetric.
If this witness realizes the current master optimum, the master certificate
and checked token witness again sandwich the true optimum. **Zero additional
CFG-oracle queries** are needed; the independent original-input checker still
runs. `proof_reuse.py` implements this mechanism with private instance caches.

In the fixed two-slot family above, retaining both the learned aa conflict and
the feasible ab witness requires four oracle calls in the first solve and zero
in every later score-scaled solve: total four rather than 4T. An unchanged
witness does not imply unchanged objective: the master and exact reward are
recomputed from every new input. The witness-only ablation cannot bypass the
infeasible top aa pair and keeps four calls per solve. Tests prohibit any hidden
oracle call in retained exact returns and exercise expansion and grammar/fixed
slot changes. This proves a computation saving for a declared infinite family;
real occurrence and wall time are measured separately on the frozen cohort.

## Execution interruption and completion protocol

After the steered user turn, the original worker no longer existed. The resource
DP file contains 68 complete JSON records and a zero-filled suffix, with one
unreferenced proof. The cause of the zero suffix was not established. Preserve
all original bytes separately. `complete_conflict_campaign.py` requires exactly
parseable completed records before an all-zero suffix and completes only the four
missing independent DP inputs. It records the new producing commit/hardware; no
previous result, including a timeout, may be rerun or replaced. Fast-method rows
and their proofs are copied byte for byte. The complete archive contains both
producing provenance records, and the interrupted source is retained for audit.
These measurements remain engineering evidence, secondary to the mathematical
result and the subsequent broader scientific investigation requested by the user.

The first completion gate additionally found two referenced resource proofs
with zero bytes in the interrupted source, despite complete result rows. The
next archive regenerates only those missing certificates, requires exact
status/objective equality with the retained rows, and records the recovery
commit and filenames. Recovery is excluded from timing statistics. Originals
and failed completion bytes remain untouched; no row/outcome is replaced.
