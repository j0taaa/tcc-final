# First-step boundary error, found by the actual native audit

2026-10-11. Preserve v6 contract, v7 prototype and the failed native capture.
Producer `df64be3e949d5ec713494da59a5146685260d2a1` stopped after its FIRST
information-audit source, before any useful result: ERROR `crossed first
native neural step`, two native model queries, ONE extra forward beyond
the shared initial head. The complete error/metadata remain. No win/zero
helper-forward or first-step information claim accompanies this run.

Cause: vendor's fallback loop uses `j` for its transfer iterator at line380,
but REASSIGNS `j=0` for the batch row at line453. Python's loop iterator
continues correctly; the visible frame local no longer reports the transfer
attempt number. V6's proposed `j==remaining-1` stopping rule is therefore
WRONG for the actual pinned decoder. The toy wrapper did not include this
clobber and was insufficient. This is an observer error, not a change to
EPIC's decoder. Do not edit the vendor or overwrite the evidence/proof.

Corrected proposed contract BEFORE implementing it: classify the SIX yield
sites of the immutable pinned native `generate` function. The first is the
fast compatible batch; the last is the terminal yield; the penultimate is
one successful fallback transfer; the other three immediately return on
failure. Count SUCCESSFUL fallback yields explicitly instead of reading j.
At fast/fallback yield, stop when committed batch plus observed fallback
transfers equals the initial step's transfer budget. Terminal/failure yields
stop immediately. Require native `i=0,num_block=0`, exact source hash/yield
sites and zero additional model forwards. Read locals/sites only; no replay,
vendor mutation, fabricated head, changed EOS/recovery or label filtering.

Add a regression with j reset to zero each transfer using the ACTUAL
no-grad generator wrapper. It must fail the previous boundary assumption
and pass the corrected one without a second simulated model call. Native
repeat uses a NEW evidence filename and immutable producer commit. Same
existing inputs/all predefined sources remain; no fresh statistical gate
is triggered by fixing this integration error. V1 mathematical query bounds
and v5 confirmed first-yield boundary are unaffected by this separate error.
