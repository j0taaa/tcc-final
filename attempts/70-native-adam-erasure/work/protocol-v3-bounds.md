# V3 — Bound admission repair, BEFORE new source/build/audit

V2 passed its original768-case numerical grid. AFTER-data inspection found
that bound(x=maxfinite,r<M) exceeds the float grid because its sound gamma
is positive, even though the actual native decay is finite. The numerical
oracle raises; the proof requires exact fallback. V2 source/result stay intact.

New independent V3 copies keep the SAME recurrence, inputs, original768
cases, H=512 and no timing/benefit gate. All C APIs use prefix a70_v3_.
Change ONLY certificate/admission handling: r=0 returns the exact starting
upper endpoint; a bound above maxfinite is unavailable and triggers moment
replay BEFORE native endpoint tests; invalid s/h/table ranges and fresh
nonfinite gradients are rejected before C entry.

Add EIGHT adverse correctness regressions: s=1024, starting state
(w=1,m=least-positive-subnormal,v=maxfinite), h in{0,1,15,512}, fresh
g in{R(-.1),R(.1)}. Compare read/full next-state bits to literal C, and
retain the unavailable-bound/fallback status. These are numerical checkpoint
fixtures, not evidence of frequency/reachability in a trained model. Test
invalid negative/oversized gaps, zero starting step and nonfinite fresh
gradient admission. Do not count any added case as a useful performance win.

Run ONE corrected audit into a new directory AFTER source commit, preserving
all prior artifacts. Report original768 and the eight regressions separately.
No whole-kernel/library identity, timing competition, neural or workload
campaign is triggered; priority/use/complete-cost benefit remain OPEN.
