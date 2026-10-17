# V7a — Uniform input-size clarification

2026-10-17. V7's bounds are polynomial in the expanded byte source and L.
For a uniform input-size statement, compute the actual longest emitted byte
path of the acyclic source by ordinary DAG dynamic programming, and take its
maximum with1. Each path uses at most E expanded edges, so this L is at most
max(1,E). Do not let an unnecessarily loose binary-encoded supplied bound
stand for a polynomial in the source-description size. The fixed-row reference
already computes its safe bound from maximum positive-weight emitted lengths
per row. No code, model, timing or new priority claim results from this note.
