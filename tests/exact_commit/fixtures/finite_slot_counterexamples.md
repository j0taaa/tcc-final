# Finite-slot counterexamples, version 1

The machine corpus in `finite_slot_counterexamples.json` freezes a deliberately
relaxed abstract compatibility check. Given ordered proposal-token anchors
`c1, ..., cm`, that check asks whether the CFG intersects
`Sigma* c1 Sigma* ... cm Sigma*`. It does not allocate physical canvas slots
and does not allocate the required EOS token. A concrete grammar-valid token
witness proves that this abstract intersection is non-empty.

This abstraction is useful only as the false-positive side of the examples. It
is not called exact, and it is not an implementation of the proposed solver.
The finite result is always reported as `exact_on_support` over the explicit
rows stored in the fixture.

## Minimal one-slot construction

Both cases use two token IDs:

| token ID | bytes | finite role |
|---:|:---:|:---|
| 0 | `61` (`a`) | ordinary |
| 1 | none | EOS before termination, PAD after termination |

There is one physical slot with support `{0, 1}`, and the EOS policy is
`REQUIRED`. The abstract pattern contains the positive-weight anchor token
`a`; its grammar-valid witness is the one-token sequence `[a]`.

The slot proof is direct: every ordinary token consumes one physical slot, and
`REQUIRED` mode consumes one additional physical slot for EOS. Therefore the
abstract witness needs `1 + 1 = 2` slots, while the canvas has only one. This
is minimal for a non-empty abstract witness: a positive number of ordinary
tokens requires at least one slot, and explicit required termination raises
the minimum to two.

| case | grammar language | abstract objective | slots available / needed | finite exact-on-support result |
|:---|:---|---:|:---:|:---|
| `required_eos_one_slot_infeasible_v1` | `{a}` | 10 | 1 / 2 | `INFEASIBLE_ON_SUPPORT` |
| `required_eos_one_slot_lower_empty_v1` | `{epsilon, a}` | 10 | 1 / 2 | `OPTIMAL`, EOS-only witness, objective 1 |

In the first case, choosing `a` leaves no EOS slot, while choosing EOS emits
the empty sequence rejected by the grammar. In the second case, the same
abstract score-10 path still cannot fit, but the empty sequence is valid. The
finite solver therefore selects the represented EOS proposal with objective
1. This is a lower feasible alternative, not a timeout and not evidence about
any vocabulary or support outside the recorded rows.

Replay the parser result and the independent full-path enumeration with:

```bash
make test-m7-counterexamples
```

The command writes the deterministic summary
`docs/evidence/t703-finite-slot-counterexamples.json`, including the fixture
hash, positive slot shortfalls, exact status counts, witnesses, objectives,
and represented-support hashes.
