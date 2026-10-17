# V3 — Complete semantic control and external-corpus FIT audit, before code

2026-10-16 local date. No resource/model experiment is authorized by this note.
README's eight criteria remain, with the following explicit reassessment:

1. Use is still exact-decimal interval infilling with fixed original bytes.
   A real external consumer has NOT yet been demonstrated. Generated schema
   conformance examples are not production infilling logs.
2. Suffix sharing and register/digit DP are classical. A59's specific bounded
   numeral theorem remains a written candidate; no unique generic compiler or
   asymptotic separation from complete semantic methods is established.
3. Supply the complete control below, not just restricted numeric frontends.
   It has the same bounded completeness and linear state order. No timing or
   superiority claim follows from agreement.
4. Its state-size/equivalence argument below precedes implementation. Existing
   non-CFL/fooling-set statements are unchanged, not rebranded as new tools.
5. Check complete byte-language equivalence by a finite product search and
   independent exact numeral/token laws. The corpus inspection below is
   descriptive ONLY, never independent performance/quality confirmation.
6. Count states/edges separately from bits, transition caching and full costs.
   O(L) graph entries require O(L log L) bits with ordinary numeric state IDs;
   a one-word register recognizer may use only O(log L) live bits. Neither
   count proves a useful full-model memory/latency gain.
7. A direct standard register construction may remove the alleged own
   algorithmic distinction. Corpus examples might contain no suitable fixed
   scientific-notation fields. Both objections must be retained.
8. Complete controls, specific priority and an actual consumer remain OPEN.
   No extensive general-interval/native implementation or neural campaign
   follows automatically from this audit.

## Complete independent register/digit-DP control

For [1,2), normalize a nonzero mantissa as10^d*m. Its first significant digit
must be1; all later digits are arbitrary. Its exponent must be E=-d. Maintain
the ordinary JSON numeric syntax phase and d in[-L,L], with the same byte
budget contract. After e/E, store the required signed exponent. Consume a
mandatory minus for a negative target, optional plus for a positive one, and
either/absent sign for zero. Leading exponent zeros do not change the target.
After the first nonzero digit, the state is just the REMAINING required
decimal suffix; identical suffixes represent the same state. Zero requires
at least one digit and then loops on zero. No epsilon transition is needed.

Implement this directly as a deterministic next(state,byte) function, with
lazy reachable-state memoization; do NOT import the candidate's graph,
compiler or epsilon implementation. Classical sum-product over these states
gives original-ID token mass/marginals without full word enumeration. The
syntax/order phase has O(L) states. Distinct residual decimal strings of the
integers0..L have O(L) suffixes, so all reachable states/edges are O(L).
This control therefore matches the current representation's capacity AND
asymptotic size. A naive unshared per-order trie is not an adequate comparator.

For each L in8,16,32,64, explore the entire product of this DFA and the counted
candidate-NFA configurations on ALL256 byte values, starting at their initial
states. Compare acceptance/path counts in every reached state. Exhausting
this finite product proves equality for every byte string for those compiled
instances, not only a selected finite set of numerals. Keep every failure.
Also check the same48,880 independent JSON/Decimal/Fraction values and exact
weighted token laws with fixed slots, aliases and empty support. Those are
mathematical checks, not an independent model dataset or comparative timing.

## Primary antecedents actually read this turn

[Daciuk/Mihov/Watson/Watson2000](https://aclanthology.org/J00-1002.pdf),
Sections2/3 through Algorithm1 and its complexity discussion (PDF pages2--7),
explicitly merge equal right languages/suffix subgraphs and avoid the full
intermediate trie. This already supplies the generic suffix-sharing mechanism.
It does NOT itself state A59's numeral theorem or implement interval infilling.
Do not infer that a specific numeral result is prior merely because its tools
are old; equally, do not claim suffix sharing as ours.

[Yin et al.2512.19701v1](https://arxiv.org/html/2512.19701v1), Sections3.1--3.4
and4.2, already uses standardized scientific numeric outputs, deterministic
JSON prefix filling and digit/sign masks for EDA resource prediction, then
clips predictions to the training range. It is autoregressive, not dLLM
arbitrary-hole conditional sampling. Thus scientific notation/prefix filling
alone are NOT a new application idea. The industrial data described there
have not been obtained, and no reproduced benefit is attributed to A59.

## Descriptive external-corpus audit, frozen before bulk inspection

Pin guidance-ai/jsonschemabench at9a94995b9279ae3af3aed4b2629172790b968d14.
Git tree metadata lists ALL11306 maskbench/data/*.json files,143978678 bytes.
Before this note, one filename was chosen solely by SHA256(path) among
nonsynthesized files to inspect its FORMAT: Github_medium---o21361.json.
Its schema/test keys and a single nonnumeric instance were read. This is
explicitly development reading, not unseen confirmation.

Read ALL11306 files, no schema/value filtering before counts. Preserve file
hashes, parse failures and label inconsistencies. Treat number lexemes as
tagged raw strings and compare exact Decimal values; do not round through
float. Count direct bounds on schema nodes, numeric types, supplied test
instances and scientific/long-precision lexemes. Traverse only direct
properties/items where the schema-instance correspondence is unambiguous;
record that this does not resolve refs/combinators or validate whole schemas.
Retain positive/zero/negative/open intervals and unfavorable counts. A valid
test label is supplied corpus metadata, not proof of exact-decimal validity.
No invented exponent reformattings or manufactured prefixes are permitted.

The primary MaskBench README's Testcases section says most examples were
generated by Llama3.1-70B and then mutated. Therefore they are an external
CONFORMANCE workload; they cannot establish natural production infilling
frequency, original raw neural output spellings or a real deployed consumer.
The independent JSON Schema Test Suite's four bound files were also read for
contract coverage, not as production data; their hashes will be retained.

Budget: external sparse source cache only,1GiB additional disk,600s fetch/read,
1GiB process RSS. No model/head/forward, target fitting, decoder execution or
competitive timing. This is a descriptive fit audit with NO positive gate
authorizing a model campaign. Counts only determine whether/where more
consumer investigation is justified; they do not meet the user's goal.
