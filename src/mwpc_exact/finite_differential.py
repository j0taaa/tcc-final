"""Replayable finite token/byte-lattice differential correctness campaigns.

The exhaustive oracle in this module enumerates token IDs directly from the
explicit per-position rows.  It computes bytes and MWPC rewards from the
frozen vocabulary and proposal records, without consulting either parser.
The byte-lattice audit is separate and checks that expansion preserves those
independently computed values and provenance.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from itertools import product
from math import fsum, isclose
from pathlib import Path
from random import Random
from types import MappingProxyType
from typing import NoReturn, Self

from mwpc_exact.byte_lattice import ByteLatticePath, build_byte_lattice
from mwpc_exact.finite_solver import ExactBackend, solve_exact_commit
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

FINITE_LATTICE_GENERATOR_SCHEMA_VERSION = 1
_BYTE_A = ord("a")
_BYTE_B = ord("b")
_BYTE_Z = ord("z")


class FiniteLatticeDifferentialMismatch(AssertionError):
    """One deterministic seed violated a finite-lattice exactness property."""

    def __init__(self, *, seed: int, property_name: str, details: str) -> None:
        self.seed = seed
        self.property_name = property_name
        self.details = details
        super().__init__(f"seed={seed} property={property_name}: {details}")


@dataclass(frozen=True, slots=True)
class RandomFiniteLatticeInstance:
    """One deterministic finite vocabulary/support/grammar intersection."""

    seed: int
    grammar_kind: str
    grammar: CnfGrammar
    canvas: tuple[int | None, ...]
    support_rows: tuple[tuple[int, ...], ...]
    emissions: tuple[bytes, ...]
    proposals: tuple[Proposal, ...]
    features: tuple[str, ...]

    def __post_init__(self) -> None:
        if isinstance(self.seed, bool) or not isinstance(self.seed, int) or self.seed < 0:
            raise ValueError("seed must be a non-negative integer")
        if not isinstance(self.grammar_kind, str) or not self.grammar_kind.strip():
            raise ValueError("grammar_kind must be a non-empty string")
        if not isinstance(self.grammar, CnfGrammar):
            raise TypeError("grammar must be a CnfGrammar")
        canvas = tuple(self.canvas)
        rows = tuple(tuple(row) for row in self.support_rows)
        emissions = tuple(self.emissions)
        proposals = tuple(self.proposals)
        features = tuple(self.features)
        if not emissions or not all(
            isinstance(emission, bytes) and emission for emission in emissions
        ):
            raise ValueError("emissions must contain non-empty byte strings")
        if not all(isinstance(proposal, Proposal) for proposal in proposals):
            raise TypeError("proposals must contain only Proposal instances")
        if any(not isinstance(feature, str) or not feature.strip() for feature in features):
            raise ValueError("features must contain non-empty strings")
        if len(set(features)) != len(features):
            raise ValueError("features must not contain duplicates")
        object.__setattr__(self, "canvas", canvas)
        object.__setattr__(self, "support_rows", rows)
        object.__setattr__(self, "emissions", emissions)
        object.__setattr__(self, "proposals", proposals)
        object.__setattr__(self, "features", features)
        # Exercise the public construction boundary while validating fixtures.
        validated_support = self.support
        if validated_support.rows != rows:
            raise AssertionError("fixture support validation changed canonical rows")

    @property
    def adapter(self) -> CompositionalByteLevelAdapter:
        """Return the exact compositional tokenizer mapping for this fixture."""

        return CompositionalByteLevelAdapter(self.emissions)

    @property
    def support(self) -> PerPositionSupport:
        """Reconstruct the explicit represented support without hidden additions."""

        return build_per_position_support(
            canvas=self.canvas,
            policy=SupportPolicy(
                kind=SupportKind.EXPLICIT,
                vocabulary_size=len(self.emissions),
            ),
            explicit_support=dict(enumerate(self.support_rows)),
            proposals=self.proposals,
        )

    def to_dict(self) -> dict[str, object]:
        """Serialize every input needed to replay a failing seed offline."""

        return {
            "schema_version": FINITE_LATTICE_GENERATOR_SCHEMA_VERSION,
            "seed": self.seed,
            "grammar_kind": self.grammar_kind,
            "grammar": self.grammar.to_dict(),
            "canvas": list(self.canvas),
            "support_rows": [list(row) for row in self.support_rows],
            "emissions_hex_by_token_id": [emission.hex() for emission in self.emissions],
            "proposals": [
                {
                    "proposal_id": proposal.proposal_id,
                    "position": proposal.position,
                    "token_id": proposal.token_id,
                    "weight": proposal.weight,
                    "model_confidence": proposal.model_confidence,
                }
                for proposal in self.proposals
            ],
            "features": list(self.features),
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, object]) -> Self:
        """Reconstruct and validate a serialized randomized fixture."""

        required = {
            "schema_version",
            "seed",
            "grammar_kind",
            "grammar",
            "canvas",
            "support_rows",
            "emissions_hex_by_token_id",
            "proposals",
            "features",
        }
        unknown = set(data) - required
        missing = required - set(data)
        if unknown or missing:
            raise ValueError(
                f"invalid finite-lattice fixture fields (missing={sorted(missing)!r}, "
                f"unknown={sorted(unknown)!r})"
            )
        schema_version = _integer(data["schema_version"], "schema_version")
        if schema_version != FINITE_LATTICE_GENERATOR_SCHEMA_VERSION:
            raise ValueError(f"unsupported finite-lattice schema version: {schema_version}")
        grammar_data = _mapping(data["grammar"], "grammar")
        canvas = tuple(
            None if item is None else _integer(item, "canvas item")
            for item in _sequence(data["canvas"], "canvas")
        )
        support_rows = tuple(
            tuple(_integer(item, "support row item") for item in _sequence(row, "support row"))
            for row in _sequence(data["support_rows"], "support_rows")
        )
        emissions = tuple(
            bytes.fromhex(_string(item, "emission"))
            for item in _sequence(
                data["emissions_hex_by_token_id"], "emissions_hex_by_token_id"
            )
        )
        proposals = tuple(
            _proposal_from_dict(_mapping(item, "proposal"))
            for item in _sequence(data["proposals"], "proposals")
        )
        return cls(
            seed=_integer(data["seed"], "seed"),
            grammar_kind=_string(data["grammar_kind"], "grammar_kind"),
            grammar=CnfGrammar.from_dict(grammar_data),
            canvas=canvas,
            support_rows=support_rows,
            emissions=emissions,
            proposals=proposals,
            features=tuple(
                _string(item, "feature") for item in _sequence(data["features"], "features")
            ),
        )

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, sort_keys=True) + "\n"

    @classmethod
    def from_json(cls, payload: str) -> Self:
        parsed: object = json.loads(payload)
        return cls.from_dict(_mapping(parsed, "finite-lattice fixture"))

    def write_json(self, path: str | Path) -> None:
        output = Path(path)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(self.to_json(), encoding="utf-8")

    @classmethod
    def read_json(cls, path: str | Path) -> Self:
        return cls.from_json(Path(path).read_text(encoding="utf-8"))


@dataclass(frozen=True, slots=True)
class FiniteLatticeCaseReport:
    seed: int
    status: SolveStatus
    enumerated_token_paths: int
    grammar_valid_paths: int
    property_checks: Mapping[str, int]
    features: tuple[str, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "property_checks", MappingProxyType(dict(self.property_checks)))


@dataclass(frozen=True, slots=True)
class FiniteLatticeFailure:
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
class FiniteLatticeCampaignSummary:
    campaign_name: str
    seed_start: int
    case_count: int
    passed_cases: int
    failed_cases: int
    total_enumerated_token_paths: int
    total_grammar_valid_paths: int
    status_counts: Mapping[str, int]
    feature_case_counts: Mapping[str, int]
    property_checks: Mapping[str, int]
    failures: tuple[FiniteLatticeFailure, ...]
    metadata: Mapping[str, str]

    def __post_init__(self) -> None:
        if not self.campaign_name.strip():
            raise ValueError("campaign_name must be non-empty")
        if self.passed_cases + self.failed_cases != self.case_count:
            raise ValueError("campaign passed/failed counts must equal case_count")
        for field_name in (
            "status_counts",
            "feature_case_counts",
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
            "campaign": "m6_finite_lattice_differential",
            "campaign_name": self.campaign_name,
            "seed_start": self.seed_start,
            "case_count": self.case_count,
            "passed_cases": self.passed_cases,
            "failed_cases": self.failed_cases,
            "total_enumerated_token_paths": self.total_enumerated_token_paths,
            "total_grammar_valid_paths": self.total_grammar_valid_paths,
            "status_counts": dict(self.status_counts),
            "feature_case_counts": dict(self.feature_case_counts),
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
class _OracleOutcome:
    status: SolveStatus
    objective_value: float | None
    optimal_token_paths: frozenset[tuple[int, ...]]
    enumerated_token_paths: int
    grammar_valid_paths: int


def generate_random_finite_lattice_instance(seed: int) -> RandomFiniteLatticeInstance:
    """Generate a tiny case with mandatory tokenizer/provenance stress features."""

    if isinstance(seed, bool) or not isinstance(seed, int) or seed < 0:
        raise ValueError("seed must be a non-negative integer")
    rng = Random(seed)
    vocabulary_size = 5 + rng.randrange(2)
    duplicate_emission = rng.choice((b"a", b"b"))
    emissions = [duplicate_emission, duplicate_emission]
    emissions.append(_random_emission(rng, minimum_length=2, maximum_length=3))
    while len(emissions) < vocabulary_size:
        emissions.append(_random_emission(rng, minimum_length=1, maximum_length=3))

    slot_count = 2 + rng.randrange(2)
    rows: list[tuple[int, ...]] = []
    for position in range(slot_count):
        represented = {0}
        if position == 0:
            represented.update((1, 2))
        for token_id in range(1, vocabulary_size):
            if rng.random() < 0.45:
                represented.add(token_id)
        rows.append(tuple(sorted(represented)))

    canvas: list[int | None] = [None] * slot_count
    features = [
        "explicit_represented_support",
        "integer_proposal_weights",
        "multi_byte_token",
        "same_bytes_distinct_token_ids",
        "variable_byte_lengths",
        "multiple_proposals_same_choice",
        "zero_weight_proposal",
    ]
    if seed % 2 == 0:
        fixed_position = slot_count - 1
        fixed_token = rng.choice((0, 1))
        canvas[fixed_position] = fixed_token
        rows[fixed_position] = (fixed_token,)
        features.append("fixed_position")

    proposals: list[Proposal] = []

    def add_proposal(position: int, token_id: int, weight: int) -> None:
        proposals.append(Proposal(len(proposals), position, token_id, weight))

    # The duplicate byte strings receive distinguishable token-level reward,
    # and token 1 carries two positive proposal IDs to stress selected-set provenance.
    add_proposal(0, 0, 0)
    add_proposal(0, 1, 2)
    add_proposal(0, 1, 3)
    add_proposal(0, 2, rng.randint(1, 5))
    for position in range(1, slot_count):
        token_id = rng.choice(rows[position])
        add_proposal(position, token_id, rng.randint(0, 9))

    grammar_kind, grammar = _grammar_for_seed(seed)
    if grammar_kind == "unrepresented_z":
        features.append("forced_infeasible_intersection")
    return RandomFiniteLatticeInstance(
        seed=seed,
        grammar_kind=grammar_kind,
        grammar=grammar,
        canvas=tuple(canvas),
        support_rows=tuple(rows),
        emissions=tuple(emissions),
        proposals=tuple(proposals),
        features=tuple(features),
    )


def finite_grammar_family_sha256() -> str:
    """Fingerprint the complete generated CNF family used by the campaign."""

    payload = json.dumps(
        [_grammar_for_seed(seed)[1].to_dict() for seed in range(4)],
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def check_finite_lattice_instance(
    instance: RandomFiniteLatticeInstance,
    *,
    backends: Sequence[ExactBackend] = (ExactBackend.PYTHON, ExactBackend.RUST),
) -> FiniteLatticeCaseReport:
    """Compare selected backends to enumeration and audit byte expansion."""

    if not isinstance(instance, RandomFiniteLatticeInstance):
        raise TypeError("instance must be a RandomFiniteLatticeInstance")
    backend_items = tuple(backends)
    if not backend_items or not all(isinstance(item, ExactBackend) for item in backend_items):
        raise ValueError("backends must contain at least one ExactBackend")
    if len(set(backend_items)) != len(backend_items):
        raise ValueError("backends must not contain duplicates")

    expanded_paths = _audit_byte_expansion(instance)
    oracle = _enumerate_token_paths(instance)
    results = {
        backend: solve_exact_commit(
            instance.grammar,
            canvas=instance.canvas,
            support=instance.support,
            proposals=instance.proposals,
            tokenizer_adapter=instance.adapter,
            backend=backend,
        )
        for backend in backend_items
    }
    statuses = {result.status for result in results.values()} | {oracle.status}
    if len(statuses) != 1:
        rendered = " ".join(
            [f"oracle={oracle.status.value}"]
            + [f"{backend.value}={results[backend].status.value}" for backend in backend_items]
        )
        _mismatch(instance, "status_agreement", rendered)
    checks = {
        "status_agreement": 1,
        "byte_expansion_path_validation": len(expanded_paths),
        "byte_expansion_score": len(expanded_paths),
        "byte_expansion_provenance": len(expanded_paths),
    }
    for backend, result in results.items():
        if result.exactness_scope != instance.support.exactness_scope:
            _mismatch(
                instance,
                "exactness_scope",
                f"backend={backend.value} returned a different represented-support scope",
            )
    checks["exactness_scope"] = len(results)

    if oracle.status is SolveStatus.OPTIMAL:
        assert oracle.objective_value is not None
        for backend, result in results.items():
            _validate_optimal_result(
                instance,
                backend=backend,
                result=result,
                oracle=oracle,
                expanded_paths=expanded_paths,
            )
        checks.update(
            {
                "objective_agreement": len(results),
                "optimal_witness_membership": len(results),
                "certificate_validation": len(results),
                "result_byte_provenance": len(results),
                "result_proposal_provenance": len(results),
            }
        )
    else:
        for backend, result in results.items():
            if (
                result.objective_value is not None
                or result.selected_proposal_ids
                or result.witness_token_ids
                or result.witness_terminal_labels
                or result.witness_graph_edge_ids
            ):
                _mismatch(
                    instance,
                    "nonoptimal_payload",
                    f"backend={backend.value} exposed partial optimal data",
                )
        checks["nonoptimal_payload"] = len(results)

    return FiniteLatticeCaseReport(
        seed=instance.seed,
        status=oracle.status,
        enumerated_token_paths=oracle.enumerated_token_paths,
        grammar_valid_paths=oracle.grammar_valid_paths,
        property_checks=checks,
        features=instance.features,
    )


def run_finite_lattice_campaign(
    *,
    campaign_name: str,
    seed_start: int,
    case_count: int,
    failure_directory: str | Path | None = None,
    metadata: Mapping[str, str] | None = None,
    checker: Callable[[RandomFiniteLatticeInstance], FiniteLatticeCaseReport] = (
        check_finite_lattice_instance
    ),
) -> FiniteLatticeCampaignSummary:
    """Run a contiguous seed campaign and persist exact replay data on failure."""

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
    valid_paths = 0
    status_counts: dict[str, int] = {}
    feature_counts: dict[str, int] = {}
    property_counts: dict[str, int] = {}
    failures: list[FiniteLatticeFailure] = []
    for seed in range(seed_start, seed_start + case_count):
        instance = generate_random_finite_lattice_instance(seed)
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
                FiniteLatticeFailure(
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
        valid_paths += report.grammar_valid_paths
        status_counts[report.status.value] = status_counts.get(report.status.value, 0) + 1
        for feature in report.features:
            feature_counts[feature] = feature_counts.get(feature, 0) + 1
        for property_name, count in report.property_checks.items():
            property_counts[property_name] = property_counts.get(property_name, 0) + count

    return FiniteLatticeCampaignSummary(
        campaign_name=campaign_name,
        seed_start=seed_start,
        case_count=case_count,
        passed_cases=passed,
        failed_cases=len(failures),
        total_enumerated_token_paths=total_paths,
        total_grammar_valid_paths=valid_paths,
        status_counts=status_counts,
        feature_case_counts=feature_counts,
        property_checks=property_counts,
        failures=tuple(failures),
        metadata={} if metadata is None else metadata,
    )


def _audit_byte_expansion(
    instance: RandomFiniteLatticeInstance,
) -> Mapping[tuple[int, ...], ByteLatticePath]:
    token_lattice = build_token_lattice(
        support=instance.support,
        proposals=instance.proposals,
    )
    byte_lattice = build_byte_lattice(token_lattice=token_lattice, adapter=instance.adapter)
    expanded_paths: dict[tuple[int, ...], ByteLatticePath] = {}
    for path in byte_lattice.iter_paths():
        byte_lattice.validate_path(path)
        token_ids = path.token_path.token_ids
        expected_bytes, expected_objective, expected_proposals = _path_metadata(
            instance, token_ids
        )
        if path.emitted_bytes != expected_bytes:
            _mismatch(instance, "byte_expansion_bytes", f"token_ids={token_ids!r}")
        if not isclose(
            path.objective_value,
            expected_objective,
            rel_tol=1e-12,
            abs_tol=1e-12,
        ):
            _mismatch(
                instance,
                "byte_expansion_score",
                f"token_ids={token_ids!r} lattice={path.objective_value} "
                f"expected={expected_objective}",
            )
        if path.matched_proposal_ids != expected_proposals:
            _mismatch(
                instance,
                "byte_expansion_provenance",
                f"token_ids={token_ids!r} lattice={path.matched_proposal_ids!r} "
                f"expected={expected_proposals!r}",
            )
        expanded_paths[token_ids] = path
    expected_count = 1
    for row in instance.support_rows:
        expected_count *= len(row)
    if len(expanded_paths) != expected_count:
        _mismatch(
            instance,
            "byte_expansion_path_count",
            f"lattice={len(expanded_paths)} expected={expected_count}",
        )
    return MappingProxyType(expanded_paths)


def _enumerate_token_paths(instance: RandomFiniteLatticeInstance) -> _OracleOutcome:
    valid: list[tuple[tuple[int, ...], float]] = []
    enumerated = 0
    for token_ids in product(*instance.support_rows):
        enumerated += 1
        emitted_bytes, objective, _ = _path_metadata(instance, token_ids)
        if recognizes_cnf(instance.grammar, tuple(emitted_bytes)):
            valid.append((token_ids, objective))
    if not valid:
        return _OracleOutcome(
            status=SolveStatus.INFEASIBLE_ON_SUPPORT,
            objective_value=None,
            optimal_token_paths=frozenset(),
            enumerated_token_paths=enumerated,
            grammar_valid_paths=0,
        )
    objective = max(item[1] for item in valid)
    optimal = frozenset(
        token_ids
        for token_ids, value in valid
        if isclose(value, objective, rel_tol=1e-12, abs_tol=1e-12)
    )
    return _OracleOutcome(
        status=SolveStatus.OPTIMAL,
        objective_value=objective,
        optimal_token_paths=optimal,
        enumerated_token_paths=enumerated,
        grammar_valid_paths=len(valid),
    )


def _validate_optimal_result(
    instance: RandomFiniteLatticeInstance,
    *,
    backend: ExactBackend,
    result: ExactCommitResult,
    oracle: _OracleOutcome,
    expanded_paths: Mapping[tuple[int, ...], ByteLatticePath],
) -> None:
    if result.status is not SolveStatus.OPTIMAL or result.objective_value is None:
        _mismatch(instance, "optimal_payload", f"backend={backend.value} omitted objective")
    assert oracle.objective_value is not None and result.objective_value is not None
    if not isclose(
        result.objective_value,
        oracle.objective_value,
        rel_tol=1e-12,
        abs_tol=1e-12,
    ):
        _mismatch(
            instance,
            "objective_agreement",
            f"backend={backend.value} solver={result.objective_value} "
            f"oracle={oracle.objective_value}",
        )
    if result.witness_token_ids not in oracle.optimal_token_paths:
        _mismatch(
            instance,
            "optimal_witness_membership",
            f"backend={backend.value} witness={result.witness_token_ids!r}",
        )
    expected_bytes, expected_objective, expected_proposals = _path_metadata(
        instance, result.witness_token_ids
    )
    if tuple(expected_bytes) != result.witness_terminal_labels:
        _mismatch(
            instance,
            "result_byte_provenance",
            f"backend={backend.value} terminal labels differ from token emissions",
        )
    if result.selected_proposal_ids != expected_proposals:
        _mismatch(
            instance,
            "result_proposal_provenance",
            f"backend={backend.value} selected={result.selected_proposal_ids!r} "
            f"expected={expected_proposals!r}",
        )
    if not isclose(
        result.objective_value,
        expected_objective,
        rel_tol=1e-12,
        abs_tol=1e-12,
    ):
        _mismatch(instance, "result_score_recomputation", f"backend={backend.value}")
    expanded = expanded_paths[result.witness_token_ids]
    if result.witness_graph_edge_ids != expanded.graph_edge_ids:
        _mismatch(
            instance,
            "result_graph_provenance",
            f"backend={backend.value} graph-edge witness differs from token expansion",
        )
    validation = result.diagnostics.get("certificate_validation")
    if not isinstance(validation, Mapping) or validation.get("is_valid") is not True:
        _mismatch(
            instance,
            "certificate_validation",
            f"backend={backend.value} independent validator did not accept",
        )


def _path_metadata(
    instance: RandomFiniteLatticeInstance,
    token_ids: tuple[int, ...],
) -> tuple[bytes, float, tuple[int, ...]]:
    emitted_bytes = b"".join(instance.emissions[token_id] for token_id in token_ids)
    matched = tuple(
        proposal
        for position, token_id in enumerate(token_ids)
        for proposal in instance.proposals
        if proposal.position == position and proposal.token_id == token_id and proposal.weight > 0
    )
    return (
        emitted_bytes,
        fsum(proposal.weight for proposal in matched),
        tuple(proposal.proposal_id for proposal in matched),
    )


def _grammar_for_seed(seed: int) -> tuple[str, CnfGrammar]:
    terminals = (
        Terminal(10, _BYTE_A),
        Terminal(20, _BYTE_B),
        Terminal(30, _BYTE_Z),
    )
    grammar_index = seed % 4
    if grammar_index == 0:
        return (
            "unrepresented_z",
            CnfGrammar(
                nonterminals=(Nonterminal(0, "S"),),
                terminals=terminals,
                start_nonterminal_id=0,
                terminal_productions=(TerminalProduction(0, 0, 30),),
            ),
        )
    if grammar_index == 1:
        return (
            "any_nonempty_ab",
            CnfGrammar(
                nonterminals=(Nonterminal(0, "S"),),
                terminals=terminals,
                start_nonterminal_id=0,
                terminal_productions=(
                    TerminalProduction(0, 0, 10),
                    TerminalProduction(1, 0, 20),
                ),
                binary_productions=(BinaryProduction(2, 0, 0, 0),),
            ),
        )
    if grammar_index == 2:
        return (
            "exactly_two_ab",
            CnfGrammar(
                nonterminals=(Nonterminal(0, "S"), Nonterminal(1, "A")),
                terminals=terminals,
                start_nonterminal_id=0,
                terminal_productions=(
                    TerminalProduction(0, 1, 10),
                    TerminalProduction(1, 1, 20),
                ),
                binary_productions=(BinaryProduction(2, 0, 1, 1),),
            ),
        )
    return (
        "one_or_more_a",
        CnfGrammar(
            nonterminals=(Nonterminal(0, "S"),),
            terminals=terminals,
            start_nonterminal_id=0,
            terminal_productions=(TerminalProduction(0, 0, 10),),
            binary_productions=(BinaryProduction(1, 0, 0, 0),),
        ),
    )


def _random_emission(rng: Random, *, minimum_length: int, maximum_length: int) -> bytes:
    length = rng.randint(minimum_length, maximum_length)
    return bytes(rng.choice((_BYTE_A, _BYTE_B)) for _ in range(length))


def _proposal_from_dict(data: Mapping[str, object]) -> Proposal:
    required = {"proposal_id", "position", "token_id", "weight", "model_confidence"}
    if set(data) != required:
        raise ValueError("serialized proposal has invalid fields")
    weight = _real(data["weight"], "proposal weight")
    confidence_value = data["model_confidence"]
    confidence = (
        None
        if confidence_value is None
        else _real(confidence_value, "proposal model_confidence")
    )
    return Proposal(
        proposal_id=_integer(data["proposal_id"], "proposal_id"),
        position=_integer(data["position"], "proposal position"),
        token_id=_integer(data["token_id"], "proposal token_id"),
        weight=weight,
        model_confidence=confidence,
    )


def _mapping(value: object, field_name: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping) or not all(isinstance(key, str) for key in value):
        raise TypeError(f"{field_name} must be a string-keyed mapping")
    return value


def _sequence(value: object, field_name: str) -> Sequence[object]:
    if isinstance(value, (str, bytes)) or not isinstance(value, Sequence):
        raise TypeError(f"{field_name} must be a sequence")
    return value


def _integer(value: object, field_name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{field_name} must be an integer")
    return value


def _real(value: object, field_name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TypeError(f"{field_name} must be a real number")
    return float(value)


def _string(value: object, field_name: str) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{field_name} must be a string")
    return value


def _mismatch(
    instance: RandomFiniteLatticeInstance,
    property_name: str,
    details: str,
) -> NoReturn:
    raise FiniteLatticeDifferentialMismatch(
        seed=instance.seed,
        property_name=property_name,
        details=details,
    )


__all__ = [
    "FINITE_LATTICE_GENERATOR_SCHEMA_VERSION",
    "FiniteLatticeCampaignSummary",
    "FiniteLatticeCaseReport",
    "FiniteLatticeDifferentialMismatch",
    "RandomFiniteLatticeInstance",
    "check_finite_lattice_instance",
    "finite_grammar_family_sha256",
    "generate_random_finite_lattice_instance",
    "run_finite_lattice_campaign",
]
