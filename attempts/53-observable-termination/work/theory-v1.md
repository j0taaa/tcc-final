# Observable terminal certificate — written contract and proof

2026-10-16, before prototype or A53 measurements. The principles below are
classical support reasoning, flat constant propagation and terminal coupling.
Their application is a candidate, not an established scientific advance.

## Completing monotone decoder and observable

A state s contains every fixed original token/position, canvas extent, EOS
convention and any control affecting future transitions. C(s) is a NONEMPTY
set of grammar-valid original-ID words through their FIRST EOS, each retaining
all fixed IDs. Future accepted actions only narrow C. The decoder completes
in finitely many steps, producing X_tau in C(s); for a forced-progress
64-slot policy a strict decrease of unfixed positions bounds the horizon.
An already paid-for witness w_s belongs to C(s). A supplied external JSON
prefix is included by the observer, not counted as a new model prediction.

The caller's observable is f(X), e.g. the parsed numeric JSON value. Raw token
IDs, exact bytes, time, intermediate streaming and failure status are NOT
part of that observable. This explicit API contract is essential. Random
resource failures are outside the ideal completing law. If failure status is
part of the target, do not convert possible failures to success and claim its
law preserved. No transfer to arbitrary remasking or EPIC rejection budgets.

A sound certificate returns TRUE only if f(C(s)) is a singleton. At the first
certified visible state sigma, stop and return w_s (or its declared parsed
observable). Until sigma run the SAME original decoder with identical random
streams; no forced re-tokenization or altered canvas while still running.

**Terminal coupling theorem.** The optimized and original final observables
agree pathwise. Hence their pushforward distributions and every bounded
observable score agree, under any proposal weights/future policy that obey
the completing/monotone contract.

**Proof.** If no early stop occurs, both executions coincide. Otherwise use
exactly the same prefix and imagine continuing the baseline with its remaining
randomness. Its completion X_tau lies in C(s_sigma); both it and the available
witness therefore have the singleton observable. No future model output can
change this conclusion. Equality pathwise implies equality in law. QED.

**Scope of necessity.** If every x in C(s) has positive conditional chance
of being the final word, and f(C(s)) has at least two values, no fixed
state/history-measurable returned observable can agree with that final
observable almost surely. Two positive-probability alternatives contradict a
single returned value. An ideal positive full-support grammatical proposal
with positive-probability full reveal has this property. This is a statement
about pathwise terminal rules, NOT a lower bound for all algorithms that can
sample a known final distribution, batching, oracle access or approximate
stopping. A conservative support superset gives soundness, not completeness
or earliest possible stopping. Finite floating zero probabilities can remove
necessity; they do not invalidate a superset certificate's soundness.

## A simple exact certificate for a finer string observable

For the first numeric-only consumer, let h erase JSON whitespace bytes and
empty/EOS emissions from the generated suffix. This is a byte-monoid
homomorphism. No generated JSON strings are allowed; the only key string is
in the supplied literal prefix. Equality of h-completions implies equal
numeric JSON semantics. It is stronger than necessary: 1 and1.0 remain
DISTINCT in this certificate. General JSON needs a state-aware output
transducer; erasing spaces inside strings would change values.

On a bounded acyclic token/grammar graph use the familiar flat string domain:
BOTTOM (no words), ONE(u) (one projected byte string), MANY (at least two).
Join ignores BOTTOM, preserves identical ONE values, otherwise returns MANY.
Product is BOTTOM if either operand is BOTTOM, concatenates two ONE strings,
and is MANY otherwise. This is a correct quotient of finite string-language
union/concatenation: if a factor has two strings and the other is nonempty,
fix one word in the other; free-monoid cancellation keeps two distinct
products. Thus the abstraction is EXACT for deciding singleton projected
language. It is not exact for arbitrary noninjective semantic arithmetic.

A backward DAG pass unions projected-edge-label times target value; accepting
first-EOS edges emit epsilon and terminate immediately. Never stop before a
fixed position at or after that EOS. All fixed original IDs remain edge
constraints. The result ONE(u) at the initial node is the certificate. Full
vocabulary IDs may be grouped only if they have the same grammar transition
and their projected output language is aggregated with the same flat domain.
Epsilon-output paths and tokenization aliases are retained, not deleted from
the grammar or policy. A general parse forest may use the same union/product
algebra on an acyclic derivation DAG; ambiguity does not change a set's image.
No claim of a new semiring, quotient principle or compiler algorithm.

## Cost consequence, not a measured speedup

For a paired original path, let saved original forward costs after sigma be
sum c_t. Let checking/compilation/witness/output overhead relative to the
competent baseline be a. Net saving is sum c_t-a; choose only when positive.
If each saved forward costs at least c_min and r are removed, benefit is at
least r*c_min-a under that explicit bound. Per-state checks, root sharing,
startup, serialization and GPU synchronization all belong in a. The theorem
has no claim that r is large or a small on real data. Existing cheap prefix
parsing and classical constant propagation are mandatory strong controls.
