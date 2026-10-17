# Reference evidence and limits

Written contract/proof commit537af90, classical-control addendum6515cfc,
reference/result commit2f2e784. Full301 tests PASS85.439s before the eighth
oracle; full302 PASS85.791s includes it. Focused8 pass; explicit Ruff check
and format pass. These are CPU correctness checks, not comparative latency.
No pretrained head, real matrix sample/statistic, new auxiliary neural draw,
model update or application quality label was obtained.

`make-check-before-archive.log` was frozen while the final archive integrity
command was still running; it is retained literally and is NOT a complete
pass log. `make-check-completed-before-archive.log` is the complete output
after exit0, before registering A55 (54 attempts/226 versions). Later archive
registration/checks have their own current-state counts. A running check log
was committed too early; no scientific measurement is attributed to that
partial log. The original and completed files are both preserved.

The scalar reference, independent determinant/coefficient oracles and explicit
classical reduction are the evidence. The latter closes the simple NB/Ewens
construction's current claim of sufficient own distinction. It does not
refute weighted-assignment sampling or establish a timing comparison.
