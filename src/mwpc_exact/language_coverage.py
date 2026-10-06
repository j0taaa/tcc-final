"""Independent finite-language support coverage, including all token aliases.

Closed yield sets upper-bound CFG languages by derivation induction. If every
full-vocabulary finite-slot tokenization of these yields is represented, no
valid probability is omitted. Productive recursive languages may have no finite
certificate; refusing coverage does not block the general mass envelope.
"""

from __future__ import annotations

from collections.abc import Iterable

from mwpc_exact.eos_policy import EOSMode
from mwpc_exact.evaluation._serde import _integer, _mapping, _sequence, _string
from mwpc_exact.reference.grammar import CnfGrammar
from mwpc_exact.state import SelectionInput


def tokenizations(
    state: SelectionInput, words: Iterable[bytes], *, max_paths: int = 100000
) -> tuple[tuple[int, ...], ...]:
    """Enumerate full-vocabulary paths for a finite byte language (ABSENT EOS).

    A limit raises explicitly, never returns an incomplete claimed coverage.
    """
    if state.eos_policy.mode is not EOSMode.ABSENT:
        raise ValueError("finite language coverage currently requires ABSENT EOS")
    by_first: dict[int, list[tuple[int, bytes]]] = {}
    for token, emission in enumerate(state.tokenizer_adapter.emissions):
        if emission is not None:
            by_first.setdefault(emission[0], []).append((token, emission))
    paths: set[tuple[int, ...]] = set()
    visited = 0
    for word in words:

        def visit(offset: int, prefix: tuple[int, ...], word: bytes = word) -> None:
            nonlocal visited
            visited += 1
            if visited > 1_000_000:
                raise ValueError("tokenization coverage exceeds search-node limit")
            if len(prefix) == len(state.canvas):
                if offset == len(word):
                    paths.add(prefix)
                    if len(paths) > max_paths:
                        raise ValueError("full-vocabulary tokenization coverage exceeds path limit")
                return
            if offset == len(word):
                return
            fixed = state.canvas[len(prefix)]
            for token, emission in by_first.get(word[offset], []):
                if (fixed is None or token == fixed) and word.startswith(emission, offset):
                    visit(offset + len(emission), (*prefix, token))

        visit(0, ())
    return tuple(sorted(paths))


def check_language_coverage(state: SelectionInput, value: object) -> tuple[bytes, ...]:
    data = _mapping(value, "language coverage")
    if _integer(data["schema_version"], "version") != 1:
        raise ValueError("unsupported language coverage certificate")
    if data.get("coverage_kind") == "terminal_alphabet":
        if state.eos_policy.mode is not EOSMode.ABSENT:
            raise ValueError("alphabet coverage currently requires ABSENT EOS")
        alphabet = set(state.grammar.terminal_labels.values())
        if any(not isinstance(label, int) for label in alphabet):
            raise ValueError("alphabet coverage requires byte grammar terminals")
        supplied = [_integer(v, "alphabet byte") for v in _sequence(data["alphabet"], "alphabet")]
        if len(supplied) != len(set(supplied)) or set(supplied) != alphabet:
            raise ValueError("coverage alphabet differs from the original grammar")
        relevant = {
            token
            for token, emission in enumerate(state.tokenizer_adapter.emissions)
            if emission is not None and set(emission) <= alphabet
        }
        if any(
            fixed is None and not relevant <= set(row)
            for fixed, row in zip(state.canvas, state.support.rows, strict=True)
        ):
            raise ValueError("alphabet-compatible vocabulary token is missing from support")
        return ()
    if data.get("coverage_kind", "finite_yields") != "finite_yields":
        raise ValueError("unknown support coverage kind")
    bounds: dict[int, set[bytes]] = {}
    for raw in _sequence(data["yield_bounds"], "yield bounds"):
        pair = _sequence(raw, "yield entry")
        if len(pair) != 2:
            raise ValueError("yield entry must have a head and finite strings")
        head = _integer(pair[0], "nonterminal")
        if head in bounds:
            raise ValueError("duplicate yield nonterminal")
        words = [bytes.fromhex(_string(w, "hex string")) for w in _sequence(pair[1], "words")]
        if len(words) != len(set(words)):
            raise ValueError("duplicate yield strings")
        bounds[head] = set(words)
    grammar = state.grammar
    if set(bounds) != {n.symbol_id for n in grammar.nonterminals}:
        raise ValueError("yield table must cover exactly every grammar nonterminal")
    for rule in grammar.terminal_productions:
        label = grammar.terminal_labels[rule.terminal_id]
        if not isinstance(label, int):
            raise ValueError("finite language coverage requires byte grammar terminals")
        if bytes((label,)) not in bounds[rule.head_id]:
            raise ValueError("yield upper bound omits a terminal production")
    for binary in grammar.binary_productions:
        if any(
            left + right not in bounds[binary.head_id]
            for left in bounds[binary.left_id]
            for right in bounds[binary.right_id]
        ):
            raise ValueError("yield upper bound is not closed under a binary production")
    root = bounds[grammar.start_nonterminal_id]
    if grammar.accepts_empty and b"" not in root:
        raise ValueError("yield upper bound omits the accepted empty word")
    for path in tokenizations(state, root):
        if any(token not in row for token, row in zip(path, state.support.rows, strict=True)):
            raise ValueError(
                "a full-vocabulary valid tokenization falls outside represented support"
            )
    return tuple(sorted(root))


def finite_yield_bounds(
    grammar: CnfGrammar, *, max_words: int = 4096, max_rounds: int = 256
) -> dict[str, object]:
    """Construct a finite closure, with explicit refusal for large/infinite yields."""
    bounds: dict[int, set[bytes]] = {n.symbol_id: set() for n in grammar.nonterminals}
    if grammar.accepts_empty:
        bounds[grammar.start_nonterminal_id].add(b"")
    for rule in grammar.terminal_productions:
        label = grammar.terminal_labels[rule.terminal_id]
        if not isinstance(label, int):
            raise ValueError("finite yield construction requires byte terminals")
        bounds[rule.head_id].add(bytes((label,)))
    for _ in range(max_rounds):
        changed = False
        for binary in grammar.binary_productions:
            old = bounds[binary.head_id]
            if any(
                len(left) + len(right) > 65536
                for left in bounds[binary.left_id]
                for right in bounds[binary.right_id]
            ):
                raise ValueError("finite yield closure exceeds byte-length limit")
            expanded = {
                left + right
                for left in tuple(bounds[binary.left_id])
                for right in tuple(bounds[binary.right_id])
            }
            if not expanded <= old:
                old.update(expanded)
                changed = True
                if len(old) > max_words:
                    raise ValueError("finite yield closure exceeds size limit")
        if not changed:
            return {
                "schema_version": 1,
                "yield_bounds": [
                    [head, [w.hex() for w in sorted(words)]]
                    for head, words in sorted(bounds.items())
                ],
            }
    raise ValueError("finite yield closure did not converge within the declared limit")


def terminal_alphabet_coverage(grammar: CnfGrammar) -> dict[str, object]:
    """A candidate certificate; the independent checker tests the complete vocabulary."""
    alphabet = set(grammar.terminal_labels.values())
    if any(not isinstance(label, int) for label in alphabet):
        raise ValueError("alphabet coverage requires byte grammar terminals")
    return {"schema_version": 1, "coverage_kind": "terminal_alphabet", "alphabet": sorted(alphabet)}
