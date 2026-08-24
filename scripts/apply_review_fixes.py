#!/usr/bin/env python3
"""Apply the review corrections deterministically to the current checkout."""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def replace_once(path: str, old: str, new: str) -> None:
    target = ROOT / path
    text = target.read_text(encoding="utf-8")
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"expected exactly one match in {path}, found {count}")
    target.write_text(text.replace(old, new, 1), encoding="utf-8")


def append_once(path: str, marker: str, content: str) -> None:
    target = ROOT / path
    text = target.read_text(encoding="utf-8")
    if marker in text:
        raise RuntimeError(f"content already present in {path}: {marker}")
    target.write_text(text.rstrip() + "\n\n" + content.strip() + "\n", encoding="utf-8")


def main() -> None:
    replace_once(
        "src/mwpc_exact/reference/token_aligned.py",
        "from __future__ import annotations\n\nfrom collections.abc import Iterable, Mapping, Sequence\n",
        "from __future__ import annotations\n\nimport hashlib\nimport json\nfrom collections.abc import Iterable, Mapping, Sequence\n",
    )
    replace_once(
        "src/mwpc_exact/reference/token_aligned.py",
        """    represented_token_ids = tuple(lexical.terminal_token_ids.values())
    if any(token_id >= exactness_scope.vocabulary_size for token_id in represented_token_ids):
""",
        """    represented_token_ids = tuple(lexical.terminal_token_ids.values())
    mapped_token_ids = frozenset(represented_token_ids)
    if exactness_scope.kind is SupportKind.FULL:
        if per_position_support is not None:
            raise ValueError(
                "FULL support is derived from the complete token mapping; "
                "per_position_support must be omitted"
            )
        expected_full_vocabulary = frozenset(range(exactness_scope.vocabulary_size))
        if mapped_token_ids != expected_full_vocabulary:
            missing = sorted(expected_full_vocabulary - mapped_token_ids)
            extra = sorted(mapped_token_ids - expected_full_vocabulary)
            raise ValueError(
                "FULL support requires the token-aligned terminal mapping to cover "
                f"every vocabulary token (missing={missing}, extra={extra})"
            )
    elif per_position_support is not None:
        for position, raw_support in enumerate(per_position_support):
            support_tokens = frozenset(raw_support)
            unmapped = sorted(support_tokens - mapped_token_ids)
            if unmapped:
                raise ValueError(
                    f"support at position {position} contains token IDs without a "
                    f"token-aligned terminal mapping: {unmapped}"
                )
            fixed_token_id = canvas_tokens[position]
            if fixed_token_id is not None and fixed_token_id not in support_tokens:
                raise ValueError(
                    f"fixed canvas token at position {position} is absent from "
                    "the represented support"
                )

    represented_support_token_ids = tuple(
        tuple(
            sorted(
                lexical.terminal_token_ids[terminal_id]
                for terminal_id, reward in row.items()
                if reward.score != NEGATIVE_INFINITY
            )
        )
        for row in lexical.rows
    )
    support_json = json.dumps(
        [list(row) for row in represented_support_token_ids],
        separators=(",", ":"),
    ).encode("utf-8")
    support_sha256 = hashlib.sha256(support_json).hexdigest()
    if any(token_id >= exactness_scope.vocabulary_size for token_id in represented_token_ids):
""",
    )
    replace_once(
        "src/mwpc_exact/reference/token_aligned.py",
        """    base_diagnostics: dict[str, object] = {
        "algorithm": "python_token_aligned_cky",
        "chart_entries": len(solve.chart.entries),
        "slot_count": lexical.slot_count,
    }
""",
        """    base_diagnostics: dict[str, object] = {
        "algorithm": "python_token_aligned_cky",
        "chart_entries": len(solve.chart.entries),
        "slot_count": lexical.slot_count,
        "support_kind": exactness_scope.kind.value,
        "represented_support_token_ids": [
            list(row) for row in represented_support_token_ids
        ],
        "represented_support_row_sizes": [
            len(row) for row in represented_support_token_ids
        ],
        "represented_support_sha256": support_sha256,
    }
""",
    )

    append_once(
        "tests/exact_commit/test_token_aligned_certificate.py",
        "test_full_scope_rejects_incomplete_vocabulary_mapping",
        r'''
def test_full_scope_rejects_incomplete_vocabulary_mapping() -> None:
    full_scope = ExactnessScope(kind=SupportKind.FULL, vocabulary_size=256)

    with pytest.raises(ValueError, match="cover every vocabulary token"):
        solve_token_aligned(
            grammar=pair_grammar(),
            canvas=(None, None),
            proposals=PROPOSALS,
            exactness_scope=full_scope,
            terminal_token_ids=TOKEN_IDS,
        )


def test_full_scope_rejects_explicitly_pruned_rows() -> None:
    full_scope = ExactnessScope(kind=SupportKind.FULL, vocabulary_size=2)

    with pytest.raises(ValueError, match="per_position_support must be omitted"):
        solve_token_aligned(
            grammar=pair_grammar(),
            canvas=(None, None),
            proposals=(Proposal(1, 0, 0, 1), Proposal(2, 1, 1, 1)),
            exactness_scope=full_scope,
            terminal_token_ids={10: 0, 20: 1},
            per_position_support=((0,), (1,)),
        )


def test_valid_full_scope_covers_the_declared_vocabulary() -> None:
    full_scope = ExactnessScope(kind=SupportKind.FULL, vocabulary_size=2)
    result = solve_token_aligned(
        grammar=pair_grammar(),
        canvas=(None, None),
        proposals=(Proposal(1, 0, 0, 1), Proposal(2, 1, 1, 1)),
        exactness_scope=full_scope,
        terminal_token_ids={10: 0, 20: 1},
    )

    assert result.status is SolveStatus.OPTIMAL
    diagnostics = result.to_dict()["diagnostics"]
    assert diagnostics["support_kind"] == "full"  # type: ignore[index]
    assert diagnostics["represented_support_token_ids"] == [  # type: ignore[index]
        [0, 1],
        [0, 1],
    ]
    assert len(diagnostics["represented_support_sha256"]) == 64  # type: ignore[arg-type,index]


def test_explicit_support_must_include_fixed_canvas_tokens() -> None:
    with pytest.raises(ValueError, match="fixed canvas token.*absent"):
        solve_token_aligned(
            grammar=pair_grammar(),
            canvas=(100, None),
            proposals=(),
            exactness_scope=SCOPE,
            terminal_token_ids=TOKEN_IDS,
            per_position_support=((200,), (200,)),
        )


def test_explicit_support_rejects_unmapped_token_ids() -> None:
    with pytest.raises(ValueError, match="without a token-aligned terminal mapping"):
        solve_token_aligned(
            grammar=pair_grammar(),
            canvas=(None, None),
            proposals=(),
            exactness_scope=SCOPE,
            terminal_token_ids=TOKEN_IDS,
            per_position_support=((100, 123), (200,)),
        )


def test_explicit_support_is_recorded_in_machine_readable_diagnostics() -> None:
    result = solve_token_aligned(
        grammar=pair_grammar(),
        canvas=(None, None),
        proposals=PROPOSALS,
        exactness_scope=SCOPE,
        terminal_token_ids=TOKEN_IDS,
        per_position_support=((100,), (200,)),
    )

    assert result.status is SolveStatus.OPTIMAL
    diagnostics = result.to_dict()["diagnostics"]
    assert diagnostics["support_kind"] == "explicit"  # type: ignore[index]
    assert diagnostics["represented_support_token_ids"] == [  # type: ignore[index]
        [100],
        [200],
    ]
    assert diagnostics["represented_support_row_sizes"] == [1, 1]  # type: ignore[index]
    assert len(diagnostics["represented_support_sha256"]) == 64  # type: ignore[arg-type,index]
''',
    )

    replace_once(
        "Makefile",
        ".PHONY: bootstrap bootstrap-epic verify-upstream install check lint format typecheck test test-unit test-upstream paper clean\n",
        ".PHONY: bootstrap bootstrap-epic verify-upstream install check lint format typecheck test test-unit test-exact test-upstream paper clean\n",
    )
    replace_once(
        "Makefile",
        """test-unit:
	$(VENV_PY) -m pytest -q tests/unit

test-upstream:
""",
        """test-unit:
	$(VENV_PY) -m pytest -q tests/unit

test-exact:
	$(VENV_PY) -m pytest -q tests/exact_commit

test-upstream:
""",
    )
    replace_once(
        "Makefile",
        """test: test-unit

check: verify-upstream lint typecheck test-unit
""",
        """test: test-unit test-exact

check: verify-upstream lint typecheck test
""",
    )
    replace_once(
        ".github/workflows/ci.yml",
        """      - name: Unit tests
        run: python -m pytest -q tests/unit
""",
        """      - name: Unit and exact-commit tests
        run: python -m pytest -q tests/unit tests/exact_commit
""",
    )

    replace_once(
        "TASKS.md",
        """Current starting point: **M2 / T200**. M0 through the M1 gate are complete at the
immutable commits recorded below; no MWPC solver result is claimed by the M0
baseline.
""",
        """Current starting point: **M4 / T400**. M0 through M3 are complete at the
immutable commits recorded below. Do not redo completed milestones unless a
regression, failed check, or explicit review finding invalidates their evidence.
""",
    )
    replace_once(
        "TASKS.md",
        """reference package; the EPIC submodule remained pinned at `5b1b310`.

---

# M4 — Generic weighted terminal-DAG reference solver
""",
        """reference package; the EPIC submodule remained pinned at `5b1b310`.

**Configured-case scope:** the M3 campaign uses deliberately tiny finite
instances (two or three slots, a three-token toy vocabulary, and the recorded
acyclic/recursive grammar families). It is an executable regression gate for
the reference implementation, not a replacement for the formal proof and not
a claim over every possible CFG or support shape.

---

# M4 — Generic weighted terminal-DAG reference solver
""",
    )

    replace_once(
        "START_HERE.md",
        """The repository structure, pinned upstream baseline, LaTeX article, CI skeleton and core Python data contracts are present. No baseline build, oracle agreement, parser correctness, tokenizer property, runtime result or end-to-end result has been asserted.

Begin at `T000`. Verify the submodule SHA and licenses, then produce reproducible environment evidence. Do not mark a task complete because files exist; execute its acceptance checks.
""",
        """M0 through M3 are complete. The pinned EPIC baseline has been reproduced, the scientific contracts are frozen, the token-aligned Python solver is implemented, and its objective agrees with both exhaustive oracles over the configured deterministic campaign. No tokenizer, Rust-production-parser, runtime benchmark, or end-to-end dLLM result has been asserted.

The next required task is `T400`: validate and index a generic weighted terminal DAG. Preserve the completed evidence unless a regression or explicit review finding invalidates it.
""",
    )
    replace_once(
        "START_HERE.md",
        """## Definition of the first deliverable

Create the token-aligned Python reference solver and two independent exhaustive oracles. Randomized tests must demonstrate:

```text
max-plus CKY optimum
  = exhaustive valid-completion optimum
  = exhaustive compatible-subset optimum
```

for every tested finite instance. Record commands, seed ranges and test counts in the relevant `TASKS.md` Evidence fields.
""",
        """## Definition of the next deliverable

Implement M4's generic weighted terminal-DAG reference solver without weakening the completed M3 gate. The DAG implementation must validate acyclicity and stable IDs, reconstruct a certificate, agree with explicit path enumeration on tiny graphs, and reduce exactly to the token-aligned solver on layered per-slot DAGs.
""",
    )

    replace_once(
        "README.md",
        "No benchmark result, correctness result, or model result is claimed in this bootstrap commit. Placeholders must remain placeholders until backed by reproducible artifacts.\n",
        """## Current implementation status

M0 through M3 are complete: the EPIC baseline and environment are recorded, scientific contracts are frozen, and the token-aligned Python max-plus CKY solver agrees with both independent exhaustive oracles on the configured deterministic campaign. The next required task is M4/T400. No tokenizer-aware, Rust-production-parser, runtime benchmark, or end-to-end model result is claimed yet; implementation-dependent article placeholders remain unchanged.
""",
    )
    replace_once(
        "README.md",
        """Read START_HERE.md, AGENTS.md, UPSTREAM.md and TASKS.md. Start at T000 and
continue in dependency order. Do not bypass correctness gates. Update task
checkboxes and Evidence fields only after running the required commands.
""",
        """Read START_HERE.md, AGENTS.md, UPSTREAM.md and TASKS.md. Continue from the
first incomplete required task in dependency order (currently T400). Do not
redo completed milestones or bypass correctness gates. Update task checkboxes
and Evidence fields only after running the required commands.
""",
    )
    replace_once(
        "README.md",
        """## First concrete target

The first scientific gate is a small token-aligned max-plus CKY implementation whose score agrees in every generated small case with both exhaustive completion enumeration and exhaustive proposal-subset enumeration. Do not begin tokenizer, model or performance integration before that gate passes.
""",
        """## Next concrete target

M3's token-aligned correctness gate has passed for the configured finite cases. The next target is M4: a generic max-plus CFG-on-DAG reference solver whose values and certificates agree with explicit path enumeration and with the layered token-aligned special case.
""",
    )

    replace_once(
        "docs/scientific-contract.md",
        """Never infer broader infeasibility from `INFEASIBLE_ON_SUPPORT`.

Every optimal result must allow an independent implementation to verify:
""",
        """Never infer broader infeasibility from `INFEASIBLE_ON_SUPPORT`. A public
solver must validate that the declared support kind matches the alternatives
actually represented. In particular, `FULL` requires complete vocabulary
coverage, while an explicit support may not omit committed tokens or include
choices that the active token/terminal interface cannot interpret.

Every optimal result must allow an independent implementation to verify:
""",
    )
    replace_once(
        "docs/decisions/0003-exactness-scope.md",
        """## Executable enforcement

`SolveStatus` defines five distinct values. `ExactnessScope` requires support
metadata and rejects top-K without `K`, invalid special tokens, and malformed
expansion sequences. `ExactCommitResult` permits objectives/certificates only
for `OPTIMAL`. The focused regressions are
`tests/exact_commit/test_exactness_scope.py` and
`tests/exact_commit/test_graph_and_result_contracts.py`. T801/T804 will make
adaptive-attempt and fallback diagnostics executable without changing these
meanings.
""",
        """## Executable enforcement

`SolveStatus` defines five distinct values. `ExactnessScope` requires support
metadata and rejects top-K without `K`, invalid special tokens, and malformed
expansion sequences. `ExactCommitResult` permits objectives/certificates only
for `OPTIMAL`.

The token-aligned reference solver additionally enforces the claim against the
represented alternatives: `FULL` rejects a partial token mapping or supplied
pruned rows; explicit rows reject unmapped alternatives and may not omit an
already committed token. Its diagnostics record canonical per-row token IDs,
row sizes, and a SHA-256 fingerprint of the represented support. The focused
regressions are `tests/exact_commit/test_exactness_scope.py`,
`tests/exact_commit/test_graph_and_result_contracts.py`, and
`tests/exact_commit/test_token_aligned_certificate.py`.

The current public result contract intentionally reports a zero-slot epsilon
witness as `UNSUPPORTED`; M2/M3 completeness evidence is therefore scoped to
non-empty physical canvases. T801/T804 will make adaptive-attempt and fallback
diagnostics executable without changing these meanings.
""",
    )
    replace_once(
        "docs/decisions/0004-grammar-normalization.md",
        """Duplicate normalized rules are merged as Boolean grammar alternatives, and
their source production IDs are combined. The diagnostic mapping is not a
claim that a source grammar has a unique derivation.
""",
        """Duplicate normalized rules are merged as Boolean grammar alternatives, and
their source production IDs are combined. These IDs are conservative
diagnostic associations, not a derivation-exact provenance certificate: unit
closure keeps a deterministic representative path and synthetic proxy rules
may merge associations from several source rules. The mapping is not a claim
that a source grammar has a unique derivation.
""",
    )

    print("Applied review corrections successfully.")


if __name__ == "__main__":
    main()
