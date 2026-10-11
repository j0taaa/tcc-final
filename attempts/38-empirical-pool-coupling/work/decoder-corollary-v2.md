# A38 decoder corollary and full-cost gate

2026-10-11. Written BEFORE any A38 model/quality measurement. Transition
coupling and conditional-mean proofs are known (also A26/A31). The candidate
difference remains the cap4 categorical/pointwise-cost theorem, NOT a claim
that applying a known antithetic principle to a dLLM is automatically new.

## One accepted transition, arbitrary complete continuation

Fix a prompt, CFG, model, tokenizer, EOS/recovery policy and sufficient native
starting state. D independently simulates ONE COMPLETE accepted native
transition, including rejected proposals, remaining budgets, model-query
phase and failures. The payload includes its original resumable generator
and private future RNG; alternatively use independent correctly distributed
future randomness after the state. A fixed key may be its next canvas or
any coarser observable classification, with NO gold answer. The key itself
need not encode every future variable, because the FULL payload is retained.

Let p_i be the native key law and h_i=E[f(final answer)|key=i] for ANY bounded
terminal score or verifier f. Apply A38 to D, then continue the two selected
literal generators to completion. The independent within-key payload lift
gives EXACT original full trajectory marginals, even when future logits
change adaptively. No assumption of stable future logits is made. It gives

    Cov(f(final X),f(final Y))
      =-(1-c) sum_i p_i^2*(h_i-mu)^2
       -(sum_i p_i^2*(h_i-mu))^2 <=0.

Here mu is the original complete decoder's expectation and c=sum_i p_i².
For every final verifier, pass@2 is never below two iid executions of THAT
same decoder. Improvement is STRICT when c<1 and h_i is not constant on
positive-mass keys. Its magnitude is NOT established by distinct canvases.
It does not increase pass@1, change tokens, repair invalid native outputs,
or prove superiority over stronger batch decoders or altered temperatures.

This derivation is also valid for a complete-answer oracle; in that case
all three/four full generations cost. In the transition version a shared
immutable frozen head may supply auxiliaries without extra model forwards,
but EVERY native selection/rejection/parsing, head clone and discarded
generator is charged. Temperature-zero native alias/mutation behavior must
be preserved. Sharing a head requires identical model inputs and deterministic
inference; share immutable values and give each native execution its own copy.

## Repeated coordination: sufficient-state requirement remains

Only coordinate two trajectories again when their COMPLETE native sufficient
states match, including clock/phase/schedule/EOS/recovery budgets, not merely
their keys or token canvases. With independent transitions otherwise, the
product of their original conditional terminal means is a supermartingale:
at a common state the displayed gap is nonnegative, and at different states
conditional independence preserves the product expectation. A finite common
horizon with absorbing completion states yields the same weak pass@2 and
variance guarantees. The standard conditional-mean principle is not new.
No repeated native adapter has been implemented or validated in A38.

## A real advantage still requires full costs

Controls must include iid2/3/4 and resource-matched mixtures, raw-ticket
stratification with native aliases, competent binary coupling when classes
are known binary, the independently implemented grouped-rank pool4 with
the SAME law, and informed methods when their probabilities are available.
Do not charge a model forward only to the controls, ignore auxiliaries,
condition away failures, restrict cheap verification or omit duplicate reuse.

The root query count alone does NOT determine forwards of the continuations.
More diverse states can defeat later forward caching. Those costs and all
final outputs must be recorded. A four-draw pointwise optimum is not an
optimal decoder at a wall-time budget. No quality or latency gate has passed.

## Small implementation and open priority

The reference has29 lines and five independent exact tests passed0.056s.
A separate rank-rotation oracle CONFIRMS the SAME-law reduction, explicitly
crediting the construction as known; an informed uniform derangement is
stronger on ALL predicates. The source-hashed capture in evidence/law-v2.json
records these results. These constructed cases are correctness/proof
objects, not favorable model benchmarks. No model-head experiment, semantic
success gain, full-cost victory or human/publication review exists for A38.
