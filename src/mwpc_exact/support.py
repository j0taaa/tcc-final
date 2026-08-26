"""Deterministic finite per-position token-support construction."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from enum import StrEnum
from math import isnan

from mwpc_exact.profiling import ComponentProfiler, ProfilingComponent
from mwpc_exact.types import ExactnessScope, Proposal, SupportKind, aggregate_proposals


class SupportInputSource(StrEnum):
    """Source from which represented token rows were constructed."""

    LOGITS = "logits"
    EXPLICIT = "explicit"


def _integer(value: object, field_name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{field_name} must be an integer")
    return value


def _token_id(value: object, field_name: str, vocabulary_size: int) -> int:
    token_id = _integer(value, field_name)
    if not 0 <= token_id < vocabulary_size:
        raise ValueError(f"{field_name} must be in [0, {vocabulary_size})")
    return token_id


def _token_id_tuple(
    value: object,
    field_name: str,
    *,
    vocabulary_size: int | None,
    allow_empty: bool,
    canonical_order: bool,
) -> tuple[int, ...]:
    if isinstance(value, (str, bytes)) or not isinstance(value, Iterable):
        raise TypeError(f"{field_name} must be an iterable of token IDs")
    result_items: list[int] = []
    for item in value:
        item_name = f"{field_name} item"
        if vocabulary_size is None:
            token_id = _integer(item, item_name)
            if token_id < 0:
                raise ValueError(f"{item_name} must be non-negative")
        else:
            token_id = _token_id(item, item_name, vocabulary_size)
        result_items.append(token_id)
    result = tuple(result_items)
    if not allow_empty and not result:
        raise ValueError(f"{field_name} must not be empty")
    if len(set(result)) != len(result):
        raise ValueError(f"{field_name} must not contain duplicate token IDs")
    return tuple(sorted(result)) if canonical_order else result


def _canonical_rows(
    rows: object,
    *,
    vocabulary_size: int | None,
    allow_empty_rows: bool,
) -> tuple[tuple[int, ...], ...]:
    if isinstance(rows, (str, bytes)) or not isinstance(rows, Sequence):
        raise TypeError("support rows must be a finite sequence")
    return tuple(
        _token_id_tuple(
            row,
            f"support row {position}",
            vocabulary_size=vocabulary_size,
            allow_empty=allow_empty_rows,
            canonical_order=True,
        )
        for position, row in enumerate(rows)
    )


def canonical_support_rows_json(rows: Sequence[Sequence[int]]) -> str:
    """Serialize represented rows with stable ordering and no whitespace."""

    canonical = _canonical_rows(rows, vocabulary_size=None, allow_empty_rows=True)
    return json.dumps([list(row) for row in canonical], separators=(",", ":"))


def support_rows_sha256(rows: Sequence[Sequence[int]]) -> str:
    """Return the SHA-256 fingerprint of canonical represented rows."""

    return hashlib.sha256(canonical_support_rows_json(rows).encode("utf-8")).hexdigest()


@dataclass(frozen=True, slots=True)
class SupportPolicy:
    """Validated construction policy and exactness metadata for one support."""

    kind: SupportKind
    vocabulary_size: int
    top_k: int | None = None
    adaptive_expansions: tuple[int, ...] = ()
    required_special_token_ids: tuple[int, ...] = ()
    include_proposal_tokens: bool = False
    permitted_token_ids: tuple[int, ...] | None = None
    pruning_description: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.kind, SupportKind):
            raise TypeError("kind must be a SupportKind")
        vocabulary_size = _integer(self.vocabulary_size, "vocabulary_size")
        if vocabulary_size <= 0:
            raise ValueError("vocabulary_size must be positive")
        if not isinstance(self.include_proposal_tokens, bool):
            raise TypeError("include_proposal_tokens must be a boolean")

        if self.permitted_token_ids is None:
            permitted = tuple(range(vocabulary_size))
        else:
            permitted = _token_id_tuple(
                self.permitted_token_ids,
                "permitted_token_ids",
                vocabulary_size=vocabulary_size,
                allow_empty=False,
                canonical_order=True,
            )
        specials = _token_id_tuple(
            self.required_special_token_ids,
            "required_special_token_ids",
            vocabulary_size=vocabulary_size,
            allow_empty=True,
            canonical_order=True,
        )
        unsupported_specials = sorted(set(specials) - set(permitted))
        if unsupported_specials:
            raise ValueError(
                "required special tokens are not permitted by the tokenizer policy: "
                f"{unsupported_specials}"
            )

        pruning_description = self.pruning_description
        if pruning_description is None:
            if self.kind is SupportKind.TOP_K:
                pruning_description = (
                    "model top-K over permitted token IDs plus configured required additions"
                )
            elif self.kind is SupportKind.EXPLICIT:
                pruning_description = (
                    "caller-provided per-position rows plus configured required additions"
                )

        scope = ExactnessScope(
            kind=self.kind,
            vocabulary_size=vocabulary_size,
            included_special_tokens=specials,
            top_k=self.top_k,
            adaptive_expansions=self.adaptive_expansions,
            pruning_description=pruning_description,
        )
        if scope.kind is SupportKind.TOP_K:
            effective_top_k = self._effective_top_k(scope)
            if effective_top_k > len(permitted):
                raise ValueError(
                    "the effective top-K width cannot exceed the permitted token count"
                )
            if effective_top_k == len(permitted):
                raise ValueError(
                    "TOP_K support must omit at least one permitted token; use FULL when "
                    "the effective width covers the permitted vocabulary"
                )

        object.__setattr__(self, "permitted_token_ids", permitted)
        object.__setattr__(self, "required_special_token_ids", specials)
        object.__setattr__(self, "adaptive_expansions", scope.adaptive_expansions)
        object.__setattr__(self, "top_k", scope.top_k)
        object.__setattr__(self, "pruning_description", pruning_description)

    @staticmethod
    def _effective_top_k(scope: ExactnessScope) -> int:
        if scope.top_k is None:
            raise AssertionError("TOP_K scope was validated without top_k")
        if scope.adaptive_expansions:
            return scope.adaptive_expansions[-1]
        return scope.top_k

    @property
    def effective_top_k(self) -> int | None:
        """Return the width represented by this attempt, including expansion."""

        scope = self.exactness_scope
        if scope.kind is not SupportKind.TOP_K:
            return None
        return self._effective_top_k(scope)

    @property
    def exactness_scope(self) -> ExactnessScope:
        """Return independently validated public scope metadata."""

        return ExactnessScope(
            kind=self.kind,
            vocabulary_size=self.vocabulary_size,
            included_special_tokens=self.required_special_token_ids,
            top_k=self.top_k,
            adaptive_expansions=self.adaptive_expansions,
            pruning_description=self.pruning_description,
        )


@dataclass(frozen=True, slots=True)
class PerPositionSupport:
    """Immutable represented token rows with replayable support diagnostics."""

    canvas: tuple[int | None, ...]
    rows: tuple[tuple[int, ...], ...]
    permitted_token_ids: tuple[int, ...]
    exactness_scope: ExactnessScope
    input_source: SupportInputSource
    top_k_token_ids_by_position: tuple[tuple[int, ...], ...]
    proposal_token_ids_by_position: tuple[tuple[int, ...], ...]
    proposal_token_inclusion_enabled: bool

    def __post_init__(self) -> None:
        if not isinstance(self.exactness_scope, ExactnessScope):
            raise TypeError("exactness_scope must be an ExactnessScope")
        if not isinstance(self.input_source, SupportInputSource):
            raise TypeError("input_source must be a SupportInputSource")
        if not isinstance(self.proposal_token_inclusion_enabled, bool):
            raise TypeError("proposal_token_inclusion_enabled must be a boolean")

        vocabulary_size = self.exactness_scope.vocabulary_size
        canvas = _canvas(self.canvas, vocabulary_size=vocabulary_size)
        rows = _canonical_rows(
            self.rows,
            vocabulary_size=vocabulary_size,
            allow_empty_rows=False,
        )
        permitted = _token_id_tuple(
            self.permitted_token_ids,
            "permitted_token_ids",
            vocabulary_size=vocabulary_size,
            allow_empty=False,
            canonical_order=True,
        )
        top_k_rows = _indexed_token_rows(
            self.top_k_token_ids_by_position,
            field_name="top_k_token_ids_by_position",
            slot_count=len(canvas),
            vocabulary_size=vocabulary_size,
        )
        proposal_rows = _indexed_token_rows(
            self.proposal_token_ids_by_position,
            field_name="proposal_token_ids_by_position",
            slot_count=len(canvas),
            vocabulary_size=vocabulary_size,
        )
        if len(rows) != len(canvas):
            raise ValueError("support rows and canvas must have equal length")

        permitted_set = set(permitted)
        specials = set(self.exactness_scope.included_special_tokens)
        if not specials <= permitted_set:
            raise ValueError("exactness-scope special tokens must be permitted")
        for position, (fixed_token, row) in enumerate(zip(canvas, rows, strict=True)):
            row_set = set(row)
            if not row_set <= permitted_set:
                unsupported = sorted(row_set - permitted_set)
                raise ValueError(
                    f"support row {position} contains non-permitted token IDs: {unsupported}"
                )
            if fixed_token is not None:
                if row != (fixed_token,):
                    raise ValueError(
                        f"fixed position {position} support must contain exactly token "
                        f"{fixed_token}"
                    )
                if top_k_rows[position]:
                    raise ValueError("fixed positions cannot contain ranked top-K tokens")
            else:
                missing_specials = sorted(specials - row_set)
                if missing_specials:
                    raise ValueError(
                        f"masked support row {position} omits required special tokens: "
                        f"{missing_specials}"
                    )

        kind = self.exactness_scope.kind
        if kind is SupportKind.FULL:
            for position, fixed_token in enumerate(canvas):
                if fixed_token is None and rows[position] != permitted:
                    raise ValueError(
                        f"FULL support row {position} must contain every permitted token"
                    )
        if kind is SupportKind.TOP_K:
            if self.input_source is not SupportInputSource.LOGITS:
                raise ValueError("TOP_K support must be constructed from logits")
            effective_k = self.effective_top_k
            if effective_k is None:
                raise AssertionError("TOP_K scope has no effective width")
            for position, fixed_token in enumerate(canvas):
                if fixed_token is None:
                    if len(top_k_rows[position]) != effective_k:
                        raise ValueError(
                            f"top-K row {position} must contain exactly {effective_k} tokens"
                        )
                    if not set(top_k_rows[position]) <= set(rows[position]):
                        raise ValueError("ranked top-K tokens must be represented in support")
        elif any(top_k_rows):
            raise ValueError("only TOP_K support may carry ranked top-K diagnostics")
        if kind is SupportKind.EXPLICIT and self.input_source is not SupportInputSource.EXPLICIT:
            raise ValueError("EXPLICIT support must be constructed from an explicit map")

        if self.proposal_token_inclusion_enabled:
            for position, proposal_tokens in enumerate(proposal_rows):
                if not set(proposal_tokens) <= set(rows[position]):
                    raise ValueError("configured proposal tokens must be represented in support")
        elif any(proposal_rows):
            raise ValueError("proposal token diagnostics require proposal inclusion to be enabled")

        object.__setattr__(self, "canvas", canvas)
        object.__setattr__(self, "rows", rows)
        object.__setattr__(self, "permitted_token_ids", permitted)
        object.__setattr__(self, "top_k_token_ids_by_position", top_k_rows)
        object.__setattr__(self, "proposal_token_ids_by_position", proposal_rows)

    @property
    def effective_top_k(self) -> int | None:
        """Return the current represented top-K width."""

        if self.exactness_scope.kind is not SupportKind.TOP_K:
            return None
        if self.exactness_scope.adaptive_expansions:
            return self.exactness_scope.adaptive_expansions[-1]
        return self.exactness_scope.top_k

    @property
    def canonical_rows_json(self) -> str:
        """Return the canonical serialized represented rows."""

        return canonical_support_rows_json(self.rows)

    @property
    def fingerprint(self) -> str:
        """Return the canonical represented-row SHA-256 digest."""

        return support_rows_sha256(self.rows)

    @property
    def permitted_token_ids_sha256(self) -> str:
        """Fingerprint the semantic token universe independently from rows."""

        encoded = json.dumps(list(self.permitted_token_ids), separators=(",", ":")).encode("utf-8")
        return hashlib.sha256(encoded).hexdigest()

    @property
    def diagnostics(self) -> dict[str, object]:
        """Return machine-readable construction diagnostics."""

        return {
            "input_source": self.input_source.value,
            "tie_break": (
                "score_descending_then_token_id_ascending"
                if self.input_source is SupportInputSource.LOGITS
                else "canonical_token_id_ascending"
            ),
            "effective_top_k": self.effective_top_k,
            "configured_required_special_token_ids": list(
                self.exactness_scope.included_special_tokens
            ),
            "proposal_token_inclusion_enabled": self.proposal_token_inclusion_enabled,
            "proposal_token_ids_by_position": [
                list(row) for row in self.proposal_token_ids_by_position
            ],
            "top_k_token_ids_by_position": [list(row) for row in self.top_k_token_ids_by_position],
            "fixed_positions": [
                position for position, token_id in enumerate(self.canvas) if token_id is not None
            ],
            "permitted_token_count": len(self.permitted_token_ids),
            "permitted_token_ids_sha256": self.permitted_token_ids_sha256,
            "represented_support_row_sizes": [len(row) for row in self.rows],
            "represented_support_canonical_json": self.canonical_rows_json,
            "represented_support_sha256": self.fingerprint,
        }

    def to_dict(self) -> dict[str, object]:
        """Serialize rows, exactness scope, and diagnostics for replay."""

        return {
            "per_position_support": [list(row) for row in self.rows],
            "permitted_token_ids": list(self.permitted_token_ids),
            "exactness_scope": self.exactness_scope.to_dict(),
            "diagnostics": self.diagnostics,
        }


def _canvas(value: object, *, vocabulary_size: int) -> tuple[int | None, ...]:
    if isinstance(value, (str, bytes)) or not isinstance(value, Sequence):
        raise TypeError("canvas must be a finite sequence of token IDs or None")
    canvas: list[int | None] = []
    for position, item in enumerate(value):
        if item is None:
            canvas.append(None)
        else:
            canvas.append(_token_id(item, f"canvas token at position {position}", vocabulary_size))
    return tuple(canvas)


def _indexed_token_rows(
    value: object,
    *,
    field_name: str,
    slot_count: int,
    vocabulary_size: int,
) -> tuple[tuple[int, ...], ...]:
    if isinstance(value, (str, bytes)) or not isinstance(value, Sequence):
        raise TypeError(f"{field_name} must be a finite sequence")
    if len(value) != slot_count:
        raise ValueError(f"{field_name} and canvas must have equal length")
    return tuple(
        _token_id_tuple(
            row,
            f"{field_name} row {position}",
            vocabulary_size=vocabulary_size,
            allow_empty=True,
            canonical_order=False,
        )
        for position, row in enumerate(value)
    )


def _validate_proposals(
    proposals: Iterable[Proposal],
    *,
    canvas: tuple[int | None, ...],
    vocabulary_size: int,
    permitted_token_ids: frozenset[int],
) -> tuple[Proposal, ...]:
    proposal_items = tuple(proposals)
    aggregate_proposals(proposal_items)
    for proposal in proposal_items:
        if proposal.position >= len(canvas):
            raise ValueError(
                f"proposal {proposal.proposal_id} position is outside the finite canvas"
            )
        _token_id(proposal.token_id, f"proposal {proposal.proposal_id} token_id", vocabulary_size)
        if proposal.token_id not in permitted_token_ids:
            raise ValueError(
                f"proposal {proposal.proposal_id} uses a non-permitted token ID: "
                f"{proposal.token_id}"
            )
        fixed_token = canvas[proposal.position]
        if fixed_token is not None and proposal.token_id != fixed_token:
            raise ValueError(
                f"proposal {proposal.proposal_id} conflicts with fixed canvas token "
                f"at position {proposal.position}"
            )
    return proposal_items


def _logit_matrix(
    value: object,
    *,
    slot_count: int,
    vocabulary_size: int,
) -> tuple[tuple[float, ...], ...]:
    if isinstance(value, (str, bytes)) or not isinstance(value, Sequence):
        raise TypeError("logits must be a finite position-by-vocabulary sequence")
    if len(value) != slot_count:
        raise ValueError("logits and canvas must have equal position counts")
    rows: list[tuple[float, ...]] = []
    for position, raw_row in enumerate(value):
        if isinstance(raw_row, (str, bytes)) or not isinstance(raw_row, Sequence):
            raise TypeError(f"logit row {position} must be a finite sequence")
        if len(raw_row) != vocabulary_size:
            raise ValueError(f"logit row {position} must contain exactly {vocabulary_size} scores")
        row: list[float] = []
        for token_id, raw_score in enumerate(raw_row):
            if isinstance(raw_score, bool) or not isinstance(raw_score, (int, float)):
                raise TypeError(f"logit at position {position}, token {token_id} must be real")
            score = float(raw_score)
            if isnan(score):
                raise ValueError(f"logit at position {position}, token {token_id} must not be NaN")
            row.append(score)
        rows.append(tuple(row))
    return tuple(rows)


def _explicit_rows(
    value: object,
    *,
    slot_count: int,
    vocabulary_size: int,
) -> tuple[tuple[int, ...], ...]:
    if not isinstance(value, Mapping):
        raise TypeError("explicit_support must be a mapping from positions to token rows")
    normalized: dict[int, object] = {}
    for raw_position, raw_row in value.items():
        position = _integer(raw_position, "explicit support position")
        if position in normalized:
            raise ValueError(f"duplicate explicit support position: {position}")
        normalized[position] = raw_row
    expected_positions = set(range(slot_count))
    actual_positions = set(normalized)
    if actual_positions != expected_positions:
        missing = sorted(expected_positions - actual_positions)
        extra = sorted(actual_positions - expected_positions)
        raise ValueError(
            "explicit_support must define exactly every canvas position "
            f"(missing={missing}, extra={extra})"
        )
    return tuple(
        _token_id_tuple(
            normalized[position],
            f"explicit support row {position}",
            vocabulary_size=vocabulary_size,
            allow_empty=True,
            canonical_order=True,
        )
        for position in range(slot_count)
    )


def _build_per_position_support(
    *,
    canvas: Sequence[int | None],
    policy: SupportPolicy,
    logits: Sequence[Sequence[float]] | None = None,
    explicit_support: Mapping[int, Sequence[int]] | None = None,
    proposals: Iterable[Proposal] = (),
) -> PerPositionSupport:
    """Construct deterministic support from logits or explicit position rows.

    Exactly one input source is required. ``TOP_K`` requires logits,
    ``EXPLICIT`` requires an explicit map, and ``FULL`` accepts either while
    validating complete coverage. Fixed slots are never widened.
    """

    if not isinstance(policy, SupportPolicy):
        raise TypeError("policy must be a SupportPolicy")
    if (logits is None) == (explicit_support is None):
        raise ValueError("provide exactly one of logits or explicit_support")
    if policy.kind is SupportKind.TOP_K and logits is None:
        raise ValueError("TOP_K support must be constructed from logits")
    if policy.kind is SupportKind.EXPLICIT and explicit_support is None:
        raise ValueError("EXPLICIT support must be constructed from an explicit map")

    canvas_tokens = _canvas(canvas, vocabulary_size=policy.vocabulary_size)
    permitted = policy.permitted_token_ids
    if permitted is None:
        raise AssertionError("SupportPolicy did not normalize permitted_token_ids")
    permitted_set = frozenset(permitted)
    for position, fixed_token in enumerate(canvas_tokens):
        if fixed_token is not None and fixed_token not in permitted_set:
            raise ValueError(
                f"fixed canvas token at position {position} is not permitted: {fixed_token}"
            )
    proposal_items = _validate_proposals(
        proposals,
        canvas=canvas_tokens,
        vocabulary_size=policy.vocabulary_size,
        permitted_token_ids=permitted_set,
    )
    proposal_tokens: list[set[int]] = [set() for _ in canvas_tokens]
    if policy.include_proposal_tokens:
        for proposal in proposal_items:
            proposal_tokens[proposal.position].add(proposal.token_id)

    top_k_rows: list[tuple[int, ...]] = [() for _ in canvas_tokens]
    if logits is not None:
        scores = _logit_matrix(
            logits,
            slot_count=len(canvas_tokens),
            vocabulary_size=policy.vocabulary_size,
        )
        base_rows: list[tuple[int, ...]] = []
        for position, fixed_token in enumerate(canvas_tokens):
            if fixed_token is not None:
                base_rows.append((fixed_token,))
                continue
            if policy.kind is SupportKind.TOP_K:
                effective_k = policy.effective_top_k
                if effective_k is None:
                    raise AssertionError("TOP_K policy has no effective width")
                ranked = tuple(
                    sorted(permitted, key=lambda token_id: (-scores[position][token_id], token_id))[
                        :effective_k
                    ]
                )
                top_k_rows[position] = ranked
                base_rows.append(tuple(sorted(ranked)))
            else:
                base_rows.append(permitted)
        input_source = SupportInputSource.LOGITS
    else:
        if explicit_support is None:
            raise AssertionError("input source validation lost explicit_support")
        base_rows = list(
            _explicit_rows(
                explicit_support,
                slot_count=len(canvas_tokens),
                vocabulary_size=policy.vocabulary_size,
            )
        )
        input_source = SupportInputSource.EXPLICIT

    represented_rows: list[tuple[int, ...]] = []
    required_specials = set(policy.required_special_token_ids)
    for position, (fixed_token, base_row) in enumerate(zip(canvas_tokens, base_rows, strict=True)):
        if fixed_token is not None:
            if base_row != (fixed_token,):
                raise ValueError(
                    f"fixed position {position} explicit support must contain exactly "
                    f"token {fixed_token}"
                )
            represented_rows.append((fixed_token,))
            continue
        row = set(base_row)
        if not row <= permitted_set:
            unsupported = sorted(row - permitted_set)
            raise ValueError(
                f"support at position {position} contains non-permitted token IDs: {unsupported}"
            )
        row.update(required_specials)
        row.update(proposal_tokens[position])
        if not row:
            raise ValueError(f"masked support row {position} must not be empty")
        represented_rows.append(tuple(sorted(row)))

    proposal_rows = tuple(
        tuple(sorted(tokens)) if policy.include_proposal_tokens else ()
        for tokens in proposal_tokens
    )
    return PerPositionSupport(
        canvas=canvas_tokens,
        rows=tuple(represented_rows),
        permitted_token_ids=permitted,
        exactness_scope=policy.exactness_scope,
        input_source=input_source,
        top_k_token_ids_by_position=tuple(top_k_rows),
        proposal_token_ids_by_position=proposal_rows,
        proposal_token_inclusion_enabled=policy.include_proposal_tokens,
    )


def build_per_position_support(
    *,
    canvas: Sequence[int | None],
    policy: SupportPolicy,
    logits: Sequence[Sequence[float]] | None = None,
    explicit_support: Mapping[int, Sequence[int]] | None = None,
    proposals: Iterable[Proposal] = (),
    profiler: ComponentProfiler | None = None,
) -> PerPositionSupport:
    """Construct deterministic support from logits or explicit position rows.

    Exactly one input source is required. ``TOP_K`` requires logits,
    ``EXPLICIT`` requires an explicit map, and ``FULL`` accepts either while
    validating complete coverage. Fixed slots are never widened. When
    supplied, the optional profiler records only support construction.
    """

    if profiler is not None and not isinstance(profiler, ComponentProfiler):
        raise TypeError("profiler must be a ComponentProfiler or None")
    if profiler is None or not profiler.enabled:
        return _build_per_position_support(
            canvas=canvas,
            policy=policy,
            logits=logits,
            explicit_support=explicit_support,
            proposals=proposals,
        )
    with profiler.measure(ProfilingComponent.SUPPORT_CONSTRUCTION):
        support = _build_per_position_support(
            canvas=canvas,
            policy=policy,
            logits=logits,
            explicit_support=explicit_support,
            proposals=proposals,
        )
    row_sizes = tuple(len(row) for row in support.rows)
    profiler.set_support_row_sizes(row_sizes)
    profiler.set_counter("support_slot_count", len(row_sizes))
    profiler.set_counter("support_alternative_count", sum(row_sizes))
    profiler.set_counter("support_max_row_size", max(row_sizes, default=0))
    profiler.set_counter("support_attempt_count", 1)
    return support
