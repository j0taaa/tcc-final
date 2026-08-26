# ADR 0015: Record semantic alignment of paired grammar representations

- Status: Accepted
- Date: 2026-08-26

A benchmark that replays both exact and EPIC selectors records one source grammar ID, exact and EPIC compiler versions, an alignment method, accepted and rejected token-sequence cases, and a SHA-256 digest. Replay reconstructs both representations and recomputes every recorded case before comparing selectors. Hash equality alone is not treated as evidence of language equivalence.
