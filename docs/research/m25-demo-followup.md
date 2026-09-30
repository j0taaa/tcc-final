# Follow-up geocoding support, after the archived v1 demonstration

The frozen M25 benchmark is complete and unchanged. Its two confirmation grids
were produced by `128c584`. All four v1 demo attempts also used that source and
the same quoted Belo Horizonte request; every attempt queried the API but
returned `query_empty`. Confidence/MAP selected `of "Belo Horizonte`, while
budget 64/EPIC selected `geographic coordinates of "Belo Horizonte`. These are
structurally valid supported strings, not correct place names.

The independent checker accepts their finite-slot certificates; a serialization
comparison bug (JSON list versus Python tuple) was fixed with an offline
regression over all four real records. No raw output was edited.

## Declared application restriction

`configs/demo/geocoding_v2.json` freezes `quote_free_names_v2` before the follow-up.
It starts from the same question-derived candidates and excludes names containing
an internal double-quote delimiter. Apostrophes in place names remain allowed.
The candidate builder had stripped a boundary quote while leaving the other
inside a multiword span. The profile retains multiple alternatives, including
Belo Horizonte, Belo and Horizonte; it does not receive an accepted API answer.

This restriction changes the represented support. It is not safe pruning of a
larger optimum, a grammar theorem, a general geographic entity recognizer or a
benchmark improvement. Exactness is still per step on the newly declared
support. The original M25/v1 construction stays available and its 928 generations
remain unchanged. Replay selects the recorded policy, preserving old records.

The same four policies (confidence 0.8, budget 64, canonical MAP 8, EPIC 32) ran sequentially on the unchanged request and model revision. All follow-up
attempts, including empty queries or failures, will be retained. This is a
post-hoc application diagnosis, not a preregistered accuracy estimate.

## Correctness gates

Six focused offline tests pass, including malformed dispatch, HTTP limits,
checksums, historical replay, quote filtering/apostrophes and all real v1
certificates. Full Python passes 1,130 tests; integration passes 19 with four existing skips.
Ruff, MyPy (87 files) and the upstream pin also pass. Gate evidence is
`docs/evidence/m25-experiment-verification.json`, recorded before committing
and launching live follow-up. No GPU timings are collected
while these checks run.


## Observed follow-up

All four follow-up records were produced by clean source `e7f6b43`.
Confidence 0.8, iterative MAP and EPIC generate Belo Horizonte and receive
nonempty API responses. Budget 64 generates a request fragment and again gets
an empty response. All eight v1/v2 attempts remain in the generated query
inventory. These observations do not change the 42-case benchmark conclusions.
