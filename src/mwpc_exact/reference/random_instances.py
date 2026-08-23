"""Deterministic tiny-instance generation for oracle differential tests."""

from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import dataclass
from itertools import product
from pathlib import Path
from random import Random
from types import MappingProxyType
from typing import Self

from mwpc_exact.reference.grammar import (
    BinaryProduction,
    CnfGrammar,
    Nonterminal,
    Terminal,
    TerminalProduction,
)
from mwpc_exact.reference.recognizer import recognizes_cnf
from mwpc_exact.types import Proposal, TerminalLabel

SCHEMA_VERSION = 1


@dataclass(frozen=True, slots=True)
class RandomTokenAlignedInstance:
    """One fully serializable finite token-aligned differential case."""

    seed: int
    grammar_kind: str
    grammar: CnfGrammar
    per_position_support: tuple[tuple[int, ...], ...]
    canvas: tuple[int | None, ...]
    proposals: tuple[Proposal, ...]
    terminal_token_ids: Mapping[int, int]

    def __post_init__(self) -> None:
        if isinstance(self.seed, bool) or not isinstance(self.seed, int) or self.seed < 0:
            raise ValueError("seed must be a non-negative integer")
        if self.grammar_kind not in {"acyclic", "recursive"}:
            raise ValueError("grammar_kind must be 'acyclic' or 'recursive'")
        if not isinstance(self.grammar, CnfGrammar):
            raise TypeError("grammar must be a CnfGrammar")
        supports = tuple(tuple(support) for support in self.per_position_support)
        if not supports:
            raise ValueError("random instances require at least one token slot")
        for position, support in enumerate(supports):
            if not support:
                raise ValueError(f"support at position {position} must be non-empty")
            if any(
                isinstance(token_id, bool) or not isinstance(token_id, int) or token_id < 0
                for token_id in support
            ):
                raise ValueError("support token IDs must be non-negative integers")
            if len(set(support)) != len(support):
                raise ValueError("per-position supports must not contain duplicates")
        canvas = tuple(self.canvas)
        if len(canvas) != len(supports):
            raise ValueError("canvas and per-position support lengths must match")
        for position, token_id in enumerate(canvas):
            if token_id is not None and token_id not in supports[position]:
                raise ValueError("fixed canvas tokens must belong to their position support")
        proposals = tuple(self.proposals)
        if not all(isinstance(item, Proposal) for item in proposals):
            raise TypeError("proposals must contain only Proposal instances")
        if len({item.proposal_id for item in proposals}) != len(proposals):
            raise ValueError("proposal IDs must be unique")
        if any(
            item.position >= len(supports) or item.token_id not in supports[item.position]
            for item in proposals
        ):
            raise ValueError("every proposal must reference its finite position support")

        terminal_token_ids = dict(self.terminal_token_ids)
        grammar_terminal_ids = {item.symbol_id for item in self.grammar.terminals}
        if set(terminal_token_ids) != grammar_terminal_ids:
            raise ValueError("terminal_token_ids must cover exactly the grammar terminals")
        if any(
            isinstance(key, bool)
            or not isinstance(key, int)
            or key < 0
            or isinstance(value, bool)
            or not isinstance(value, int)
            or value < 0
            for key, value in terminal_token_ids.items()
        ):
            raise ValueError("terminal and token IDs must be non-negative integers")
        if len(set(terminal_token_ids.values())) != len(terminal_token_ids):
            raise ValueError("terminal_token_ids values must be unique")
        supported_tokens = {token_id for support in supports for token_id in support}
        if not supported_tokens <= set(terminal_token_ids.values()):
            raise ValueError("every supported token must have a terminal mapping")

        object.__setattr__(self, "per_position_support", supports)
        object.__setattr__(self, "canvas", canvas)
        object.__setattr__(self, "proposals", proposals)
        object.__setattr__(
            self,
            "terminal_token_ids",
            MappingProxyType(terminal_token_ids),
        )

    @property
    def terminal_labels_by_token_id(self) -> Mapping[int, TerminalLabel]:
        labels = self.grammar.terminal_labels
        return MappingProxyType(
            {
                token_id: labels[terminal_id]
                for terminal_id, token_id in self.terminal_token_ids.items()
            }
        )

    @property
    def vocabulary_size(self) -> int:
        return max(self.terminal_token_ids.values()) + 1

    def to_dict(self) -> dict[str, object]:
        """Return a versioned JSON-compatible replay fixture."""
        return {
            "schema_version": SCHEMA_VERSION,
            "seed": self.seed,
            "grammar_kind": self.grammar_kind,
            "grammar": self.grammar.to_dict(),
            "per_position_support": [list(support) for support in self.per_position_support],
            "canvas": list(self.canvas),
            "proposals": [
                {
                    "proposal_id": item.proposal_id,
                    "position": item.position,
                    "token_id": item.token_id,
                    "weight": item.weight,
                    "model_confidence": item.model_confidence,
                }
                for item in self.proposals
            ],
            "terminal_token_ids": [
                {"terminal_id": terminal_id, "token_id": token_id}
                for terminal_id, token_id in sorted(self.terminal_token_ids.items())
            ],
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, object]) -> Self:
        """Load and validate a replay fixture."""
        if not isinstance(data, Mapping):
            raise TypeError("random instance data must be a mapping")
        version = data.get("schema_version")
        if version != SCHEMA_VERSION:
            raise ValueError(f"unsupported random instance schema_version: {version!r}")
        grammar_data = data.get("grammar")
        if not isinstance(grammar_data, Mapping):
            raise TypeError("grammar must be a mapping")
        proposal_data = _mapping_sequence(data.get("proposals"), "proposals")
        mapping_data = _mapping_sequence(data.get("terminal_token_ids"), "terminal_token_ids")
        supports_data = _sequence(data.get("per_position_support"), "per_position_support")
        canvas_data = _sequence(data.get("canvas"), "canvas")
        grammar_kind = data.get("grammar_kind")
        if not isinstance(grammar_kind, str):
            raise TypeError("grammar_kind must be a string")
        return cls(
            seed=_integer(data.get("seed"), "seed"),
            grammar_kind=grammar_kind,
            grammar=CnfGrammar.from_dict(grammar_data),
            per_position_support=tuple(
                tuple(
                    _integer(token_id, f"support token at position {position}")
                    for token_id in _sequence(support, f"support at position {position}")
                )
                for position, support in enumerate(supports_data)
            ),
            canvas=tuple(
                None if token_id is None else _integer(token_id, "canvas token")
                for token_id in canvas_data
            ),
            proposals=tuple(
                Proposal(
                    proposal_id=_mapping_integer(item, "proposal_id", "proposal"),
                    position=_mapping_integer(item, "position", "proposal"),
                    token_id=_mapping_integer(item, "token_id", "proposal"),
                    weight=_mapping_number(item, "weight", "proposal"),
                    model_confidence=_mapping_optional_number(item, "model_confidence", "proposal"),
                )
                for item in proposal_data
            ),
            terminal_token_ids={
                _mapping_integer(item, "terminal_id", "terminal mapping"): _mapping_integer(
                    item, "token_id", "terminal mapping"
                )
                for item in mapping_data
            },
        )

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, sort_keys=True) + "\n"

    @classmethod
    def from_json(cls, text: str) -> Self:
        if not isinstance(text, str):
            raise TypeError("instance JSON must be a string")
        parsed = json.loads(text)
        if not isinstance(parsed, Mapping):
            raise TypeError("instance JSON root must be an object")
        return cls.from_dict(parsed)

    def write_json(self, path: str | Path) -> None:
        """Write a replay artifact without embedding machine-specific metadata."""
        Path(path).write_text(self.to_json(), encoding="utf-8")

    @classmethod
    def read_json(cls, path: str | Path) -> Self:
        return cls.from_json(Path(path).read_text(encoding="utf-8"))


def generate_random_instance(seed: int) -> RandomTokenAlignedInstance:
    """Generate one deterministic, deliberately nontrivial tiny instance."""
    if isinstance(seed, bool) or not isinstance(seed, int) or seed < 0:
        raise ValueError("seed must be a non-negative integer")
    rng = Random(seed)
    slot_count = 2 + rng.randrange(2)
    vocabulary = (0, 1, 2)
    terminals = tuple(Terminal(token_id, f"t{token_id}") for token_id in vocabulary)

    if seed % 3 == 0:
        grammar_kind = "recursive"
        grammar, known_witness = _recursive_grammar(rng, terminals, slot_count)
    else:
        grammar_kind = "acyclic"
        grammar, known_witness = _acyclic_grammar(rng, terminals, slot_count, seed)

    supports: list[tuple[int, ...]] = []
    for position in range(slot_count):
        count = rng.randint(1, len(vocabulary))
        support = set(rng.sample(vocabulary, count))
        support.add(known_witness[position])
        supports.append(tuple(sorted(support)))
    if len(supports[0]) < 2:
        alternative = next(token_id for token_id in vocabulary if token_id not in supports[0])
        supports[0] = tuple(sorted((*supports[0], alternative)))

    if seed % 4 == 0:
        supports = [tuple(vocabulary) for _ in range(slot_count)]
        labels = grammar.terminal_labels
        rejected = next(
            completion
            for completion in product(*supports)
            if not recognizes_cnf(
                grammar,
                tuple(labels[token_id] for token_id in completion),
            )
        )
        canvas: tuple[int | None, ...] = rejected
    else:
        canvas = tuple(
            known_witness[position] if rng.random() < 0.3 else None
            for position in range(slot_count)
        )

    proposals: list[Proposal] = []
    next_proposal_id = 0

    def add_proposal(position: int, token_id: int, weight: int) -> None:
        nonlocal next_proposal_id
        proposals.append(
            Proposal(
                proposal_id=next_proposal_id,
                position=position,
                token_id=token_id,
                weight=weight,
            )
        )
        next_proposal_id += 1

    # Two positive alternatives at one position make every case nontrivial.
    add_proposal(0, supports[0][0], rng.randint(1, 9))
    add_proposal(0, supports[0][1], rng.randint(1, 9))
    for position in range(1, slot_count):
        add_proposal(position, rng.choice(supports[position]), rng.randint(1, 9))
    if seed % 2 == 0:
        first = proposals[0]
        add_proposal(first.position, first.token_id, rng.randint(1, 9))
    if seed % 5 == 0:
        add_proposal(0, supports[0][-1], 0)

    return RandomTokenAlignedInstance(
        seed=seed,
        grammar_kind=grammar_kind,
        grammar=grammar,
        per_position_support=tuple(supports),
        canvas=canvas,
        proposals=tuple(proposals),
        terminal_token_ids={token_id: token_id for token_id in vocabulary},
    )


def _recursive_grammar(
    rng: Random, terminals: tuple[Terminal, ...], slot_count: int
) -> tuple[CnfGrammar, tuple[int, ...]]:
    base_tokens = tuple(sorted(rng.sample((0, 1, 2), rng.randint(1, 2))))
    tail_tokens = tuple(sorted(rng.sample((0, 1, 2), rng.randint(1, 2))))
    nonterminals = (Nonterminal(0, "S"), Nonterminal(1, "Tail"))
    terminal_productions: list[TerminalProduction] = []
    production_id = 1
    for token_id in base_tokens:
        terminal_productions.append(TerminalProduction(production_id, 0, token_id))
        production_id += 1
    for token_id in tail_tokens:
        terminal_productions.append(TerminalProduction(production_id, 1, token_id))
        production_id += 1
    grammar = CnfGrammar(
        nonterminals=nonterminals,
        terminals=terminals,
        start_nonterminal_id=0,
        terminal_productions=tuple(terminal_productions),
        binary_productions=(BinaryProduction(production_id, 0, 0, 1),),
    )
    return grammar, (base_tokens[0], *(tail_tokens[0] for _ in range(slot_count - 1)))


def _acyclic_grammar(
    rng: Random,
    terminals: tuple[Terminal, ...],
    slot_count: int,
    seed: int,
) -> tuple[CnfGrammar, tuple[int, ...]]:
    all_words = list(product((0, 1, 2), repeat=slot_count))
    rng.shuffle(all_words)
    allowed_words = all_words[: rng.randint(2, min(5, len(all_words)))]
    branches = [*allowed_words]
    if seed % 5 == 1:
        branches.append(allowed_words[0])  # same word, separate derivation

    nonterminals: list[Nonterminal] = [Nonterminal(0, "S")]
    terminal_productions: list[TerminalProduction] = []
    binary_productions: list[BinaryProduction] = []
    next_nonterminal_id = 1
    next_production_id = 1
    for branch_index, word in enumerate(branches):
        leaf_ids: list[int] = []
        for position, token_id in enumerate(word):
            leaf_id = next_nonterminal_id
            next_nonterminal_id += 1
            leaf_ids.append(leaf_id)
            nonterminals.append(Nonterminal(leaf_id, f"B{branch_index}_{position}"))
            terminal_productions.append(TerminalProduction(next_production_id, leaf_id, token_id))
            next_production_id += 1
        if slot_count == 2:
            binary_productions.append(
                BinaryProduction(
                    next_production_id,
                    0,
                    leaf_ids[0],
                    leaf_ids[1],
                )
            )
            next_production_id += 1
        else:
            tail_id = next_nonterminal_id
            next_nonterminal_id += 1
            nonterminals.append(Nonterminal(tail_id, f"B{branch_index}_tail"))
            binary_productions.append(
                BinaryProduction(
                    next_production_id,
                    tail_id,
                    leaf_ids[1],
                    leaf_ids[2],
                )
            )
            next_production_id += 1
            binary_productions.append(
                BinaryProduction(
                    next_production_id,
                    0,
                    leaf_ids[0],
                    tail_id,
                )
            )
            next_production_id += 1
    grammar = CnfGrammar(
        nonterminals=tuple(nonterminals),
        terminals=terminals,
        start_nonterminal_id=0,
        terminal_productions=tuple(terminal_productions),
        binary_productions=tuple(binary_productions),
    )
    return grammar, allowed_words[0]


def _sequence(value: object, field_name: str) -> tuple[object, ...]:
    if isinstance(value, (str, bytes)) or not isinstance(value, (list, tuple)):
        raise TypeError(f"{field_name} must be a sequence")
    return tuple(value)


def _mapping_sequence(value: object, field_name: str) -> tuple[Mapping[str, object], ...]:
    items = _sequence(value, field_name)
    result: list[Mapping[str, object]] = []
    for item in items:
        if not isinstance(item, Mapping):
            raise TypeError(f"{field_name} must contain only mappings")
        result.append(item)
    return tuple(result)


def _integer(value: object, field_name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{field_name} must be an integer")
    return value


def _mapping_value(item: Mapping[str, object], key: str, description: str) -> object:
    if key not in item:
        raise ValueError(f"{description} is missing {key}")
    return item[key]


def _mapping_integer(item: Mapping[str, object], key: str, description: str) -> int:
    return _integer(_mapping_value(item, key, description), f"{description} {key}")


def _mapping_number(item: Mapping[str, object], key: str, description: str) -> float:
    value = _mapping_value(item, key, description)
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TypeError(f"{description} {key} must be a real number")
    return float(value)


def _mapping_optional_number(
    item: Mapping[str, object], key: str, description: str
) -> float | None:
    value = _mapping_value(item, key, description)
    return None if value is None else _mapping_number(item, key, description)
