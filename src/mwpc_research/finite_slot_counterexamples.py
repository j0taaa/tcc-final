"""Replayable counterexamples to unbounded ``Sigma*`` gap reasoning.

The abstract check in this module is deliberately weaker than the finite
solver: it asks whether a grammar-valid token sequence contains an ordered
set of proposal-token anchors, with arbitrary token gaps before, between, and
after them.  It does not allocate physical canvas slots.  The discrepancy is
the subject of the T703 fixtures, not an alternative exact solver.
"""

from __future__ import annotations

import json
from collections import Counter
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from math import fsum, isclose
from pathlib import Path
from typing import Self

from mwpc_exact.eos_lattice import EOSLatticePath, build_eos_lattice
from mwpc_exact.eos_policy import EOSMode, EOSPolicy
from mwpc_exact.reference.epsilon import solve_cfg_on_epsilon_dag
from mwpc_exact.reference.grammar import CnfGrammar
from mwpc_exact.reference.recognizer import recognizes_cnf
from mwpc_exact.support import SupportPolicy, build_per_position_support
from mwpc_exact.token_lattice import build_token_lattice
from mwpc_exact.tokenizer_bytes import CompositionalByteLevelAdapter
from mwpc_exact.types import ExactnessScope, Proposal, SolveStatus, SupportKind

FINITE_SLOT_COUNTEREXAMPLE_SCHEMA_VERSION = 1
ABSTRACT_SIGMA_STAR_SEMANTICS = (
    "ordered proposal-token anchors separated and surrounded by unbounded token Sigma* "
    "gaps; physical canvas slots and the required EOS token are not allocated"
)


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


def _exact_fields(
    data: Mapping[str, object],
    required: set[str],
    field_name: str,
) -> None:
    missing = required - set(data)
    unknown = set(data) - required
    if missing or unknown:
        raise ValueError(
            f"invalid {field_name} fields (missing={sorted(missing)!r}, "
            f"unknown={sorted(unknown)!r})"
        )


def _integer_tuple(value: object, field_name: str) -> tuple[int, ...]:
    return tuple(
        _non_negative_integer(item, f"{field_name} item") for item in _sequence(value, field_name)
    )


def _proposal_from_dict(data: Mapping[str, object]) -> Proposal:
    _exact_fields(data, {"proposal_id", "position", "token_id", "weight"}, "proposal")
    return Proposal(
        proposal_id=_non_negative_integer(data["proposal_id"], "proposal_id"),
        position=_non_negative_integer(data["position"], "proposal position"),
        token_id=_non_negative_integer(data["token_id"], "proposal token_id"),
        weight=_number(data["weight"], "proposal weight"),
    )


def _eos_policy_from_dict(data: Mapping[str, object]) -> EOSPolicy:
    _exact_fields(
        data,
        {"mode", "termination_token_ids", "pad_token_id"},
        "EOS policy",
    )
    mode_value = _string(data["mode"], "EOS mode")
    try:
        mode = EOSMode(mode_value)
    except ValueError as exc:
        raise ValueError(f"unknown EOS mode: {mode_value!r}") from exc
    raw_pad_token_id = data["pad_token_id"]
    pad_token_id = (
        None
        if raw_pad_token_id is None
        else _non_negative_integer(raw_pad_token_id, "pad_token_id")
    )
    return EOSPolicy(
        mode=mode,
        termination_token_ids=_integer_tuple(
            data["termination_token_ids"], "termination_token_ids"
        ),
        pad_token_id=pad_token_id,
    )


@dataclass(frozen=True, slots=True)
class FiniteSlotCounterexample:
    """One complete abstract/finite discrepancy fixture."""

    case_id: str
    title: str
    grammar: CnfGrammar
    canvas: tuple[int | None, ...]
    support_rows: tuple[tuple[int, ...], ...]
    emissions: tuple[bytes | None, ...]
    proposals: tuple[Proposal, ...]
    eos_policy: EOSPolicy
    abstract_pattern: str
    abstract_proposal_ids: tuple[int, ...]
    abstract_witness_token_ids: tuple[int, ...]
    expected_abstract_objective: float
    expected_minimum_physical_slots: int
    expected_finite_status: SolveStatus
    expected_finite_objective: float | None
    expected_finite_selected_proposal_ids: tuple[int, ...]
    expected_finite_witness_token_ids: tuple[int, ...] | None

    def __post_init__(self) -> None:
        _string(self.case_id, "case_id")
        _string(self.title, "title")
        if not isinstance(self.grammar, CnfGrammar):
            raise TypeError("grammar must be a CnfGrammar")
        canvas = tuple(self.canvas)
        rows = tuple(tuple(row) for row in self.support_rows)
        emissions = tuple(self.emissions)
        proposals = tuple(self.proposals)
        if not canvas:
            raise ValueError("counterexamples must contain at least one physical slot")
        if len(rows) != len(canvas):
            raise ValueError("support_rows and canvas must have equal length")
        if not emissions:
            raise ValueError("emissions must contain at least one token")
        if any(
            emission is not None and (not isinstance(emission, bytes) or not emission)
            for emission in emissions
        ):
            raise ValueError("ordinary emissions must be non-empty bytes; controls use null")
        if not all(isinstance(proposal, Proposal) for proposal in proposals):
            raise TypeError("proposals must contain only Proposal instances")
        if not isinstance(self.eos_policy, EOSPolicy):
            raise TypeError("eos_policy must be an EOSPolicy")
        if self.eos_policy.mode is not EOSMode.REQUIRED:
            raise ValueError("T703 counterexamples require an explicit REQUIRED EOS policy")
        _string(self.abstract_pattern, "abstract_pattern")
        if len(set(self.abstract_proposal_ids)) != len(self.abstract_proposal_ids):
            raise ValueError("abstract_proposal_ids must not contain duplicates")
        if self.expected_finite_status not in {
            SolveStatus.OPTIMAL,
            SolveStatus.INFEASIBLE_ON_SUPPORT,
        }:
            raise ValueError("expected finite status must be OPTIMAL or INFEASIBLE_ON_SUPPORT")
        if self.expected_finite_status is SolveStatus.OPTIMAL:
            if (
                self.expected_finite_objective is None
                or self.expected_finite_witness_token_ids is None
            ):
                raise ValueError("an expected OPTIMAL result requires objective and witness")
        elif (
            self.expected_finite_objective is not None
            or self.expected_finite_selected_proposal_ids
            or self.expected_finite_witness_token_ids is not None
        ):
            raise ValueError("an expected infeasible result cannot contain certificate fields")
        object.__setattr__(self, "canvas", canvas)
        object.__setattr__(self, "support_rows", rows)
        object.__setattr__(self, "emissions", emissions)
        object.__setattr__(self, "proposals", proposals)

    @classmethod
    def from_dict(cls, data: Mapping[str, object]) -> Self:
        """Deserialize one schema-versioned case."""

        required = {
            "case_id",
            "title",
            "grammar",
            "canvas",
            "support_rows",
            "emissions_hex_by_token_id",
            "proposals",
            "eos_policy",
            "abstract_sigma_star",
            "slot_proof",
            "expected_finite",
        }
        _exact_fields(data, required, "counterexample")
        abstract = _mapping(data["abstract_sigma_star"], "abstract_sigma_star")
        _exact_fields(
            abstract,
            {"pattern", "proposal_ids", "witness_token_ids", "objective_value"},
            "abstract_sigma_star",
        )
        slot_proof = _mapping(data["slot_proof"], "slot_proof")
        _exact_fields(
            slot_proof,
            {"minimum_physical_slots", "available_physical_slots"},
            "slot_proof",
        )
        expected = _mapping(data["expected_finite"], "expected_finite")
        _exact_fields(
            expected,
            {"status", "objective_value", "selected_proposal_ids", "witness_token_ids"},
            "expected_finite",
        )
        status_value = _string(expected["status"], "expected finite status")
        try:
            status = SolveStatus(status_value)
        except ValueError as exc:
            raise ValueError(f"unknown expected finite status: {status_value!r}") from exc
        raw_objective = expected["objective_value"]
        raw_witness = expected["witness_token_ids"]
        available_slots = _non_negative_integer(
            slot_proof["available_physical_slots"], "available_physical_slots"
        )
        canvas = tuple(
            None if item is None else _non_negative_integer(item, "canvas item")
            for item in _sequence(data["canvas"], "canvas")
        )
        if available_slots != len(canvas):
            raise ValueError("slot_proof available_physical_slots must equal canvas length")
        emissions = tuple(
            None if item is None else bytes.fromhex(_string(item, "emission hex"))
            for item in _sequence(data["emissions_hex_by_token_id"], "emissions_hex_by_token_id")
        )
        return cls(
            case_id=_string(data["case_id"], "case_id"),
            title=_string(data["title"], "title"),
            grammar=CnfGrammar.from_dict(_mapping(data["grammar"], "grammar")),
            canvas=canvas,
            support_rows=tuple(
                _integer_tuple(row, "support row")
                for row in _sequence(data["support_rows"], "support_rows")
            ),
            emissions=emissions,
            proposals=tuple(
                _proposal_from_dict(_mapping(item, "proposal"))
                for item in _sequence(data["proposals"], "proposals")
            ),
            eos_policy=_eos_policy_from_dict(_mapping(data["eos_policy"], "eos_policy")),
            abstract_pattern=_string(abstract["pattern"], "abstract pattern"),
            abstract_proposal_ids=_integer_tuple(abstract["proposal_ids"], "abstract proposal_ids"),
            abstract_witness_token_ids=_integer_tuple(
                abstract["witness_token_ids"], "abstract witness_token_ids"
            ),
            expected_abstract_objective=_number(
                abstract["objective_value"], "abstract objective_value"
            ),
            expected_minimum_physical_slots=_non_negative_integer(
                slot_proof["minimum_physical_slots"], "minimum_physical_slots"
            ),
            expected_finite_status=status,
            expected_finite_objective=(
                None
                if raw_objective is None
                else _number(raw_objective, "expected finite objective_value")
            ),
            expected_finite_selected_proposal_ids=_integer_tuple(
                expected["selected_proposal_ids"], "expected selected_proposal_ids"
            ),
            expected_finite_witness_token_ids=(
                None
                if raw_witness is None
                else _integer_tuple(raw_witness, "expected witness_token_ids")
            ),
        )


@dataclass(frozen=True, slots=True)
class FiniteSlotCounterexampleReport:
    """Recomputed abstract witness, slot proof, and exact-on-support answer."""

    case_id: str
    abstract_pattern: str
    abstract_terminal_labels: tuple[int, ...]
    abstract_objective: float
    available_physical_slots: int
    minimum_physical_slots: int
    finite_status: SolveStatus
    finite_objective: float | None
    finite_selected_proposal_ids: tuple[int, ...]
    finite_witness_token_ids: tuple[int, ...] | None
    finite_witness_terminal_labels: tuple[int, ...] | None
    finite_witness_graph_edge_ids: tuple[int, ...] | None
    finite_witness_token_roles: tuple[str, ...] | None
    finite_witness_eos_position: int | None
    finite_witness_content_endpoint_slot: int | None
    finite_exactness_scope: ExactnessScope
    eos_policy: EOSPolicy
    represented_support_sha256: str

    @property
    def slot_shortfall(self) -> int:
        return self.minimum_physical_slots - self.available_physical_slots

    def to_dict(self) -> dict[str, object]:
        return {
            "case_id": self.case_id,
            "abstract_sigma_star": {
                "pattern": self.abstract_pattern,
                "accepted": True,
                "terminal_labels": list(self.abstract_terminal_labels),
                "terminal_bytes_hex": bytes(self.abstract_terminal_labels).hex(),
                "objective_value": self.abstract_objective,
            },
            "slot_proof": {
                "available_physical_slots": self.available_physical_slots,
                "minimum_physical_slots": self.minimum_physical_slots,
                "slot_shortfall": self.slot_shortfall,
            },
            "finite_exact_on_support": {
                "status": self.finite_status.value,
                "objective_value": self.finite_objective,
                "selected_proposal_ids": list(self.finite_selected_proposal_ids),
                "witness_token_ids": (
                    None
                    if self.finite_witness_token_ids is None
                    else list(self.finite_witness_token_ids)
                ),
                "witness_terminal_labels": (
                    None
                    if self.finite_witness_terminal_labels is None
                    else list(self.finite_witness_terminal_labels)
                ),
                "witness_graph_edge_ids": (
                    None
                    if self.finite_witness_graph_edge_ids is None
                    else list(self.finite_witness_graph_edge_ids)
                ),
                "witness_token_roles": (
                    None
                    if self.finite_witness_token_roles is None
                    else list(self.finite_witness_token_roles)
                ),
                "witness_eos_position": self.finite_witness_eos_position,
                "witness_content_endpoint_slot": (self.finite_witness_content_endpoint_slot),
                "exactness_scope": {
                    "claim": "exact_on_support",
                    **self.finite_exactness_scope.to_dict(),
                },
                "eos_policy": self.eos_policy.to_dict(),
                "represented_support_sha256": self.represented_support_sha256,
            },
        }


def load_finite_slot_counterexamples(
    path: str | Path,
) -> tuple[FiniteSlotCounterexample, ...]:
    """Load and validate the complete versioned T703 corpus."""

    parsed: object = json.loads(Path(path).read_text(encoding="utf-8"))
    corpus = _mapping(parsed, "counterexample corpus")
    _exact_fields(
        corpus,
        {"schema_version", "abstract_sigma_star_semantics", "cases"},
        "counterexample corpus",
    )
    schema_version = _non_negative_integer(corpus["schema_version"], "schema_version")
    if schema_version != FINITE_SLOT_COUNTEREXAMPLE_SCHEMA_VERSION:
        raise ValueError(f"unsupported counterexample schema version: {schema_version}")
    semantics = _string(corpus["abstract_sigma_star_semantics"], "abstract_sigma_star_semantics")
    if semantics != ABSTRACT_SIGMA_STAR_SEMANTICS:
        raise ValueError("counterexample corpus changed the frozen abstract Sigma* semantics")
    cases = tuple(
        FiniteSlotCounterexample.from_dict(_mapping(item, "counterexample"))
        for item in _sequence(corpus["cases"], "cases")
    )
    if not cases:
        raise ValueError("counterexample corpus must not be empty")
    case_ids = tuple(case.case_id for case in cases)
    if len(set(case_ids)) != len(case_ids):
        raise ValueError("counterexample case IDs must be unique")
    return cases


def _is_subsequence(anchors: tuple[int, ...], witness: tuple[int, ...]) -> bool:
    anchor_offset = 0
    for token_id in witness:
        if anchor_offset < len(anchors) and anchors[anchor_offset] == token_id:
            anchor_offset += 1
    return anchor_offset == len(anchors)


def _best_enumerated_path(
    grammar: CnfGrammar,
    paths: Sequence[EOSLatticePath],
) -> EOSLatticePath | None:
    feasible = tuple(path for path in paths if recognizes_cnf(grammar, path.terminal_labels))
    return min(
        feasible,
        key=lambda path: (-path.objective_value, path.graph_edge_ids),
        default=None,
    )


def replay_finite_slot_counterexample(
    case: FiniteSlotCounterexample,
) -> FiniteSlotCounterexampleReport:
    """Independently replay one abstract false positive and finite exact solve."""

    if not isinstance(case, FiniteSlotCounterexample):
        raise TypeError("case must be a FiniteSlotCounterexample")
    proposal_by_id = {proposal.proposal_id: proposal for proposal in case.proposals}
    if len(proposal_by_id) != len(case.proposals):
        raise ValueError("proposal IDs must be unique")
    try:
        abstract_proposals = tuple(
            proposal_by_id[proposal_id] for proposal_id in case.abstract_proposal_ids
        )
    except KeyError as exc:
        raise ValueError(f"abstract witness references unknown proposal ID {exc.args[0]}") from exc
    anchor_token_ids = tuple(proposal.token_id for proposal in abstract_proposals)
    if not _is_subsequence(anchor_token_ids, case.abstract_witness_token_ids):
        raise ValueError("abstract witness does not satisfy its ordered Sigma* token anchors")

    adapter = CompositionalByteLevelAdapter(case.emissions)
    try:
        abstract_bytes = adapter.detokenize_bytes(case.abstract_witness_token_ids)
    except (IndexError, ValueError) as exc:
        raise ValueError("abstract witness must contain only ordinary vocabulary tokens") from exc
    abstract_labels = tuple(abstract_bytes)
    if not recognizes_cnf(case.grammar, abstract_labels):
        raise ValueError("abstract Sigma* witness is not grammar-valid")
    abstract_objective = fsum(proposal.weight for proposal in abstract_proposals)
    if not isclose(
        abstract_objective,
        case.expected_abstract_objective,
        rel_tol=1e-12,
        abs_tol=1e-12,
    ):
        raise ValueError("recomputed abstract objective differs from the fixture")

    minimum_slots = len(case.abstract_witness_token_ids) + 1
    available_slots = len(case.canvas)
    if minimum_slots != case.expected_minimum_physical_slots:
        raise ValueError("recomputed REQUIRED-EOS slot count differs from the fixture proof")
    if minimum_slots <= available_slots:
        raise ValueError("counterexample abstract witness fits in the available physical slots")

    assert case.eos_policy.pad_token_id is not None
    required_special_ids = tuple(
        dict.fromkeys((*case.eos_policy.termination_token_ids, case.eos_policy.pad_token_id))
    )
    support = build_per_position_support(
        canvas=case.canvas,
        policy=SupportPolicy(
            kind=SupportKind.EXPLICIT,
            vocabulary_size=len(case.emissions),
            required_special_token_ids=required_special_ids,
            pruning_description=f"T703 versioned fixture {case.case_id}",
        ),
        explicit_support=dict(enumerate(case.support_rows)),
        proposals=case.proposals,
    )
    if support.rows != case.support_rows:
        raise ValueError("EOS support additions changed the versioned support rows")
    lattice = build_eos_lattice(
        token_lattice=build_token_lattice(support=support, proposals=case.proposals),
        adapter=adapter,
        policy=case.eos_policy,
    )
    all_paths = tuple(lattice.iter_paths())
    enumerated = _best_enumerated_path(case.grammar, all_paths)
    solve = solve_cfg_on_epsilon_dag(case.grammar, lattice.graph)

    if enumerated is None:
        if solve.status is not SolveStatus.INFEASIBLE_ON_SUPPORT:
            raise AssertionError("parser accepted a finite path rejected by enumeration")
        finite_path = None
        finite_objective = None
    else:
        if solve.status is not SolveStatus.OPTIMAL or solve.certificate is None:
            raise AssertionError("parser missed the best grammar-valid enumerated path")
        finite_path = lattice.reconstruct_original_path(solve.certificate.witness_graph_edge_ids)
        lattice.validate_path(finite_path)
        if not recognizes_cnf(case.grammar, finite_path.terminal_labels):
            raise AssertionError("reconstructed parser witness is not grammar-valid")
        if not isclose(
            finite_path.objective_value,
            enumerated.objective_value,
            rel_tol=1e-12,
            abs_tol=1e-12,
        ):
            raise AssertionError("parser objective differs from exhaustive path enumeration")
        finite_objective = finite_path.objective_value

    if solve.status is not case.expected_finite_status:
        raise AssertionError("finite status differs from the versioned expected result")
    if finite_objective != case.expected_finite_objective:
        raise AssertionError("finite objective differs from the versioned expected result")
    finite_selected_ids = () if finite_path is None else finite_path.matched_proposal_ids
    finite_witness_ids = None if finite_path is None else finite_path.token_path.token_ids
    finite_terminal_labels = None if finite_path is None else finite_path.terminal_labels
    finite_graph_edge_ids = None if finite_path is None else finite_path.graph_edge_ids
    finite_token_roles = (
        None if finite_path is None else tuple(role.value for role in finite_path.token_roles)
    )
    finite_eos_position = None if finite_path is None else finite_path.eos_position
    finite_content_endpoint = None if finite_path is None else finite_path.content_endpoint_slot
    if finite_selected_ids != case.expected_finite_selected_proposal_ids:
        raise AssertionError("finite selected proposal IDs differ from the expected result")
    if finite_witness_ids != case.expected_finite_witness_token_ids:
        raise AssertionError("finite token witness differs from the expected result")
    if finite_objective is not None and finite_objective >= abstract_objective:
        raise AssertionError("the finite alternative is not lower than the abstract objective")

    return FiniteSlotCounterexampleReport(
        case_id=case.case_id,
        abstract_pattern=case.abstract_pattern,
        abstract_terminal_labels=abstract_labels,
        abstract_objective=abstract_objective,
        available_physical_slots=available_slots,
        minimum_physical_slots=minimum_slots,
        finite_status=solve.status,
        finite_objective=finite_objective,
        finite_selected_proposal_ids=finite_selected_ids,
        finite_witness_token_ids=finite_witness_ids,
        finite_witness_terminal_labels=finite_terminal_labels,
        finite_witness_graph_edge_ids=finite_graph_edge_ids,
        finite_witness_token_roles=finite_token_roles,
        finite_witness_eos_position=finite_eos_position,
        finite_witness_content_endpoint_slot=finite_content_endpoint,
        finite_exactness_scope=support.exactness_scope,
        eos_policy=case.eos_policy,
        represented_support_sha256=support.fingerprint,
    )


def summarize_finite_slot_counterexamples(
    reports: Sequence[FiniteSlotCounterexampleReport],
) -> dict[str, object]:
    """Return a deterministic machine-readable corpus summary."""

    report_items = tuple(reports)
    if not report_items:
        raise ValueError("reports must not be empty")
    status_counts = Counter(report.finite_status.value for report in report_items)
    return {
        "schema_version": FINITE_SLOT_COUNTEREXAMPLE_SCHEMA_VERSION,
        "abstract_sigma_star_semantics": ABSTRACT_SIGMA_STAR_SEMANTICS,
        "case_count": len(report_items),
        "all_abstract_sigma_star_accepted": True,
        "all_slot_shortfalls_positive": all(report.slot_shortfall > 0 for report in report_items),
        "finite_status_counts": dict(sorted(status_counts.items())),
        "cases": [report.to_dict() for report in report_items],
    }
