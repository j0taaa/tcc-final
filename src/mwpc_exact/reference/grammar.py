"""Small immutable grammar representation for the token-aligned reference solver.

The CKY core consumes only terminal productions ``A -> a`` and binary
productions ``A -> B C``. Empty-string acceptance is an explicit grammar flag;
epsilon is never represented as a terminal. Unit productions are rejected and
must be removed by the independently tested normalization boundary.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from typing import Protocol, Self

from mwpc_exact.types import TerminalLabel


def _stable_id(value: object, field_name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{field_name} must be an integer")
    if value < 0:
        raise ValueError(f"{field_name} must be non-negative")
    return value


def _nonempty_name(value: object, field_name: str) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{field_name} must be a string")
    if not value.strip():
        raise ValueError(f"{field_name} must be non-empty")
    return value


def _terminal_label(value: object) -> TerminalLabel:
    if isinstance(value, bool) or not isinstance(value, (int, str)):
        raise TypeError("terminal label must be a byte integer or string")
    if isinstance(value, int) and not 0 <= value <= 255:
        raise ValueError("integer terminal labels must be bytes in [0, 255]")
    if isinstance(value, str) and not value:
        raise ValueError("string terminal labels must be non-empty")
    return value


def _source_ids(value: object) -> tuple[int, ...]:
    if isinstance(value, (str, bytes)) or not isinstance(value, Iterable):
        raise TypeError("source_production_ids must be a sequence of integers")
    result = tuple(_stable_id(item, "source_production_ids item") for item in tuple(value))
    if len(set(result)) != len(result):
        raise ValueError("source_production_ids must not contain duplicates")
    return result


@dataclass(frozen=True, slots=True)
class Nonterminal:
    """One nonterminal with a stable solver-local ID."""

    symbol_id: int
    name: str

    def __post_init__(self) -> None:
        _stable_id(self.symbol_id, "nonterminal symbol_id")
        _nonempty_name(self.name, "nonterminal name")


@dataclass(frozen=True, slots=True)
class Terminal:
    """One terminal label with a stable solver-local ID."""

    symbol_id: int
    label: TerminalLabel

    def __post_init__(self) -> None:
        _stable_id(self.symbol_id, "terminal symbol_id")
        object.__setattr__(self, "label", _terminal_label(self.label))


@dataclass(frozen=True, slots=True)
class TerminalProduction:
    """A CNF production ``head -> terminal``."""

    production_id: int
    head_id: int
    terminal_id: int
    source_production_ids: tuple[int, ...] = ()

    def __post_init__(self) -> None:
        _stable_id(self.production_id, "production_id")
        _stable_id(self.head_id, "head_id")
        _stable_id(self.terminal_id, "terminal_id")
        object.__setattr__(
            self,
            "source_production_ids",
            _source_ids(self.source_production_ids),
        )


@dataclass(frozen=True, slots=True)
class BinaryProduction:
    """A CNF production ``head -> left right``."""

    production_id: int
    head_id: int
    left_id: int
    right_id: int
    source_production_ids: tuple[int, ...] = ()

    def __post_init__(self) -> None:
        _stable_id(self.production_id, "production_id")
        _stable_id(self.head_id, "head_id")
        _stable_id(self.left_id, "left_id")
        _stable_id(self.right_id, "right_id")
        object.__setattr__(
            self,
            "source_production_ids",
            _source_ids(self.source_production_ids),
        )


@dataclass(frozen=True, slots=True)
class CnfGrammar:
    """Validated CNF grammar used by the Python reference implementation.

    ``accepts_empty`` is deliberately separate from the production lists. CKY
    over a non-empty finite canvas never treats epsilon as consuming a slot.
    """

    nonterminals: tuple[Nonterminal, ...]
    terminals: tuple[Terminal, ...]
    start_nonterminal_id: int
    terminal_productions: tuple[TerminalProduction, ...] = ()
    binary_productions: tuple[BinaryProduction, ...] = ()
    accepts_empty: bool = False

    def __post_init__(self) -> None:
        nonterminals = tuple(self.nonterminals)
        terminals = tuple(self.terminals)
        terminal_productions = tuple(self.terminal_productions)
        binary_productions = tuple(self.binary_productions)
        if not nonterminals:
            raise ValueError("CNF grammar requires at least one nonterminal")
        if not all(isinstance(item, Nonterminal) for item in nonterminals):
            raise TypeError("nonterminals must contain only Nonterminal instances")
        if not all(isinstance(item, Terminal) for item in terminals):
            raise TypeError("terminals must contain only Terminal instances")
        if not all(isinstance(item, TerminalProduction) for item in terminal_productions):
            raise TypeError("terminal_productions must contain only TerminalProduction instances")
        if not all(isinstance(item, BinaryProduction) for item in binary_productions):
            raise TypeError("binary_productions must contain only BinaryProduction instances")
        if not isinstance(self.accepts_empty, bool):
            raise TypeError("accepts_empty must be a bool")

        nonterminal_ids = tuple(item.symbol_id for item in nonterminals)
        terminal_ids = tuple(item.symbol_id for item in terminals)
        if len(set(nonterminal_ids)) != len(nonterminal_ids):
            raise ValueError("nonterminal symbol IDs must be unique")
        if len({item.name for item in nonterminals}) != len(nonterminals):
            raise ValueError("nonterminal names must be unique")
        if len(set(terminal_ids)) != len(terminal_ids):
            raise ValueError("terminal symbol IDs must be unique")
        if len({item.label for item in terminals}) != len(terminals):
            raise ValueError("terminal labels must be unique")

        start_id = _stable_id(self.start_nonterminal_id, "start_nonterminal_id")
        nonterminal_id_set = set(nonterminal_ids)
        terminal_id_set = set(terminal_ids)
        if start_id not in nonterminal_id_set:
            raise ValueError("start_nonterminal_id must reference a nonterminal")

        all_productions: tuple[TerminalProduction | BinaryProduction, ...] = (
            *terminal_productions,
            *binary_productions,
        )
        production_ids = tuple(item.production_id for item in all_productions)
        if len(set(production_ids)) != len(production_ids):
            raise ValueError("production IDs must be globally unique")
        for terminal_production in terminal_productions:
            if terminal_production.head_id not in nonterminal_id_set:
                raise ValueError(
                    f"terminal production {terminal_production.production_id} has unknown head_id"
                )
            if terminal_production.terminal_id not in terminal_id_set:
                raise ValueError(
                    f"terminal production {terminal_production.production_id} "
                    "has unknown terminal_id"
                )
        for binary_production in binary_productions:
            references = (
                binary_production.head_id,
                binary_production.left_id,
                binary_production.right_id,
            )
            if any(reference not in nonterminal_id_set for reference in references):
                raise ValueError(
                    f"binary production {binary_production.production_id} references an "
                    "unknown nonterminal"
                )

        object.__setattr__(self, "nonterminals", nonterminals)
        object.__setattr__(self, "terminals", terminals)
        object.__setattr__(self, "terminal_productions", terminal_productions)
        object.__setattr__(self, "binary_productions", binary_productions)

    @property
    def nonterminal_names(self) -> Mapping[int, str]:
        """Return the stable nonterminal ID-to-name symbol table."""
        return {symbol.symbol_id: symbol.name for symbol in self.nonterminals}

    @property
    def terminal_labels(self) -> Mapping[int, TerminalLabel]:
        """Return the stable terminal ID-to-label symbol table."""
        return {symbol.symbol_id: symbol.label for symbol in self.terminals}

    def to_dict(self) -> dict[str, object]:
        """Serialize the complete grammar without losing stable IDs."""
        return {
            "nonterminals": [
                {"symbol_id": item.symbol_id, "name": item.name} for item in self.nonterminals
            ],
            "terminals": [
                {"symbol_id": item.symbol_id, "label": item.label} for item in self.terminals
            ],
            "start_nonterminal_id": self.start_nonterminal_id,
            "terminal_productions": [
                {
                    "production_id": item.production_id,
                    "head_id": item.head_id,
                    "terminal_id": item.terminal_id,
                    "source_production_ids": list(item.source_production_ids),
                }
                for item in self.terminal_productions
            ],
            "binary_productions": [
                {
                    "production_id": item.production_id,
                    "head_id": item.head_id,
                    "left_id": item.left_id,
                    "right_id": item.right_id,
                    "source_production_ids": list(item.source_production_ids),
                }
                for item in self.binary_productions
            ],
            "accepts_empty": self.accepts_empty,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, object]) -> Self:
        """Deserialize and revalidate a grammar produced by :meth:`to_dict`."""
        if not isinstance(data, Mapping):
            raise TypeError("grammar data must be a mapping")
        required = {
            "nonterminals",
            "terminals",
            "start_nonterminal_id",
            "terminal_productions",
            "binary_productions",
            "accepts_empty",
        }
        missing = required - set(data)
        if missing:
            raise ValueError(f"missing grammar fields: {', '.join(sorted(missing))}")
        unknown = set(data) - required
        if unknown:
            raise ValueError(f"unknown grammar fields: {', '.join(sorted(unknown))}")

        return cls(
            nonterminals=tuple(
                Nonterminal(
                    symbol_id=_mapping_int(item, "symbol_id", "nonterminal"),
                    name=_mapping_str(item, "name", "nonterminal"),
                )
                for item in _mapping_items(data["nonterminals"], "nonterminals")
            ),
            terminals=tuple(
                Terminal(
                    symbol_id=_mapping_int(item, "symbol_id", "terminal"),
                    label=_mapping_terminal(item, "label", "terminal"),
                )
                for item in _mapping_items(data["terminals"], "terminals")
            ),
            start_nonterminal_id=_plain_int(data["start_nonterminal_id"], "start_nonterminal_id"),
            terminal_productions=tuple(
                TerminalProduction(
                    production_id=_mapping_int(item, "production_id", "terminal production"),
                    head_id=_mapping_int(item, "head_id", "terminal production"),
                    terminal_id=_mapping_int(item, "terminal_id", "terminal production"),
                    source_production_ids=_mapping_int_tuple(
                        item, "source_production_ids", "terminal production"
                    ),
                )
                for item in _mapping_items(data["terminal_productions"], "terminal_productions")
            ),
            binary_productions=tuple(
                BinaryProduction(
                    production_id=_mapping_int(item, "production_id", "binary production"),
                    head_id=_mapping_int(item, "head_id", "binary production"),
                    left_id=_mapping_int(item, "left_id", "binary production"),
                    right_id=_mapping_int(item, "right_id", "binary production"),
                    source_production_ids=_mapping_int_tuple(
                        item, "source_production_ids", "binary production"
                    ),
                )
                for item in _mapping_items(data["binary_productions"], "binary_productions")
            ),
            accepts_empty=_plain_bool(data["accepts_empty"], "accepts_empty"),
        )


class RepositoryCFG(Protocol):
    """Structural boundary exposed by the pinned EPIC CFG binding."""

    def to_text(self) -> str: ...


def from_repository_cnf(grammar: RepositoryCFG) -> CnfGrammar:
    """Adapt an already-normalized repository CFG without importing EPIC.

    EPIC's ``CFG.to_text()`` includes a ``Start Symbol:`` line, production
    lines, and a trailing ``Terminals:`` line. This adapter intentionally does
    not call ``to_normal_form()``: normalization is an explicit, audited step.
    """
    if not hasattr(grammar, "to_text") or not callable(grammar.to_text):
        raise TypeError("repository grammar must provide a callable to_text()")
    text = grammar.to_text()
    if not isinstance(text, str):
        raise TypeError("repository grammar to_text() must return a string")
    return _parse_repository_cnf_text(text)


def _parse_repository_cnf_text(text: str) -> CnfGrammar:
    lines = tuple(line.strip() for line in text.splitlines() if line.strip())
    start_lines = tuple(line for line in lines if line.startswith("Start Symbol:"))
    if len(start_lines) != 1:
        raise ValueError("repository CNF text must contain exactly one Start Symbol line")
    start_name = start_lines[0].partition(":")[2].strip()
    if not start_name:
        raise ValueError("repository CNF start symbol must be non-empty")

    production_lines = tuple(
        line
        for line in lines
        if "->" in line
        and not line.startswith("Start Symbol:")
        and not line.startswith("Terminals:")
    )
    if not production_lines:
        raise ValueError("repository CNF text does not contain productions")
    heads = tuple(line.partition("->")[0].strip() for line in production_lines)
    if any(not head for head in heads):
        raise ValueError("repository CNF contains an empty production head")
    if len(set(heads)) != len(heads):
        raise ValueError("repository CNF must serialize each production head once")
    if start_name not in heads:
        raise ValueError("repository CNF start symbol has no serialized nonterminal")

    nonterminals = tuple(
        Nonterminal(symbol_id=index, name=name) for index, name in enumerate(heads)
    )
    nonterminal_by_name = {item.name: item.symbol_id for item in nonterminals}
    terminals: list[Terminal] = []
    terminal_by_label: dict[str, int] = {}
    terminal_productions: list[TerminalProduction] = []
    binary_productions: list[BinaryProduction] = []
    accepts_empty = False
    next_production_id = 0

    for line in production_lines:
        head_text, _, alternatives_text = line.partition("->")
        head_name = head_text.strip()
        alternatives = tuple(part.strip() for part in alternatives_text.split("|"))
        if not alternatives:
            raise ValueError(f"repository CNF head {head_name!r} has no alternatives")
        for alternative in alternatives:
            symbols = tuple(alternative.split())
            if not symbols or symbols in (("ε",), ("epsilon",), ("$",)):
                if head_name != start_name:
                    raise ValueError("only the CNF start symbol may derive epsilon")
                accepts_empty = True
                continue
            if len(symbols) == 1:
                symbol = symbols[0]
                if symbol in nonterminal_by_name:
                    raise ValueError(f"unit production {head_name} -> {symbol} is not valid CNF")
                terminal_id = terminal_by_label.get(symbol)
                if terminal_id is None:
                    terminal_id = len(terminals)
                    terminal_by_label[symbol] = terminal_id
                    terminals.append(Terminal(symbol_id=terminal_id, label=symbol))
                terminal_productions.append(
                    TerminalProduction(
                        production_id=next_production_id,
                        head_id=nonterminal_by_name[head_name],
                        terminal_id=terminal_id,
                    )
                )
            elif len(symbols) == 2:
                missing = tuple(symbol for symbol in symbols if symbol not in nonterminal_by_name)
                if missing:
                    raise ValueError(
                        f"binary production {head_name!r} references unknown "
                        f"nonterminal(s): {', '.join(missing)}"
                    )
                binary_productions.append(
                    BinaryProduction(
                        production_id=next_production_id,
                        head_id=nonterminal_by_name[head_name],
                        left_id=nonterminal_by_name[symbols[0]],
                        right_id=nonterminal_by_name[symbols[1]],
                    )
                )
            else:
                raise ValueError(
                    f"production {head_name!r} has body length {len(symbols)}; "
                    "expected terminal or binary CNF body"
                )
            next_production_id += 1

    return CnfGrammar(
        nonterminals=nonterminals,
        terminals=tuple(terminals),
        start_nonterminal_id=nonterminal_by_name[start_name],
        terminal_productions=tuple(terminal_productions),
        binary_productions=tuple(binary_productions),
        accepts_empty=accepts_empty,
    )


def _mapping_items(value: object, field_name: str) -> tuple[Mapping[str, object], ...]:
    if isinstance(value, (str, bytes)) or not isinstance(value, Iterable):
        raise TypeError(f"{field_name} must be a sequence of mappings")
    items = tuple(value)
    if not all(isinstance(item, Mapping) for item in items):
        raise TypeError(f"{field_name} must contain only mappings")
    return items


def _mapping_value(item: Mapping[str, object], key: str, description: str) -> object:
    if key not in item:
        raise ValueError(f"{description} is missing {key}")
    return item[key]


def _plain_int(value: object, field_name: str) -> int:
    return _stable_id(value, field_name)


def _plain_bool(value: object, field_name: str) -> bool:
    if not isinstance(value, bool):
        raise TypeError(f"{field_name} must be a bool")
    return value


def _mapping_int(item: Mapping[str, object], key: str, description: str) -> int:
    return _stable_id(_mapping_value(item, key, description), f"{description} {key}")


def _mapping_str(item: Mapping[str, object], key: str, description: str) -> str:
    return _nonempty_name(_mapping_value(item, key, description), f"{description} {key}")


def _mapping_terminal(item: Mapping[str, object], key: str, description: str) -> TerminalLabel:
    return _terminal_label(_mapping_value(item, key, description))


def _mapping_int_tuple(item: Mapping[str, object], key: str, description: str) -> tuple[int, ...]:
    return _source_ids(_mapping_value(item, key, description))
