"""Seeded exhaustive differential checks for finite-slot EOS/PAD semantics.

The oracle enumerates explicit token rows and interprets the EOS policy
directly.  It does not inspect product-lattice states, parser charts, epsilon
normalization, or backpointers.  This separation keeps disagreements useful as
correctness blockers rather than comparing an implementation with itself.
"""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from itertools import product
from math import fsum, isclose
from pathlib import Path
from random import Random
from types import MappingProxyType
from typing import NoReturn, Self

from mwpc_exact.eos_lattice import (
    EOSLattice,
    EOSLatticePath,
    EOSMode,
    EOSPolicy,
    TokenRole,
    build_eos_lattice,
)
from mwpc_exact.reference.epsilon import solve_cfg_on_epsilon_dag
from mwpc_exact.reference.grammar import (
    BinaryProduction,
    CnfGrammar,
    Nonterminal,
    Terminal,
    TerminalProduction,
)
from mwpc_exact.reference.recognizer import recognizes_cnf
from mwpc_exact.support import PerPositionSupport, SupportPolicy, build_per_position_support
from mwpc_exact.token_lattice import build_token_lattice
from mwpc_exact.tokenizer_bytes import CompositionalByteLevelAdapter
from mwpc_exact.types import ExactCommitResult, Proposal, SolveStatus, SupportKind
from mwpc_exact.validator import validate_exact_commit_certificate

EOS_DIFFERENTIAL_GENERATOR_SCHEMA_VERSION = 1
_EMISSIONS: tuple[bytes | None, ...] = (b"a", b"b", None, None, None)
_EOS_PAD_ID = 2
_EOT_ID = 3
_UNSUPPORTED_CONTROL_ID = 4


class EOSFiniteSlotDifferentialMismatch(AssertionError):
    """One deterministic seed violated a named finite-slot property."""

    def __init__(self, *, seed: int, property_name: str, details: str) -> None:
        self.seed = seed
        self.property_name = property_name
        self.details = details
        super().__init__(f"seed={seed} property={property_name}: {details}")


def _mapping(value: object, field_name: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping) or any(not isinstance(key, str) for key in value):
        raise TypeError(f"{field_name} must be a string-keyed mapping")
    return value


def _sequence(value: object, field_name: str) -> Sequence[object]:
    if isinstance(value, (str, bytes)) or not isinstance(value, Sequence):
        raise TypeError(f"{field_name} must be a finite sequence")
    return value


def _integer(value: object, field_name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{field_name} must be an integer")
    return value


def _non_negative_integer(value: object, field_name: str) -> int:
    result = _integer(value, field_name)
    if result < 0:
        raise ValueError(f"{field_name} must be non-negative")
    return result


def _number(value: object, field_name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TypeError(f"{field_name} must be a real number")
    return float(value)


def _string(value: object, field_name: str) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{field_name} must be a string")
    if not value.strip():
        raise ValueError(f"{field_name} must be non-empty")
    return value


def _integer_tuple(value: object, field_name: str) -> tuple[int, ...]:
    return tuple(
        _non_negative_integer(item, f"{field_name} item") for item in _sequence(value, field_name)
    )


def _proposal_from_dict(data: Mapping[str, object]) -> Proposal:
    required = {"proposal_id", "position", "token_id", "weight"}
    if set(data) != required:
        raise ValueError("serialized proposal fields do not match the EOS fixture schema")
    return Proposal(
        proposal_id=_non_negative_integer(data["proposal_id"], "proposal_id"),
        position=_non_negative_integer(data["position"], "proposal position"),
        token_id=_non_negative_integer(data["token_id"], "proposal token_id"),
        weight=_number(data["weight"], "proposal weight"),
    )


def _policy_from_dict(data: Mapping[str, object]) -> EOSPolicy:
    required = {"mode", "termination_token_ids", "pad_token_id"}
    if set(data) != required:
        raise ValueError("serialized EOS policy fields do not match the fixture schema")
    mode_value = _string(data["mode"], "EOS mode")
    try:
        mode = EOSMode(mode_value)
    except ValueError as exc:
        raise ValueError(f"unknown EOS mode: {mode_value!r}") from exc
    raw_pad = data["pad_token_id"]
    return EOSPolicy(
        mode=mode,
        termination_token_ids=_integer_tuple(
            data["termination_token_ids"], "termination_token_ids"
        ),
        pad_token_id=(None if raw_pad is None else _non_negative_integer(raw_pad, "pad_token_id")),
    )


def _exact_word_grammar(word: bytes) -> CnfGrammar:
    """Construct a deterministic strict-CNF grammar for exactly one byte word."""

    if not isinstance(word, bytes):
        raise TypeError("word must be bytes")
    if not word:
        return CnfGrammar(
            nonterminals=(Nonterminal(0, "S"),),
            terminals=(),
            start_nonterminal_id=0,
            accepts_empty=True,
        )

    labels = tuple(sorted(set(word)))
    terminals = tuple(Terminal(index, label) for index, label in enumerate(labels))
    terminal_id_by_label = {terminal.label: terminal.symbol_id for terminal in terminals}
    if len(word) == 1:
        return CnfGrammar(
            nonterminals=(Nonterminal(0, "S"),),
            terminals=terminals,
            start_nonterminal_id=0,
            terminal_productions=(TerminalProduction(0, 0, terminal_id_by_label[word[0]]),),
        )

    length = len(word)
    preterminal_ids = tuple(range(1, length + 1))
    chain_ids = tuple(range(length + 1, length + 1 + (length - 2)))
    nonterminals = (
        Nonterminal(0, "S"),
        *(
            Nonterminal(symbol_id, f"P{position}")
            for position, symbol_id in enumerate(preterminal_ids)
        ),
        *(Nonterminal(symbol_id, f"C{offset + 1}") for offset, symbol_id in enumerate(chain_ids)),
    )
    terminal_productions = tuple(
        TerminalProduction(
            production_id=position,
            head_id=preterminal_ids[position],
            terminal_id=terminal_id_by_label[byte_value],
        )
        for position, byte_value in enumerate(word)
    )
    next_production_id = len(terminal_productions)
    binary_productions: list[BinaryProduction] = []
    if length == 2:
        binary_productions.append(
            BinaryProduction(next_production_id, 0, preterminal_ids[0], preterminal_ids[1])
        )
    else:
        binary_productions.append(
            BinaryProduction(next_production_id, 0, preterminal_ids[0], chain_ids[0])
        )
        next_production_id += 1
        for position in range(1, length - 2):
            binary_productions.append(
                BinaryProduction(
                    next_production_id,
                    chain_ids[position - 1],
                    preterminal_ids[position],
                    chain_ids[position],
                )
            )
            next_production_id += 1
        binary_productions.append(
            BinaryProduction(
                next_production_id,
                chain_ids[-1],
                preterminal_ids[-2],
                preterminal_ids[-1],
            )
        )
    return CnfGrammar(
        nonterminals=nonterminals,
        terminals=terminals,
        start_nonterminal_id=0,
        terminal_productions=terminal_productions,
        binary_productions=tuple(binary_productions),
    )


@dataclass(frozen=True, slots=True)
class RandomEOSFiniteSlotInstance:
    """One complete, versioned finite-support EOS/PAD differential input."""

    seed: int
    grammar: CnfGrammar
    grammar_kind: str
    canvas: tuple[int | None, ...]
    support_rows: tuple[tuple[int, ...], ...]
    emissions: tuple[bytes | None, ...]
    proposals: tuple[Proposal, ...]
    eos_policy: EOSPolicy
    target_token_ids: tuple[int, ...]
    target_eos_position: int | None
    features: tuple[str, ...]

    def __post_init__(self) -> None:
        if isinstance(self.seed, bool) or not isinstance(self.seed, int) or self.seed < 0:
            raise ValueError("seed must be a non-negative integer")
        if not isinstance(self.grammar, CnfGrammar):
            raise TypeError("grammar must be a CnfGrammar")
        _string(self.grammar_kind, "grammar_kind")
        canvas = tuple(self.canvas)
        rows = tuple(tuple(row) for row in self.support_rows)
        emissions = tuple(self.emissions)
        proposals = tuple(self.proposals)
        target = tuple(self.target_token_ids)
        features = tuple(self.features)
        if not canvas or len(rows) != len(canvas) or len(target) != len(canvas):
            raise ValueError("canvas, support rows, and target path need equal non-zero length")
        if not emissions or any(
            emission is not None and (not isinstance(emission, bytes) or not emission)
            for emission in emissions
        ):
            raise ValueError("ordinary emissions must be non-empty bytes; controls use null")
        if not all(isinstance(proposal, Proposal) for proposal in proposals):
            raise TypeError("proposals must contain only Proposal instances")
        if not isinstance(self.eos_policy, EOSPolicy):
            raise TypeError("eos_policy must be an EOSPolicy")
        if self.eos_policy.mode not in {EOSMode.REQUIRED, EOSMode.OPTIONAL}:
            raise ValueError("random EOS fixtures support only REQUIRED and OPTIONAL modes")
        if len(set(features)) != len(features) or any(not feature for feature in features):
            raise ValueError("features must contain unique non-empty strings")
        for position, token_id in enumerate(target):
            if token_id not in rows[position]:
                raise ValueError("target token path must be represented in every support row")
            fixed_token = canvas[position]
            if fixed_token is not None and fixed_token != token_id:
                raise ValueError("target token path must preserve every fixed canvas position")
        object.__setattr__(self, "canvas", canvas)
        object.__setattr__(self, "support_rows", rows)
        object.__setattr__(self, "emissions", emissions)
        object.__setattr__(self, "proposals", proposals)
        object.__setattr__(self, "target_token_ids", target)
        object.__setattr__(self, "features", features)
        if self.support.rows != rows:
            raise AssertionError("support construction changed the serialized explicit rows")
        interpreted = _interpret_token_path(self, target)
        if interpreted is None or interpreted.eos_position != self.target_eos_position:
            raise ValueError("target path does not satisfy its recorded finite EOS semantics")

    @property
    def adapter(self) -> CompositionalByteLevelAdapter:
        return CompositionalByteLevelAdapter(self.emissions)

    @property
    def support(self) -> PerPositionSupport:
        assert self.eos_policy.pad_token_id is not None
        special_ids = tuple(
            dict.fromkeys((*self.eos_policy.termination_token_ids, self.eos_policy.pad_token_id))
        )
        return build_per_position_support(
            canvas=self.canvas,
            policy=SupportPolicy(
                kind=SupportKind.EXPLICIT,
                vocabulary_size=len(self.emissions),
                required_special_token_ids=special_ids,
                pruning_description=f"T704 seeded explicit fixture {self.seed}",
            ),
            explicit_support=dict(enumerate(self.support_rows)),
            proposals=self.proposals,
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "schema_version": EOS_DIFFERENTIAL_GENERATOR_SCHEMA_VERSION,
            "seed": self.seed,
            "grammar": self.grammar.to_dict(),
            "grammar_kind": self.grammar_kind,
            "canvas": list(self.canvas),
            "support_rows": [list(row) for row in self.support_rows],
            "emissions_hex_by_token_id": [
                None if emission is None else emission.hex() for emission in self.emissions
            ],
            "proposals": [
                {
                    "proposal_id": proposal.proposal_id,
                    "position": proposal.position,
                    "token_id": proposal.token_id,
                    "weight": proposal.weight,
                }
                for proposal in self.proposals
            ],
            "eos_policy": self.eos_policy.to_dict(),
            "target_token_ids": list(self.target_token_ids),
            "target_eos_position": self.target_eos_position,
            "features": list(self.features),
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, object]) -> Self:
        required = {
            "schema_version",
            "seed",
            "grammar",
            "grammar_kind",
            "canvas",
            "support_rows",
            "emissions_hex_by_token_id",
            "proposals",
            "eos_policy",
            "target_token_ids",
            "target_eos_position",
            "features",
        }
        if set(data) != required:
            raise ValueError("serialized EOS fixture fields do not match the schema")
        schema_version = _non_negative_integer(data["schema_version"], "schema_version")
        if schema_version != EOS_DIFFERENTIAL_GENERATOR_SCHEMA_VERSION:
            raise ValueError(f"unsupported EOS differential schema version: {schema_version}")
        raw_target_eos = data["target_eos_position"]
        return cls(
            seed=_non_negative_integer(data["seed"], "seed"),
            grammar=CnfGrammar.from_dict(_mapping(data["grammar"], "grammar")),
            grammar_kind=_string(data["grammar_kind"], "grammar_kind"),
            canvas=tuple(
                None if item is None else _non_negative_integer(item, "canvas item")
                for item in _sequence(data["canvas"], "canvas")
            ),
            support_rows=tuple(
                _integer_tuple(row, "support row")
                for row in _sequence(data["support_rows"], "support_rows")
            ),
            emissions=tuple(
                None if item is None else bytes.fromhex(_string(item, "emission hex"))
                for item in _sequence(
                    data["emissions_hex_by_token_id"], "emissions_hex_by_token_id"
                )
            ),
            proposals=tuple(
                _proposal_from_dict(_mapping(item, "proposal"))
                for item in _sequence(data["proposals"], "proposals")
            ),
            eos_policy=_policy_from_dict(_mapping(data["eos_policy"], "eos_policy")),
            target_token_ids=_integer_tuple(data["target_token_ids"], "target_token_ids"),
            target_eos_position=(
                None
                if raw_target_eos is None
                else _non_negative_integer(raw_target_eos, "target_eos_position")
            ),
            features=tuple(
                _string(item, "feature") for item in _sequence(data["features"], "features")
            ),
        )

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, sort_keys=True) + "\n"

    @classmethod
    def from_json(cls, payload: str) -> Self:
        parsed: object = json.loads(payload)
        return cls.from_dict(_mapping(parsed, "EOS differential fixture"))

    def write_json(self, path: str | Path) -> None:
        output = Path(path)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(self.to_json(), encoding="utf-8")

    @classmethod
    def read_json(cls, path: str | Path) -> Self:
        return cls.from_json(Path(path).read_text(encoding="utf-8"))


@dataclass(frozen=True, slots=True)
class EOSFiniteSlotCaseReport:
    seed: int
    status: SolveStatus
    enumerated_token_paths: int
    legal_eos_paths: int
    grammar_valid_paths: int
    witness_eos_bucket: str | None
    property_checks: Mapping[str, int]
    features: tuple[str, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "property_checks", MappingProxyType(dict(self.property_checks)))


@dataclass(frozen=True, slots=True)
class EOSFiniteSlotFailure:
    seed: int
    error_type: str
    message: str
    fixture_file: str | None
    failure_file: str | None

    def to_dict(self) -> dict[str, object]:
        return {
            "seed": self.seed,
            "error_type": self.error_type,
            "message": self.message,
            "fixture_file": self.fixture_file,
            "failure_file": self.failure_file,
        }


@dataclass(frozen=True, slots=True)
class EOSFiniteSlotCampaignSummary:
    campaign_name: str
    seed_start: int
    case_count: int
    passed_cases: int
    failed_cases: int
    total_enumerated_token_paths: int
    total_legal_eos_paths: int
    total_grammar_valid_paths: int
    status_counts: Mapping[str, int]
    feature_case_counts: Mapping[str, int]
    witness_eos_position_counts: Mapping[str, int]
    property_checks: Mapping[str, int]
    failures: tuple[EOSFiniteSlotFailure, ...]
    metadata: Mapping[str, str]

    def __post_init__(self) -> None:
        if not self.campaign_name.strip():
            raise ValueError("campaign_name must be non-empty")
        if self.passed_cases + self.failed_cases != self.case_count:
            raise ValueError("campaign passed/failed counts must equal case_count")
        for field_name in (
            "status_counts",
            "feature_case_counts",
            "witness_eos_position_counts",
            "property_checks",
            "metadata",
        ):
            object.__setattr__(
                self,
                field_name,
                MappingProxyType(dict(getattr(self, field_name))),
            )

    def to_dict(self) -> dict[str, object]:
        return {
            "schema_version": 1,
            "campaign": "m7_eos_finite_slot_differential",
            "campaign_name": self.campaign_name,
            "seed_start": self.seed_start,
            "case_count": self.case_count,
            "passed_cases": self.passed_cases,
            "failed_cases": self.failed_cases,
            "total_enumerated_token_paths": self.total_enumerated_token_paths,
            "total_legal_eos_paths": self.total_legal_eos_paths,
            "total_grammar_valid_paths": self.total_grammar_valid_paths,
            "status_counts": dict(self.status_counts),
            "feature_case_counts": dict(self.feature_case_counts),
            "witness_eos_position_counts": dict(self.witness_eos_position_counts),
            "property_checks": dict(self.property_checks),
            "failures": [failure.to_dict() for failure in self.failures],
            "metadata": dict(self.metadata),
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, sort_keys=True) + "\n"

    def write_json(self, path: str | Path) -> None:
        output = Path(path)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(self.to_json(), encoding="utf-8")


@dataclass(frozen=True, slots=True)
class _InterpretedPath:
    token_ids: tuple[int, ...]
    token_roles: tuple[TokenRole, ...]
    emitted_bytes: bytes
    eos_position: int | None
    content_endpoint_slot: int
    objective_value: float
    selected_proposal_ids: tuple[int, ...]


@dataclass(frozen=True, slots=True)
class _OracleOutcome:
    status: SolveStatus
    objective_value: float | None
    optimal_token_paths: frozenset[tuple[int, ...]]
    legal_paths: Mapping[tuple[int, ...], _InterpretedPath]
    enumerated_token_paths: int
    grammar_valid_paths: int

    def __post_init__(self) -> None:
        object.__setattr__(self, "legal_paths", MappingProxyType(dict(self.legal_paths)))


def generate_random_eos_finite_slot_instance(seed: int) -> RandomEOSFiniteSlotInstance:
    """Generate a deterministic tiny EOS/PAD/support/fixed-position instance."""

    if isinstance(seed, bool) or not isinstance(seed, int) or seed < 0:
        raise ValueError("seed must be a non-negative integer")
    rng = Random(seed)
    slot_count = 2 + rng.randrange(4)
    mode_selector = seed % 6
    mode = EOSMode.OPTIONAL if mode_selector in {0, 1} else EOSMode.REQUIRED
    eos_position = None if mode_selector == 0 else rng.randrange(slot_count)
    policy = EOSPolicy(
        mode=mode,
        termination_token_ids=(_EOS_PAD_ID, _EOT_ID),
        pad_token_id=_EOS_PAD_ID,
    )
    content_endpoint = slot_count if eos_position is None else eos_position
    content_tokens = tuple(rng.randrange(2) for _ in range(content_endpoint))
    target: list[int] = list(content_tokens)
    if eos_position is not None:
        target.append(rng.choice((_EOS_PAD_ID, _EOT_ID)))
        target.extend((_EOS_PAD_ID,) * (slot_count - eos_position - 1))

    rows: list[tuple[int, ...]] = []
    for target_token in target:
        represented = {target_token, _EOS_PAD_ID, _EOT_ID}
        for ordinary_token_id in (0, 1):
            if rng.random() < 0.55:
                represented.add(ordinary_token_id)
        if rng.random() < 0.25:
            represented.add(_UNSUPPORTED_CONTROL_ID)
        rows.append(tuple(sorted(represented)))

    canvas: list[int | None] = [None] * slot_count
    features = [
        "explicit_represented_support",
        "random_support_rows",
        "integer_proposal_weights",
        "multiple_proposals_same_choice",
        "zero_weight_proposal",
        f"mode_{mode.value}",
    ]
    if eos_position is None:
        features.append("target_eos_absent")
    else:
        features.append(f"target_eos_{_eos_bucket(eos_position, slot_count)}")
        if target[eos_position] == _EOS_PAD_ID:
            features.append("eos_pad_alias_termination")
        else:
            features.append("alternate_eot_termination")
        if eos_position < slot_count - 1:
            features.append("pad_suffix")

    fixed_kind = seed % 4
    fixed_position: int | None = None
    fixed_role: str | None = None
    if fixed_kind == 1 and eos_position is not None:
        fixed_position = eos_position
        fixed_role = "eos"
    elif fixed_kind == 2 and eos_position is not None and eos_position < slot_count - 1:
        fixed_position = eos_position + 1 + rng.randrange(slot_count - eos_position - 1)
        fixed_role = "pad"
    elif fixed_kind == 3 and content_endpoint > 0:
        fixed_position = rng.randrange(content_endpoint)
        fixed_role = "ordinary"
    elif fixed_kind != 0:
        fixed_position = rng.randrange(slot_count)
        if eos_position is None or fixed_position < eos_position:
            fixed_role = "ordinary"
        elif fixed_position == eos_position:
            fixed_role = "eos"
        else:
            fixed_role = "pad"
    if fixed_position is not None:
        canvas[fixed_position] = target[fixed_position]
        rows[fixed_position] = (target[fixed_position],)
        features.extend(("fixed_position", f"fixed_{fixed_role}"))

    proposals: list[Proposal] = []

    def add_proposal(position: int, token_id: int, weight: int) -> None:
        proposals.append(Proposal(len(proposals), position, token_id, weight))

    for position, row in enumerate(rows):
        add_proposal(position, target[position], rng.randint(1, 9))
        for token_id in row:
            if token_id != target[position] and rng.random() < 0.55:
                add_proposal(position, token_id, rng.randint(0, 9))
    add_proposal(0, target[0], rng.randint(1, 5))
    add_proposal(0, target[0], 0)

    target_bytes = bytes(content_tokens[index] + ord("a") for index in range(len(content_tokens)))
    forced_infeasible = seed % 7 == 0
    grammar_word = b"z" if forced_infeasible else target_bytes
    if forced_infeasible:
        features.append("forced_infeasible_intersection")
        grammar_kind = "unrepresented_z"
    else:
        grammar_kind = f"exact_target_bytes_{target_bytes.hex() or 'epsilon'}"
    return RandomEOSFiniteSlotInstance(
        seed=seed,
        grammar=_exact_word_grammar(grammar_word),
        grammar_kind=grammar_kind,
        canvas=tuple(canvas),
        support_rows=tuple(rows),
        emissions=_EMISSIONS,
        proposals=tuple(proposals),
        eos_policy=policy,
        target_token_ids=tuple(target),
        target_eos_position=eos_position,
        features=tuple(features),
    )


def eos_finite_slot_grammar_family_sha256() -> str:
    """Fingerprint all exact-word grammars reachable by the generator."""

    words = [b""]
    for length in range(1, 6):
        words.extend(bytes(values) for values in product((ord("a"), ord("b")), repeat=length))
    words.append(b"z")
    payload = json.dumps(
        [_exact_word_grammar(word).to_dict() for word in words],
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def check_eos_finite_slot_instance(
    instance: RandomEOSFiniteSlotInstance,
) -> EOSFiniteSlotCaseReport:
    """Compare independent full-row enumeration with the EOS lattice and solver."""

    if not isinstance(instance, RandomEOSFiniteSlotInstance):
        raise TypeError("instance must be a RandomEOSFiniteSlotInstance")
    oracle = _enumerate_paths(instance)
    lattice = build_eos_lattice(
        token_lattice=build_token_lattice(
            support=instance.support,
            proposals=instance.proposals,
        ),
        adapter=instance.adapter,
        policy=instance.eos_policy,
    )
    lattice_paths = _audit_lattice_paths(instance, lattice, oracle)
    solve = solve_cfg_on_epsilon_dag(instance.grammar, lattice.graph)
    if solve.status is not oracle.status:
        _mismatch(
            instance,
            "status_agreement",
            f"oracle={oracle.status.value} solver={solve.status.value}",
        )
    checks = {
        "status_agreement": 1,
        "legal_path_set_agreement": 1,
        "lattice_path_validation": len(lattice_paths),
        "lattice_path_metadata": len(lattice_paths),
    }
    witness_bucket: str | None = None
    if oracle.status is SolveStatus.OPTIMAL:
        if solve.certificate is None or solve.objective_value is None:
            _mismatch(instance, "optimal_payload", "solver omitted its certificate")
        assert solve.certificate is not None and solve.objective_value is not None
        if oracle.objective_value is None or not isclose(
            solve.objective_value,
            oracle.objective_value,
            rel_tol=1e-12,
            abs_tol=1e-12,
        ):
            _mismatch(
                instance,
                "objective_agreement",
                f"oracle={oracle.objective_value} solver={solve.objective_value}",
            )
        path = lattice.reconstruct_original_path(solve.certificate.witness_graph_edge_ids)
        lattice.validate_path(path)
        if path.token_path.token_ids not in oracle.optimal_token_paths:
            _mismatch(
                instance,
                "optimal_witness_membership",
                f"witness={path.token_path.token_ids!r}",
            )
        expected = oracle.legal_paths[path.token_path.token_ids]
        _compare_path_metadata(instance, path, expected)
        result = ExactCommitResult(
            status=SolveStatus.OPTIMAL,
            exactness_scope=instance.support.exactness_scope,
            objective_value=path.objective_value,
            selected_proposal_ids=path.matched_proposal_ids,
            witness_token_ids=path.token_path.token_ids,
            witness_terminal_labels=path.terminal_labels,
            witness_graph_edge_ids=path.graph_edge_ids,
            witness_eos_position=path.eos_position,
            witness_content_endpoint_slot=path.content_endpoint_slot,
            diagnostics={
                "backend": "python_epsilon_dag_reference",
                "finite_slot_policy": "all_physical_slots_consumed",
            },
        )
        validation = validate_exact_commit_certificate(
            result,
            expected_scope=instance.support.exactness_scope,
            canvas=instance.canvas,
            proposals=instance.proposals,
            graph=lattice.graph,
            grammar_recognizer=lambda labels: recognizes_cnf(instance.grammar, labels),
            support_validator=lambda tokens: _support_accepts(instance, tokens),
            eos_policy=instance.eos_policy,
            eos_adapter=instance.adapter,
        )
        if not validation.is_valid:
            _mismatch(
                instance,
                "certificate_validation",
                json.dumps(validation.to_dict(), sort_keys=True),
            )
        if len(result.witness_token_ids) != len(instance.canvas):
            _mismatch(instance, "exact_slot_consumption", "optimal witness length changed")
        checks.update(
            {
                "objective_agreement": 1,
                "optimal_witness_membership": 1,
                "certificate_validation": 1,
                "exact_slot_consumption": 1,
                "result_path_metadata": 1,
            }
        )
        witness_bucket = _eos_bucket(path.eos_position, len(instance.canvas))
    else:
        if solve.objective_value is not None or solve.certificate is not None:
            _mismatch(instance, "nonoptimal_payload", "infeasible solve exposed a certificate")
        checks["nonoptimal_payload"] = 1

    return EOSFiniteSlotCaseReport(
        seed=instance.seed,
        status=oracle.status,
        enumerated_token_paths=oracle.enumerated_token_paths,
        legal_eos_paths=len(oracle.legal_paths),
        grammar_valid_paths=oracle.grammar_valid_paths,
        witness_eos_bucket=witness_bucket,
        property_checks=checks,
        features=instance.features,
    )


def run_eos_finite_slot_campaign(
    *,
    campaign_name: str,
    seed_start: int,
    case_count: int,
    failure_directory: str | Path | None = None,
    metadata: Mapping[str, str] | None = None,
    checker: Callable[[RandomEOSFiniteSlotInstance], EOSFiniteSlotCaseReport] = (
        check_eos_finite_slot_instance
    ),
) -> EOSFiniteSlotCampaignSummary:
    """Run a contiguous seed range and persist every exact failing input."""

    if not isinstance(campaign_name, str) or not campaign_name.strip():
        raise ValueError("campaign_name must be non-empty")
    if isinstance(seed_start, bool) or not isinstance(seed_start, int) or seed_start < 0:
        raise ValueError("seed_start must be a non-negative integer")
    if isinstance(case_count, bool) or not isinstance(case_count, int) or case_count <= 0:
        raise ValueError("case_count must be a positive integer")
    failure_path = None if failure_directory is None else Path(failure_directory)
    if failure_path is not None:
        failure_path.mkdir(parents=True, exist_ok=True)

    passed = 0
    total_paths = 0
    legal_paths = 0
    grammar_valid_paths = 0
    status_counts: dict[str, int] = {}
    feature_counts: dict[str, int] = {}
    witness_counts: dict[str, int] = {}
    property_counts: dict[str, int] = {}
    failures: list[EOSFiniteSlotFailure] = []
    for seed in range(seed_start, seed_start + case_count):
        instance = generate_random_eos_finite_slot_instance(seed)
        try:
            report = checker(instance)
        except Exception as error:
            fixture_file: str | None = None
            failure_file: str | None = None
            if failure_path is not None:
                fixture_name = f"seed-{seed}.json"
                failure_name = f"seed-{seed}.failure.json"
                instance.write_json(failure_path / fixture_name)
                (failure_path / failure_name).write_text(
                    json.dumps(
                        {
                            "schema_version": 1,
                            "campaign_name": campaign_name,
                            "seed": seed,
                            "error_type": type(error).__name__,
                            "message": str(error),
                            "fixture_file": fixture_name,
                        },
                        indent=2,
                        sort_keys=True,
                    )
                    + "\n",
                    encoding="utf-8",
                )
                fixture_file = fixture_name
                failure_file = failure_name
            failures.append(
                EOSFiniteSlotFailure(
                    seed=seed,
                    error_type=type(error).__name__,
                    message=str(error),
                    fixture_file=fixture_file,
                    failure_file=failure_file,
                )
            )
            continue
        passed += 1
        total_paths += report.enumerated_token_paths
        legal_paths += report.legal_eos_paths
        grammar_valid_paths += report.grammar_valid_paths
        status_counts[report.status.value] = status_counts.get(report.status.value, 0) + 1
        for feature in report.features:
            feature_counts[feature] = feature_counts.get(feature, 0) + 1
        if report.witness_eos_bucket is not None:
            witness_counts[report.witness_eos_bucket] = (
                witness_counts.get(report.witness_eos_bucket, 0) + 1
            )
        for property_name, count in report.property_checks.items():
            property_counts[property_name] = property_counts.get(property_name, 0) + count

    return EOSFiniteSlotCampaignSummary(
        campaign_name=campaign_name,
        seed_start=seed_start,
        case_count=case_count,
        passed_cases=passed,
        failed_cases=len(failures),
        total_enumerated_token_paths=total_paths,
        total_legal_eos_paths=legal_paths,
        total_grammar_valid_paths=grammar_valid_paths,
        status_counts=status_counts,
        feature_case_counts=feature_counts,
        witness_eos_position_counts=witness_counts,
        property_checks=property_counts,
        failures=tuple(failures),
        metadata={} if metadata is None else metadata,
    )


def _interpret_token_path(
    instance: RandomEOSFiniteSlotInstance,
    token_ids: tuple[int, ...],
) -> _InterpretedPath | None:
    if len(token_ids) != len(instance.canvas):
        return None
    if any(
        fixed is not None and token_ids[position] != fixed
        for position, fixed in enumerate(instance.canvas)
    ):
        return None
    policy = instance.eos_policy
    assert policy.pad_token_id is not None
    after_eos = False
    eos_position: int | None = None
    roles: list[TokenRole] = []
    emitted = bytearray()
    for position, token_id in enumerate(token_ids):
        if not 0 <= token_id < len(instance.emissions):
            return None
        if after_eos:
            if token_id != policy.pad_token_id:
                return None
            roles.append(TokenRole.PAD)
            continue
        if token_id in policy.termination_token_ids:
            roles.append(TokenRole.EOS)
            eos_position = position
            after_eos = True
            continue
        if token_id == policy.pad_token_id:
            return None
        emission = instance.emissions[token_id]
        if emission is None:
            return None
        roles.append(TokenRole.ORDINARY)
        emitted.extend(emission)
    if policy.mode is EOSMode.REQUIRED and eos_position is None:
        return None
    matched = tuple(
        proposal
        for proposal in instance.proposals
        if proposal.weight > 0 and token_ids[proposal.position] == proposal.token_id
    )
    return _InterpretedPath(
        token_ids=token_ids,
        token_roles=tuple(roles),
        emitted_bytes=bytes(emitted),
        eos_position=eos_position,
        content_endpoint_slot=(len(token_ids) if eos_position is None else eos_position),
        objective_value=fsum(proposal.weight for proposal in matched),
        selected_proposal_ids=tuple(proposal.proposal_id for proposal in matched),
    )


def _enumerate_paths(instance: RandomEOSFiniteSlotInstance) -> _OracleOutcome:
    legal: dict[tuple[int, ...], _InterpretedPath] = {}
    grammar_valid: list[_InterpretedPath] = []
    enumerated = 0
    for token_ids in product(*instance.support_rows):
        enumerated += 1
        interpreted = _interpret_token_path(instance, token_ids)
        if interpreted is None:
            continue
        legal[token_ids] = interpreted
        if recognizes_cnf(instance.grammar, tuple(interpreted.emitted_bytes)):
            grammar_valid.append(interpreted)
    if not grammar_valid:
        return _OracleOutcome(
            status=SolveStatus.INFEASIBLE_ON_SUPPORT,
            objective_value=None,
            optimal_token_paths=frozenset(),
            legal_paths=legal,
            enumerated_token_paths=enumerated,
            grammar_valid_paths=0,
        )
    objective = max(path.objective_value for path in grammar_valid)
    optimal_paths = frozenset(
        path.token_ids
        for path in grammar_valid
        if isclose(path.objective_value, objective, rel_tol=1e-12, abs_tol=1e-12)
    )
    return _OracleOutcome(
        status=SolveStatus.OPTIMAL,
        objective_value=objective,
        optimal_token_paths=optimal_paths,
        legal_paths=legal,
        enumerated_token_paths=enumerated,
        grammar_valid_paths=len(grammar_valid),
    )


def _audit_lattice_paths(
    instance: RandomEOSFiniteSlotInstance,
    lattice: EOSLattice,
    oracle: _OracleOutcome,
) -> Mapping[tuple[int, ...], _InterpretedPath]:
    lattice_paths = {path.token_path.token_ids: path for path in lattice.iter_paths()}
    if set(lattice_paths) != set(oracle.legal_paths):
        missing = sorted(set(oracle.legal_paths) - set(lattice_paths))
        extra = sorted(set(lattice_paths) - set(oracle.legal_paths))
        _mismatch(
            instance,
            "legal_path_set_agreement",
            f"missing={missing!r} extra={extra!r}",
        )
    for token_ids, path in lattice_paths.items():
        lattice.validate_path(path)
        expected = oracle.legal_paths[token_ids]
        _compare_path_metadata(instance, path, expected)
        if len(path.token_path.token_ids) != len(instance.canvas):
            _mismatch(instance, "lattice_slot_consumption", f"token_ids={token_ids!r}")
    return MappingProxyType(dict(oracle.legal_paths))


def _compare_path_metadata(
    instance: RandomEOSFiniteSlotInstance,
    path: EOSLatticePath,
    expected: _InterpretedPath,
) -> None:
    token_path = path.token_path
    if path.token_roles != expected.token_roles:
        _mismatch(instance, "path_roles", f"token_ids={expected.token_ids!r}")
    if path.emitted_bytes != expected.emitted_bytes:
        _mismatch(instance, "path_bytes", f"token_ids={expected.token_ids!r}")
    if path.eos_position != expected.eos_position:
        _mismatch(instance, "path_eos_position", f"token_ids={expected.token_ids!r}")
    if path.content_endpoint_slot != expected.content_endpoint_slot:
        _mismatch(instance, "path_content_endpoint", f"token_ids={expected.token_ids!r}")
    if not isclose(
        path.objective_value,
        expected.objective_value,
        rel_tol=1e-12,
        abs_tol=1e-12,
    ):
        _mismatch(instance, "path_objective", f"token_ids={expected.token_ids!r}")
    if Counter(path.matched_proposal_ids) != Counter(expected.selected_proposal_ids):
        _mismatch(instance, "path_proposals", f"token_ids={expected.token_ids!r}")
    if token_path.token_ids != expected.token_ids:
        _mismatch(instance, "path_token_ids", f"token_ids={expected.token_ids!r}")


def _support_accepts(
    instance: RandomEOSFiniteSlotInstance,
    token_ids: tuple[int, ...],
) -> bool:
    return len(token_ids) == len(instance.support_rows) and all(
        token_id in instance.support_rows[position] for position, token_id in enumerate(token_ids)
    )


def _eos_bucket(eos_position: int | None, slot_count: int) -> str:
    if eos_position is None:
        return "absent_optional"
    if eos_position == 0:
        return "first_slot"
    if eos_position == slot_count - 1:
        return "final_slot"
    return "middle_slot"


def _mismatch(
    instance: RandomEOSFiniteSlotInstance,
    property_name: str,
    details: str,
) -> NoReturn:
    raise EOSFiniteSlotDifferentialMismatch(
        seed=instance.seed,
        property_name=property_name,
        details=details,
    )
