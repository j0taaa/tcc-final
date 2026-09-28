"""Certified finite-slot JSON repair. No model, tokenizer download, or new parser.

The objective is weighted token substitution, not unrestricted edit distance.
The supplied grammar defines feasibility; JSON/duplicate-key checks can abstain,
but never silently add constraints to an optimality claim.
"""

from __future__ import annotations

import argparse
import json
from collections.abc import Sequence
from dataclasses import dataclass, replace
from itertools import islice, product
from math import fsum, isfinite
from time import perf_counter
from typing import Any

from mwpc_exact import (
    CompositionalByteLevelAdapter,
    EOSMode,
    EOSPolicy,
    ExactBackend,
    Proposal,
    SelectionInput,
    SelectionResult,
    SelectionStatus,
    SupportKind,
    SupportPolicy,
    build_per_position_support,
    select_exact_mwpc,
    select_greedy_exact_feasibility,
)
from mwpc_exact.profiling import ComponentProfiler
from mwpc_exact.reference.byte_grammars import lower_ascii_json_value_subset_v1_source
from mwpc_exact.reference.grammar import CnfGrammar, Nonterminal, Terminal
from mwpc_exact.reference.normalization import (
    NonterminalRef,
    SourceGrammar,
    SourceProduction,
    TerminalRef,
    normalize_to_cnf,
)

BYTE_ADAPTER = CompositionalByteLevelAdapter(tuple(bytes((i,)) for i in range(256)))
STRUCTURAL_ALTERNATIVES = {ord(a): ord(b) for a, b in zip("{}[],:", "[]{}:,", strict=True)}


def json_repair_grammar(*, root_object: bool = False, record_schema: bool = False) -> CnfGrammar:
    """Recursive integer JSON: ASCII/escaped strings, whitespace, no floats.

    Independent ``json.loads`` validation additionally rejects duplicate keys;
    key uniqueness is not represented by this CFG.
    """
    base = lower_ascii_json_value_subset_v1_source()
    nts = list(base.nonterminals)
    terms = list(base.terminals)
    names = {n.name: n.symbol_id for n in nts}
    byte_ids = {t.label: t.symbol_id for t in terms}
    for name in ("WS", "Atom", "Unsigned", "Hex", "Root", "Record", "Records", "RecordList"):
        names[name] = len(nts)
        nts.append(Nonterminal(names[name], name))
    rules: list[SourceProduction] = []

    def add(head: str, *body: str | bytes) -> None:
        refs: list[NonterminalRef | TerminalRef] = []
        for part in body:
            if isinstance(part, str):
                refs.append(NonterminalRef(names[part]))
            else:
                for byte in part:
                    if byte not in byte_ids:
                        byte_ids[byte] = len(terms)
                        terms.append(Terminal(byte_ids[byte], byte))
                    refs.append(TerminalRef(byte_ids[byte]))
        rules.append(SourceProduction(len(rules), names[head], tuple(refs)))

    for rule in base.productions:
        head = rule.head_id
        if head == names["Value"]:
            head = names["Atom"]
        elif head == names["Integer"]:
            head = names["Unsigned"]
        rules.append(SourceProduction(len(rules), head, rule.body))
    add("Value", "WS", "Atom", "WS")
    add("Integer", "Unsigned")
    add("Integer", b"-", "Unsigned")
    add("WS")
    for byte in b" \t\r\n":
        add("WS", bytes((byte,)), "WS")
    # Whitespace around object keys/separators and inside empty containers.
    add("Member", "WS", "String", "WS", b":", "Value")
    add("Array", b"[", "WS", b"]")
    add("Object", b"{", "WS", b"}")
    add("Object", b"{", "Members", "WS", b"}")
    for byte in range(32, 127):
        if byte not in b'"\\' and not (97 <= byte <= 122 or 48 <= byte <= 57 or byte == 32):
            add("Character", bytes((byte,)))
    for byte in b'"\\/bfnrt':
        add("Character", b"\\", bytes((byte,)))
    for byte in b"0123456789abcdefABCDEF":
        add("Hex", bytes((byte,)))
    add("Character", b"\\u", "Hex", "Hex", "Hex", "Hex")
    if record_schema:
        # Fixed shared schema and key order, never instance-specific answer values.
        add("Record", b'{"a":', "Integer", b',"b":', "Integer", b"}")
        add("Records", "Record")
        add("Records", "Records", b",", "Record")
        add("RecordList", b"[]")
        add("RecordList", b"[", "Records", b"]")
        add("Root", b'{"id":', "Integer", b',"payload":', "RecordList", b"}")
    else:
        add("Root", "WS", "Object" if root_object else "Value", "WS")
    return normalize_to_cnf(
        reachable_source(SourceGrammar(tuple(nts), tuple(terms), names["Root"], tuple(rules)))
    ).grammar


def reachable_source(source: SourceGrammar) -> SourceGrammar:
    """Remove only symbols unreachable from the start; preserve its entire language.

    Every node in a start derivation is reachable by following production bodies.
    Thus no start derivation can use a removed rule; all retained rules are original.
    This does not prune any token alternatives or chart paths.
    """
    reached = {source.start_nonterminal_id}
    while True:
        expanded = reached | {
            symbol.symbol_id
            for rule in source.productions
            if rule.head_id in reached
            for symbol in rule.body
            if isinstance(symbol, NonterminalRef)
        }
        if expanded == reached:
            break
        reached = expanded
    rules = tuple(rule for rule in source.productions if rule.head_id in reached)
    terminals = {
        symbol.symbol_id
        for rule in rules
        for symbol in rule.body
        if isinstance(symbol, TerminalRef)
    }
    return SourceGrammar(
        tuple(n for n in source.nonterminals if n.symbol_id in reached),
        tuple(t for t in source.terminals if t.symbol_id in terminals),
        source.start_nonterminal_id,
        rules,
    )


def strict_json_loads(text: str) -> Any:
    """Independent syntax/duplicate-key check, not a semantic correctness oracle."""

    def object_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in pairs:
            if key in result:
                raise ValueError(f"duplicate JSON key: {key}")
            result[key] = value
        return result

    def invalid_constant(value: str) -> None:
        raise ValueError(f"non-JSON numeric constant: {value}")

    return json.loads(text, object_pairs_hook=object_pairs, parse_constant=invalid_constant)


def structural_byte_support(text: str) -> tuple[tuple[int, ...], ...]:
    """Swap container kind or comma/colon outside strings; no answer is consulted."""
    quoted = False
    escaped = False
    rows = []
    for byte in text.encode("utf-8"):
        alternate = STRUCTURAL_ALTERNATIVES.get(byte) if not quoted else None
        rows.append((byte,) if alternate is None else (byte, alternate))
        if escaped:
            escaped = False
        elif quoted and byte == 92:
            escaped = True
        elif byte == 34:
            quoted = not quoted
    return tuple(rows)


def structural_token_support(
    draft_token_ids: Sequence[int],
    adapter: CompositionalByteLevelAdapter,
    *,
    max_variants_per_token: int = 32,
) -> tuple[tuple[int, ...], ...]:
    """Same-byte-length structural replacements present in a real vocabulary.

    Enumerates at most the declared prefix of the Cartesian byte alternatives.
    This is explicit support pruning, never a full-vocabulary guarantee.
    """
    if isinstance(max_variants_per_token, bool) or not isinstance(max_variants_per_token, int):
        raise TypeError("max_variants_per_token must be an integer")
    if max_variants_per_token < 1:
        raise ValueError("max_variants_per_token must be positive")
    by_bytes: dict[bytes, list[int]] = {}
    for token, emission in enumerate(adapter.emissions):
        if emission is not None:
            by_bytes.setdefault(emission, []).append(token)
    raw = adapter.detokenize_bytes(draft_token_ids)
    byte_rows = structural_byte_support(raw.decode("utf-8"))
    offset = 0
    rows = []
    for token in draft_token_ids:
        size = len(adapter.token_bytes(token))
        choices = [token]
        for variant in islice(product(*byte_rows[offset : offset + size]), max_variants_per_token):
            choices.extend(by_bytes.get(bytes(variant), ()))
        rows.append(tuple(dict.fromkeys(choices)))
        offset += size
    return tuple(rows)


@dataclass(frozen=True)
class RepairResult:
    status: SelectionStatus
    output_text: str | None
    substitution_cost: float | None
    changed_positions: tuple[int, ...]
    protected_positions: tuple[int, ...]
    elapsed_seconds: float
    selection: SelectionResult | None
    support_specification: dict[str, object]
    detail: str = ""

    def to_dict(self) -> dict[str, object]:
        return {
            "status": self.status.value,
            "output_text": self.output_text,
            "substitution_cost": self.substitution_cost,
            "changed_positions": list(self.changed_positions),
            "protected_positions": list(self.protected_positions),
            "elapsed_seconds": self.elapsed_seconds,
            "certificate": self.selection.to_dict() if self.selection else None,
            "support_specification": self.support_specification,
            "detail": self.detail,
        }


def prepare_repair(
    draft_token_ids: Sequence[int],
    *,
    adapter: CompositionalByteLevelAdapter,
    grammar: CnfGrammar,
    alternatives: Sequence[Sequence[int]],
    protected_byte_spans: Sequence[tuple[int, int]] = (),
    weights: Sequence[float] | None = None,
) -> tuple[SelectionInput, tuple[int, ...]]:
    """Freeze every token intersecting a protected half-open byte interval."""
    ids = tuple(draft_token_ids)
    if not ids or len(ids) != len(alternatives):
        raise ValueError("draft and alternatives must have equal, positive slot counts")
    for row in alternatives:
        for token_id in row:
            adapter.token_bytes(token_id)
    raw = adapter.detokenize_bytes(ids)
    spans = tuple(protected_byte_spans)
    for start, end in spans:
        if any(isinstance(v, bool) or not isinstance(v, int) for v in (start, end)):
            raise TypeError("protected byte offsets must be integers")
        if not 0 <= start < end <= len(raw):
            raise ValueError("protected span must be nonempty and inside draft bytes")
    if weights is None:
        weights = (1.0,) * len(ids)
    if len(weights) != len(ids):
        raise ValueError("weights must have one entry per slot")
    proposals = tuple(
        Proposal(i, i, token, weight)
        for i, (token, weight) in enumerate(zip(ids, weights, strict=True))
    )
    locked = []
    offset = 0
    for position, token in enumerate(ids):
        end = offset + len(adapter.detokenize_bytes((token,)))
        if any(offset < b and end > a for a, b in spans):
            locked.append(position)
        offset = end
    canvas = tuple(token if i in locked else None for i, token in enumerate(ids))
    support = build_per_position_support(
        canvas=canvas,
        policy=SupportPolicy(
            kind=SupportKind.EXPLICIT,
            vocabulary_size=adapter.vocabulary_size,
            pruning_description=(
                "repair: original plus caller alternatives; whole-token byte locks; "
                "fixed slots; no EOS"
            ),
        ),
        explicit_support={
            i: (token,) if i in locked else tuple(dict.fromkeys((token, *alternatives[i])))
            for i, token in enumerate(ids)
        },
        proposals=proposals,
    )
    return SelectionInput(
        grammar, canvas, proposals, support, adapter, EOSPolicy(EOSMode.ABSENT)
    ), tuple(locked)


def repair_tokens(
    draft_token_ids: Sequence[int],
    *,
    adapter: CompositionalByteLevelAdapter,
    grammar: CnfGrammar,
    alternatives: Sequence[Sequence[int]],
    protected_byte_spans: Sequence[tuple[int, int]] = (),
    weights: Sequence[float] | None = None,
    method: str = "exact",
    backend: ExactBackend = ExactBackend.RUST,
    timeout_seconds: float = 2.0,
    profiler: ComponentProfiler | None = None,
) -> RepairResult:
    """Return a checked repair or explicit abstention; timeout covers preparation too.

    This cooperative deadline detects late results. A hard resource ceiling needs
    a supervised process (used by the experiment runner), especially for Python.
    """
    if method not in ("exact", "greedy"):
        raise ValueError("method must be exact or greedy")
    if isinstance(timeout_seconds, bool) or not isinstance(timeout_seconds, (float, int)):
        raise TypeError("timeout_seconds must be a real number")
    if not isfinite(timeout_seconds) or timeout_seconds < 0:
        raise ValueError("timeout_seconds must be finite and non-negative")
    started = perf_counter()
    state, locked = prepare_repair(
        draft_token_ids,
        adapter=adapter,
        grammar=grammar,
        alternatives=alternatives,
        protected_byte_spans=protected_byte_spans,
        weights=weights,
    )

    support_spec = {
        **state.support.exactness_scope.to_dict(),
        "rows": [list(row) for row in state.support.rows],
        "original_token_ids": list(draft_token_ids),
        "weights": [p.weight for p in state.proposals],
    }

    def failure(status: SelectionStatus, detail: str) -> RepairResult:
        return RepairResult(
            status, None, None, (), locked, perf_counter() - started, None, support_spec, detail
        )

    remaining = timeout_seconds - (perf_counter() - started)
    if remaining <= 0:
        return failure(SelectionStatus.TIMEOUT, "preparation exceeded total deadline")
    if method == "exact":
        selected = select_exact_mwpc(
            state,
            backend=backend,
            profiler=profiler,
            timeout_seconds=remaining if backend is ExactBackend.RUST else None,
        )
    else:
        selected = select_greedy_exact_feasibility(
            state,
            backend=backend,
            total_timeout_seconds=remaining,
            reuse_witness=True,
            profiler=profiler,
        )
    if perf_counter() - started >= timeout_seconds:
        return failure(SelectionStatus.TIMEOUT, "total deadline exceeded")
    if selected.status not in (SelectionStatus.OPTIMAL, SelectionStatus.FEASIBLE_ON_SUPPORT):
        return failure(selected.status, str(dict(selected.diagnostics)))
    try:
        text = adapter.detokenize_bytes(selected.witness_token_ids).decode("utf-8")
        strict_json_loads(text)
    except (ValueError, UnicodeError) as exc:
        return failure(
            SelectionStatus.UNSUPPORTED, f"CFG witness rejected by additional JSON check: {exc}"
        )
    changes = tuple(
        i
        for i, (before, after) in enumerate(
            zip(draft_token_ids, selected.witness_token_ids, strict=True)
        )
        if before != after
    )
    try:
        cost = fsum(state.proposals[i].weight for i in changes)
    except OverflowError:
        return failure(SelectionStatus.ERROR, "substitution cost exceeds float range")
    if any(i in locked for i in changes):
        return failure(SelectionStatus.ERROR, "protected token changed")
    if perf_counter() - started >= timeout_seconds:
        return failure(SelectionStatus.TIMEOUT, "final validation exceeded total deadline")
    return RepairResult(
        selected.status,
        text,
        cost,
        changes,
        locked,
        perf_counter() - started,
        selected,
        support_spec,
    )


def repair_json_text(
    text: str,
    *,
    protected_byte_spans: Sequence[tuple[int, int]] = (),
    method: str = "exact",
    backend: ExactBackend = ExactBackend.RUST,
    timeout_seconds: float = 2.0,
    record_schema: bool = False,
) -> RepairResult:
    """Convenience byte-token profile, structurally restricted and model-free."""
    if isinstance(timeout_seconds, bool) or not isinstance(timeout_seconds, (float, int)):
        raise TypeError("timeout_seconds must be a real number")
    if not isfinite(timeout_seconds) or timeout_seconds < 0:
        raise ValueError("timeout_seconds must be finite and non-negative")
    started = perf_counter()
    grammar = json_repair_grammar(record_schema=record_schema)
    support = structural_byte_support(text)
    remaining = max(0.0, timeout_seconds - (perf_counter() - started))
    result = repair_tokens(
        tuple(text.encode("utf-8")),
        adapter=BYTE_ADAPTER,
        grammar=grammar,
        alternatives=support,
        protected_byte_spans=protected_byte_spans,
        method=method,
        backend=backend,
        timeout_seconds=remaining,
    )
    return replace(result, elapsed_seconds=perf_counter() - started)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("text", help="JSON draft, or - to read stdin")
    parser.add_argument("--method", choices=("exact", "greedy"), default="exact")
    parser.add_argument("--backend", choices=("rust", "python"), default="rust")
    parser.add_argument("--timeout", type=float, default=2.0)
    parser.add_argument("--profile", choices=("json", "records"), default="json")
    parser.add_argument(
        "--protect",
        action="append",
        default=[],
        metavar="START:END",
        help="half-open UTF-8 byte interval; repeatable",
    )
    args = parser.parse_args()
    import sys

    text = sys.stdin.read() if args.text == "-" else args.text
    spans = tuple(tuple(map(int, item.split(":"))) for item in args.protect)
    if any(len(span) != 2 for span in spans):
        parser.error("--protect requires START:END")
    result = repair_json_text(
        text,
        protected_byte_spans=[(s[0], s[1]) for s in spans],
        method=args.method,
        backend=ExactBackend(args.backend),
        timeout_seconds=args.timeout,
        record_schema=args.profile == "records",
    )
    print(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))
    if result.output_text is None:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
