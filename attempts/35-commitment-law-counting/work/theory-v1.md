# Counting accepted dispatch probabilities, with unambiguous syntax

Written2026-10-11 BEFORE code. Candidate specialization, not verified priority.

## 1. Input and grammar

Let Phi=C_1 OR ... OR C_m be a DNF on n Boolean variables. Remove contradictory
terms. Empty/tautological trivial inputs can be handled separately; otherwise
pad duplicate terms to m>=5. Duplicating a term DOES NOT change its truth set.
Let ell_j be its number of distinct constrained variables. Provide m DISTINCT
witness terminals w_j, even when their terms are duplicates.

Terminals: flag A/B, witness w_1,...,w_m, and bits0/1, all disjoint. A grammar
of length n+2 is:

    S -> A T | B U
    T -> w_j D_(j,1), for every j
    U -> w_j E_1, for every j
    D_(j,k) -> required_bit D_(j,k+1), if C_j fixes bit k
               0 D_(j,k+1) | 1 D_(j,k+1), otherwise
    E_k -> 0 E_(k+1) | 1 E_(k+1)
    D_(j,n+1) -> epsilon; E_(n+1) -> epsilon.

This grammar is LL(1): all alternatives have distinct FIRST terminals; each
nullable final nonterminal has ONE empty production. Every complete word
has a unique flag, witness and bit sequence, hence unique derivation. Its
size is O(mn). It is a regular subclass, so no CFG-recursion lower bound is
claimed. A byte encoding replaces witnesses by a prefix-trie of distinct
names ending in a delimiter; fixed delimiter/JSON scaffolding slots cost
polynomial work. A fixed alphabet does not force an exponential grammar.

A means checked dispatch: the arguments must satisfy the named variant's
precondition. B means unrestricted dispatch, with the same witness alternatives.
For a fully fixed argument assignment a and unknown flag/witness, completion
ALWAYS exists via B. With flag A fixed and witness free, completion exists
IFF Phi(a)=1. This is an existential union, not a sum of derivations.

## 2. Frozen head and original identities

Each argument slot has two original IDs, spelling0/1, probability1/2 each.
The flag slot has FOUR original IDs: two aliases for A, two for B, all1/4.
The witness slot has m original IDs, all1/m. This is the complete declared
law; outside IDs have probability ZERO, not discarded positive mass. IDs and
aliases survive selection/reconstruction. Use independent continuous Gumbel
rankings (temperature1) of log probabilities per slot. Equivalently, each
slot has the Plackett--Luce ranking of its original IDs.

The proposal confidence is the ORIGINAL ID probability. Thus all argument
proposals have confidence1/2, flag proposal1/4 and witness proposal1/m<=1/5.
Order argument positions first (any fixed tie rule), flag next, witness last.
The top flag spelling is A with probability1/2, independently of the uniform
n-bit argument assignment. Aliases preserve these confidence gaps: merging
alias probabilities to a1/2 byte event before ordering would be WRONG.

## 3. Greedy compatibility kernel

At each slot, inspect original IDs in its sampled ranking and commit the first
one retaining at least one grammatical completion with all prior commits.
This is the ideal finite-support greedy operation corresponding to the native
confidence-ordered core, NOT a claim of every numeric/toolchain detail of
complete EPIC. Charge ALL rejected choices and completeability checks.

Every argument proposal is accepted, because B remains possible. Thus a is
uniform in{0,1}^n, independent of the flag ranking. If the top flag spells B,
it is accepted. If it spells A, it is accepted iff Phi(a)=1; otherwise BOTH
A aliases are rejected and the first B alias is accepted. Finally a compatible
witness is always available. Therefore the event of an ACTUALLY COMMITTED A
has exact probability

    p_A = #Phi / 2^(n+1).

Not the raw proposal event, not posterior mass, and not derivative counting.

Computing p_A exactly computes #DNF by multiplication by2^(n+1), with O(n)
bit denominators. Exact #DNF is #P-complete under polynomial-time Turing
reductions; from #CNF one can negate to DNF and subtract from2^n. This is the
CLASSICAL complexity premise. It does not imply hard approximation (#DNF
has an FPRAS), hard grammar membership, or hard exact sampling of this kernel.
This kernel itself runs in polynomial time: at most n+4+m original candidates,
and completion is polynomial on a CFG/lattice. In this family it is just
checking compatible terms, O(mn) per query or less incrementally.

Native check_valid's abstract gaps do not invalidate the fixed-suffix union:
AFTER the n argument tokens are fixed, the only unfixed region is BEFORE them.
Witness names/delimiter use disjoint terminals, and every grammar word has
exactly n argument bits, so an unbounded gap cannot reinterpret or add an
argument. Earlier argument commits always have B completions. Do not extend
this reasoning to arbitrary partially fixed native gaps or EOS/PAD rules.

## 4. MWPC primary optimum gives the same committed tag event

Give every top original proposal its confidence weight. A completion may
match argument proposals, flag proposal and witness proposal; other weights
are zero. There exists a completion matching ALL n arguments and the witness
(via B), score n/2+1/m. Losing even one argument gains at most1/4+1/m<1/2,
so NO primary optimum loses an argument proposal. When the flag proposal is B,
it is compatible with all arguments and witness and is matched. When it is A:

- if Phi(a)=0 it cannot be matched;
- if Phi(a)=1 there exists a witness retaining A, adding1/4, even if the top
  witness's1/m reward is lost; because1/4>1/m, EVERY optimum matches A.

Consequently the matched-A event for MWPC also has p_A. Do not infer complete
same-path/alias/fallback equivalence from this event equality. Reconstructing
an unmatched flag after A infeasibility yields B, but if reporting only
matched-proposal events keep that output contract distinct.

## 5. The CFG posterior is a different, easy distribution

For the SAME frozen product and declared domains, each witness is distinct.
The valid unconditioned mass is

    Z = 1/2 + (1/(2m)) sum_j 2^(-ell_j).

The posterior flag-A marginal is

    P_product(A | valid) = R/(m+R), R=sum_j 2^(-ell_j).

Computing R/Z is polynomial rational arithmetic; each witnessed word has a
unique parse. Overlapping terms count DISTINCT witnessed words, correctly.
This is why an exact LL(1) CFG posterior or factor plan does NOT supply p_A of
the greedy/MWPC kernel: the latter accepts a tag based on an existential union
before choosing the witness. In general #Phi is not R*2^n. Counting each term
and adding it as though disjoint would give an erroneous native law.

## 6. Relevance and nonclaims

This establishes a computationally legitimate reason why a structured native
transition class need not have cheaply available p, even with simple syntax,
tractable per-draw selection and all model logits visible. It does NOT prove
that an optimal coupling must evaluate p, or that real EPIC kernels usually
exhibit this hardness. A34's exact regular sample-only budget frontier can
coordinate such a sampler without calculating p; raw-noise/full-grammar methods
remain competent controls OUTSIDE that information-theoretic lower bound.

No semantic correctness, physical latency advantage or publication novelty is
asserted from this family. It is a mathematical object, not experimental data.
A useful native implementation still needs a class of accepted transitions
with semantic signal and cheap auxiliary draws, with entire cost reported.
