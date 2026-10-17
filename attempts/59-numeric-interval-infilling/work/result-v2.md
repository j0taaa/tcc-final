# V2 — Small positive compiler oracle; practical contribution still OPEN

2026-10-16 local date. The README/eight criteria and written construction
1aac564b280e89e78344df1f7fcffedfc85be386 precede all code. This is a new
semantic-number operation, not a reopening of A58's negative resource family.

The written claim gives a globally sound, byte-budget-complete unambiguous
NFA for a fixed finite positive exact-decimal interval. Its O_I(L) states AND
edges match an Omega(L) fooling-set lower bound for [1,2). The unbounded
semantic interval language is non-CFL by an explicit exponential-gap unary
image. Parikh/fooling sets, counters, shared suffixes and weighted automata
are CLASSICAL; this is not confirmed academic priority or a new generic
inference/sampling theorem. Uniform input-bound bit costs need more work.

The implementation is ONLY [1,2): a111-line module INCLUDING a conventional
weighted-token mass routine. It retains scientific notation, unlimited
fraction precision, exponent zero padding and original token-ID aliases.
L bounds mantissa order; accepting a correct longer input is allowed by the
written contract. No claim that its language is exactly truncated at L.
General intervals, JSON object composition, variable EOT/PAD and a native
dLLM integration have NOT been implemented by this prototype.

## Preserved initial failure and separate correction

Initial producer3a94c76480f039d50acf28589bd5eb890a4e1f78 runs4 tests in0.304s,
with3 PASS/1 FAIL. It permits an unsigned spelling of a NEGATIVE exponent.
Independent JSON/Decimal/Fraction evaluation finds the literal counterexample
10e1: actual value100, outside [1,2), while the NFA reports one accepting path.
Its complete log/receipt are in evidence/preflight-v1, committed97f01f8 before
repair. The written construction already requires a negative sign; its proof
is not relabeled as a different algorithm after this implementation error.

Corrected producer439f4b11e5fc2ae6af05141050c78fc5f421783d restricts the sign-
omitting epsilon transition to NONNEGATIVE exponents. It retains the real
10e1/10e+1/10e-1 and fractional regressions. Four oracles PASS0.737s:

* 48,880 separately parsed exact numeral values and10 malformed strings,
  checking accepting path count exactly0 or1;
* byte-budget witnesses, very long sound inputs and exponent-sign regressions;
* 900 prefix/suffix fooling pairs and concrete linear graph-size checks;
* 3 rational weighted-token scenarios,15 original-ID marginal coefficients,
  fixed holes, byte aliases, tokens spanning e/sign boundaries and zero mass.

The path-count checks prevent ambiguous accepting derivations from silently
changing the token-sequence law. Per-token advancement does NOT add a final
epsilon closure; closure occurs before bytes and once after the whole word.
The numerical reference uses Python's JSON parser with Decimal and Fraction,
not the compiler's order/comparison decomposition.

| Byte budget | States | Character/epsilon edges |
|---:|---:|---:|
|16|160|935|
|32|307|1834|
|64|595|3626|
|128|1200|7239|
|256|2423|14478|

These constructed graphs/oracles are mathematical checks, NOT model-resource
benchmarks, external application data or independent statistical confirmation.
Source hashes and exact counts are in evidence/preflight-v2/summary.json.

## Scientific decision and next required evidence

Continue the MINIMAL compiler/antecedent investigation. Do not promote it to
the article or start a model/timing campaign from these checks alone. The
pinned llguidance/XGrammar source audit identifies restricted range forms,
but an existing complete register/digit-DP compiler may obtain the same
compact result. That comparator must be implemented/understood fairly;
beating only a frontend with less lexical support is insufficient.

Need a concrete externally sourced numeric-infilling workload, exact semantic
contract with the consumer, general interval/EOT/PAD integration, tokenizer
lifting costs and a substantive own distinction. Canonical regeneration is
allowed when prefixes are editable; generic exact parsing/search and symbolic
arithmetic remain legitimate controls. No artificial delay or selected
favorable numeral family can establish complete-cost usefulness.

The A59 prototype performs ZERO model reads/heads/forwards, optimizer updates
or competitive timings. No accepted publication, human review, trained model,
large useful gain or fulfilled positive user goal is claimed.

Later maintained validation: full330 tests PASS94.438s, focused Ruff/format
PASS5 files. Complete logs are evidence/preflight-v2/full-tests.log and
ruff.log. Existing historical head fixtures in the maintained suite are not
new A59 model captures. No competitive benchmark ran alongside these checks.
