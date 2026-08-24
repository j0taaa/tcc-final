"""Public token-aligned reference API with support-scope enforcement.

The max-plus CKY implementation remains in ``_token_aligned_core`` so the
algorithmic core stays independently testable. This module validates that the
scope claimed by a solve matches the token alternatives actually represented
and records a canonical support fingerprint on every returned result.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import replace

from mwpc_exact.reference._token_aligned_core import (
    BinaryBackpointer,
    CertificateReconstructionError,
    ChartEntry,
    CkyChart,
    CkySolve,
    EmptyBackpointer,
    ReconstructedCkyCertificate,
    TerminalBackpointer,
    build_token_aligned_support_graph,
    reconstruct_cky_certificate,
    run_cky,
    solve_token_aligned as _solve_token_aligned,
)
from mwpc_exact.reference.grammar import CnfGrammar
from mwpc_exact.reference.lexical import (
    NEGATIVE_INFINITY,
    LexicalRewardTable,
    build_lexical_rewards,
)
from mwpc_exact.types import ExactCommitResult, ExactnessScope, Proposal, SupportKind

__all__ = [
    "BinaryBackpointer",
    "CertificateReconstructionError",
    "ChartEntry",
    "CkyChart",
    "CkySolve",
    "EmptyBackpointer",
    "ReconstructedCkyCertificate",
    "TerminalBackpointer",
    "build_token_aligned_support_graph",
    "reconstruct_cky_certificate",
    "run_cky",
    "solve_token_aligned",
]


def solve_token_aligned(
    *,
    grammar: CnfGrammar,
    canvas: Sequence[int | None],
    proposals: Iterable[Proposal],
    exactness_scope: ExactnessScope,
    terminal_token_ids: Mapping[int, int] | None = None,
    per_position_support: Sequence[Sequence[int]] | None = None,
) -> ExactCommitResult:
    """Solve one token-aligned instance after validating its support claim.

    ``FULL`` is accepted only when the token/terminal mapping covers every ID
    in the declared vocabulary and no caller-supplied pruned rows are present.
    Explicit rows may not contain unmapped choices or omit a committed token.
    The exact represented rows and a SHA-256 fingerprint are added to result
    diagnostics for independent replay.
    """
    if not isinstance(exactness_scope, ExactnessScope):
        raise TypeError("exactness_scope must be an ExactnessScope")
    if exactness_scope.kind not in {SupportKind.FULL, SupportKind.EXPLICIT}:
        raise ValueError("token-aligned reference solves require FULL or EXPLICIT support")

    canvas_tokens = tuple(canvas)
    proposal_items = tuple(proposals)
    lexical = build_lexical_rewards(
        grammar=grammar,
        canvas=canvas_tokens,
        proposals=proposal_items,
        terminal_token_ids=terminal_token_ids,
        per_position_support=per_position_support,
    )
    if per_position_support is not None and any(
        token_id >= exactness_scope.vocabulary_size
        for support in per_position_support
        for token_id in support
    ):
        raise ValueError("support token is outside the exactness-scope vocabulary")
    mapped_token_ids = frozenset(lexical.terminal_token_ids.values())
    _validate_scope_against_support(
        exactness_scope=exactness_scope,
        canvas=canvas_tokens,
        mapped_token_ids=mapped_token_ids,
        per_position_support=per_position_support,
    )

    result = _solve_token_aligned(
        grammar=grammar,
        canvas=canvas_tokens,
        proposals=proposal_items,
        exactness_scope=exactness_scope,
        terminal_token_ids=terminal_token_ids,
        per_position_support=per_position_support,
    )
    represented_rows = _represented_support_rows(lexical)
    encoded_rows = json.dumps(
        [list(row) for row in represented_rows],
        separators=(",", ":"),
    ).encode("utf-8")
    diagnostics: dict[str, object] = {
        **dict(result.diagnostics),
        "support_kind": exactness_scope.kind.value,
        "represented_support_token_ids": [list(row) for row in represented_rows],
        "represented_support_row_sizes": [len(row) for row in represented_rows],
        "represented_support_sha256": hashlib.sha256(encoded_rows).hexdigest(),
    }
    return replace(result, diagnostics=diagnostics)


def _validate_scope_against_support(
    *,
    exactness_scope: ExactnessScope,
    canvas: tuple[int | None, ...],
    mapped_token_ids: frozenset[int],
    per_position_support: Sequence[Sequence[int]] | None,
) -> None:
    if exactness_scope.kind is SupportKind.FULL:
        if per_position_support is not None:
            raise ValueError(
                "FULL support is derived from the complete token mapping; "
                "per_position_support must be omitted"
            )
        expected = frozenset(range(exactness_scope.vocabulary_size))
        if mapped_token_ids != expected:
            missing = sorted(expected - mapped_token_ids)
            extra = sorted(mapped_token_ids - expected)
            raise ValueError(
                "FULL support requires the token-aligned terminal mapping to cover "
                f"every vocabulary token (missing={missing}, extra={extra})"
            )
        return

    if per_position_support is None:
        return
    for position, raw_support in enumerate(per_position_support):
        support = frozenset(raw_support)
        unmapped = sorted(support - mapped_token_ids)
        if unmapped:
            raise ValueError(
                f"support at position {position} contains token IDs without a "
                f"token-aligned terminal mapping: {unmapped}"
            )
        fixed_token_id = canvas[position]
        if fixed_token_id is not None and fixed_token_id not in support:
            raise ValueError(
                f"fixed canvas token at position {position} is absent from "
                "the represented support"
            )


def _represented_support_rows(
    lexical: LexicalRewardTable,
) -> tuple[tuple[int, ...], ...]:
    return tuple(
        tuple(
            sorted(
                lexical.terminal_token_ids[terminal_id]
                for terminal_id, reward in row.items()
                if reward.score != NEGATIVE_INFINITY
            )
        )
        for row in lexical.rows
    )
