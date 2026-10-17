# V6 — Classical coaccessibility before repeating the same tiny oracle

2026-10-17. All eight V5 criteria/contracts remain; no resource/model campaign.
The first V5 source321582c2a46ab08618eb12701b41c2fd573c2041 was frozen before
its oracle. The run was explicitly interrupted by SIGINT, exit130, during
the FIRST test's compact-quantile checks, not a completed/failed correctness
gate. Full traceback is retained in evidence/v5-interrupted/oracles.log.
It is inside V1's unchanged events() routine creating zero forward entries
while scanning the complete topology. No correctness discrepancy was observed,
and no passing four-oracle result is claimed for this interrupted run.

Before the next execution, remove output-DAG vertices whose exact suffix mass
beta is0. All original weights are nonnegative, so such vertices lie on no
positive-weight accepting path. Delete their incident arcs, retain the other
vertices/labels/weights/final markers, and renumber topologically. Every retained
vertex has the SAME beta: omitted successors contributed0. This preserves
all output-key path sums, the total law, CDFs and quantiles. If beta(start)=0,
keep a singleton nonfinal root so queries return EMPTY.

This is CLASSICAL coaccessibility/trimming, not a new numerical theorem or a
claim of competitive speed. Record raw and retained graph sizes. Full build,
beta computation and trimming must ALL be charged in any later protocol.
All complete controls receive equally strong trimming. V5's polynomial upper
bound still applies; trimming does not establish real model usefulness or
priority of the numerical relation. Preserve original V5 source/run literally;
freeze the revised source before re-running the SAME four independent oracles.
