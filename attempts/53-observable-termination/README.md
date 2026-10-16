# A53 — Stop a completing dLLM when its observable output is determined

2026-10-16. WRITTEN before prototype/new measurements/heads. This changes the
operation from A52's failed reward-gradient application; that branch stays
closed. No new neural campaign, timing win, priority or achieved goal yet.

1. **Real use.** A caller consumes a parsed numeric JSON result, rather than
   the raw original-ID trace. A grammar-conditioned monotone dLLM may keep
   spending forwards on whitespace, empty-token aliases and EOS after its
   observable result is determined. Return the previously available valid
   proposal witness when a sound current-state certificate proves that every
   admissible completion has the same observable. The current proposal is
   already paid for; no label or new head is needed to check the certificate.
2. **Precise difference.** Investigate an exact terminal optimization preserving
   the final observable under a coupling with the original completing decoder.
   This DOES NOT preserve its raw text/token trace. EOS termination, grammar
   jump-forward, semantic realizability, quotient kernels and flat constant
   propagation are antecedents, NOT inventions. A useful own dLLM application
   and sufficient incremental originality remain hypotheses. The proof below
   is a restricted application of those classical ideas, not new parsing theory.
3. **Reason to choose.** Potentially skip all remaining forwards after semantic
   absorption while preserving the caller's output law, without training or
   confidence thresholds. The necessary benefit condition includes checking
   and returning the witness; zero extra neural calls is not zero work.
   Baselines: existing first-EOS stop, cheap contiguous-prefix JSON parsing,
   forced-token/byte propagation, a classical generic DAG constant analysis,
   and a no-optimization completing decoder. The classical DAG analysis can
   supply the SAME certificate; no speed/novelty claim over it is allowed.
4. **Proof first.** work/theory-v1.md gives the pathwise terminal theorem,
   its scope/necessity and the flat-language calculation. It proves equality
   of the declared observable, not semantic correctness of the model answer.
5. **First experiment.** ONLY a minimal independent finite-language oracle:
   exhaustively enumerate bounded completions, aliases, EOS, fixed positions,
   erasing-output tokens and divergent contexts. No real old-path counts,
   native heads, golds or timings before a separately frozen screen. New
   corpus/full-cost controls require another written protocol if warranted.
6. **Full cost.** Compile tokenizer/grammar, retain a valid witness, certificate
   at every checked state, data movement, serialization and all original/new
   forwards. Original IDs before stopping stay fixed; returned witness may
   differ from the unexecuted raw suffix. Caching and root sharing must be
   charged equivalently. A raw-token/streaming consumer may not use this API.
7. **Objections.** The cheap prefix parser may find every useful stop already;
   forced syntax or a canonical output grammar may be better when changing
   the target law is acceptable. Most states may have multiple observables.
   Classical constant analysis may subsume all technical content. Finite
   failure/timeout status and a remasking decoder invalidate naive absorption.
   Ignoring whitespace inside JSON strings is UNSOUND; numeric-only erasure
   cannot be transferred to general JSON without a lexical transducer proof.
8. **Article gap.** Specific sufficient novelty, nontrivial applicability,
   complete-cost benefit over competent controls, real preserved neural
   trajectories and independent external confirmation. No main-paper promotion
   or guaranteed acceptance. Close the simple direction if its own distinction
   or nontrivial useful gain fails; negative code/tests alone do not meet goal.

Primary sources/scopes: work/primary-v1.md. No A52 mutable implementation is
imported by this attempt. First only a standalone small certificate oracle.
