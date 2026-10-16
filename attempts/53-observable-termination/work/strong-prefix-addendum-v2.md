# V2 pre-old-data addendum: numeric-sealed prefix control

2026-10-16, before ANY A53 old-path certificate/count. Synthetic full-V
preflight exposed a mistaken expectation, not a compiler bug: a free slot
before fixed1} may add digits/sign and alter the number. Failed source/log
are retained. Do not claim that synthetic case certifies.

Strengthen the cheap-prefix control before real data: a contiguous fixed
numeric JSON prefix whose number has already ended in JSON whitespace
(lexer state19) determines the same observable even if } is not yet fixed.
Lexer state20 is the complete-object case. Both permit only closing syntax,
whitespace and EOS in subsequent viable continuations. This needs no inside
pass. Retain both cases in the SAME cheap-prefix comparator and unchanged
20%/two-question gate; never compare against only a weaker brace-wait rule.

The current projected singleton analysis must agree with this prefix whenever
it fires. The all16-path known development screen is still unexecuted. This
is an explicit pre-data control strengthening, no positive post hoc change.
