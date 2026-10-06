"""Independent ambiguity-safe mass certificates; no search/optimizer imports.

Probabilities describe a frozen mean-field predictive, not factual confidence.
Rationals preserve the supplied numeric distribution, including omitted mass.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Callable
from dataclasses import dataclass, replace
from enum import StrEnum
from fractions import Fraction
from math import lcm, prod
from random import Random

from mwpc_exact.budget_bounds import budget_input_fingerprint, validate_budget_batch
from mwpc_exact.budget_proof import (
    _fraction,
    _ints,
    fraction_data,
    read_budget_proof,
    verify_budget_proof,
)
from mwpc_exact.conflict_proof import read_state, state_data
from mwpc_exact.language_coverage import check_language_coverage
from mwpc_exact.serde import _integer, _mapping, _sequence, _string
from mwpc_exact.state import SelectionInput
from mwpc_exact.support import SupportPolicy, build_per_position_support
from mwpc_exact.types import SolveStatus, SupportKind

Box = tuple[tuple[int, ...], ...]


class PosteriorScope(StrEnum):
    REPRESENTED = "represented_support"
    FULL = "full_predictive_with_omitted_mass"


class MassStatus(StrEnum):
    CERTIFIED = "certified_tolerance"
    INCOMPLETE = "incomplete"
    TIMEOUT = "timeout"
    ZERO_ON_SUPPORT = "zero_valid_probability_on_support"


def probability(value: object) -> Fraction:
    if isinstance(value, bool) or not isinstance(value, (int, Fraction)):
        raise TypeError("probabilities/tolerances must be exact rationals")
    result = Fraction(value)
    if not 0 <= result <= 1:
        raise ValueError("probability/tolerance must lie in [0, 1]")
    return result


@dataclass(frozen=True)
class ProbabilityInput:
    state: SelectionInput
    probabilities: tuple[tuple[Fraction, ...], ...]

    def __post_init__(self) -> None:
        if len(self.probabilities) != len(self.state.canvas):
            raise ValueError("one probability row is required per canvas slot")
        normalized = tuple(tuple(probability(p) for p in row) for row in self.probabilities)
        for fixed, tokens, row in zip(
            self.state.canvas, self.state.support.rows, normalized, strict=True
        ):
            if len(tokens) != len(row) or sum(row) > 1:
                raise ValueError("probabilities must align with support and sum to at most one")
            if fixed is not None and (tokens != (fixed,) or row != (Fraction(1),)):
                raise ValueError("fixed slots must have their fixed token with probability one")
        object.__setattr__(self, "probabilities", normalized)

    @property
    def fingerprint(self) -> str:
        data = [
            budget_input_fingerprint(self.state),
            [[fraction_data(p) for p in row] for row in self.probabilities],
        ]
        return hashlib.sha256(json.dumps(data, separators=(",", ":")).encode()).hexdigest()

    @property
    def omitted_mass(self) -> Fraction:
        return 1 - prod((sum(row, Fraction()) for row in self.probabilities), start=Fraction(1))

    def box_mass(self, box: Box) -> Fraction:
        return prod(
            (
                sum((p for t, p in zip(tokens, row, strict=True) if t in domain), Fraction())
                for tokens, row, domain in zip(
                    self.state.support.rows, self.probabilities, box, strict=True
                )
            ),
            start=Fraction(1),
        )


def restrict_box(state: SelectionInput, box: Box) -> SelectionInput:
    if len(box) != len(state.canvas) or any(not row for row in box):
        raise ValueError("box must contain one nonempty domain per slot")
    support = build_per_position_support(
        canvas=state.canvas,
        policy=SupportPolicy(
            kind=SupportKind.EXPLICIT,
            vocabulary_size=state.tokenizer_adapter.vocabulary_size,
            required_special_token_ids=state.support.exactness_scope.included_special_tokens,
        ),
        explicit_support=dict(enumerate(box)),
    )
    if any(not set(row) <= set(old) for row, old in zip(box, state.support.rows, strict=True)):
        raise ValueError("box contains tokens outside the original support")
    return replace(state, proposals=(), support=support)


@dataclass(frozen=True)
class MassEnvelope:
    lower: Fraction
    unresolved: Fraction
    omitted: Fraction
    accepted: tuple[tuple[tuple[int, ...], Fraction], ...]
    oracle_calls: int
    outside_valid_upper: Fraction

    def upper(self, scope: PosteriorScope) -> Fraction:
        return self.lower + self.unknown(scope)

    def unknown(self, scope: PosteriorScope) -> Fraction:
        if not isinstance(scope, PosteriorScope):
            raise TypeError("posterior scope must be explicit")
        return self.unresolved + (
            self.outside_valid_upper if scope is PosteriorScope.FULL else Fraction()
        )

    def tv_bound(self, scope: PosteriorScope) -> Fraction | None:
        unknown = self.unknown(scope)
        return unknown / (self.lower + unknown) if self.lower else None

    def event_interval(
        self, event: Callable[[tuple[int, ...]], bool], scope: PosteriorScope
    ) -> tuple[Fraction, Fraction]:
        if not self.lower:
            raise ValueError("a posterior requires positive accepted mass")
        known = sum((mass for witness, mass in self.accepted if event(witness)), Fraction())
        unknown = self.unknown(scope)
        return known / (self.lower + unknown), (known + unknown) / (self.lower + unknown)

    def sample(self, rng: Random, *, scope: PosteriorScope, max_tv: Fraction) -> tuple[int, ...]:
        tolerance = probability(max_tv)
        bound = self.tv_bound(scope)
        if bound is None or bound > tolerance:
            raise ValueError("sampling refused: requested posterior tolerance is not certified")
        unit = lcm(*(mass.denominator for _, mass in self.accepted))
        weights = [int(mass * unit) for _, mass in self.accepted]
        draw = rng.randrange(sum(weights))
        for (witness, _), weight in zip(self.accepted, weights, strict=True):
            if draw < weight:
                return witness
            draw -= weight
        raise AssertionError("exact rational categorical sample must select a witness")


def verify_mass_proof(
    value: object,
    *,
    expected_input: ProbabilityInput | None = None,
    reweight: ProbabilityInput | None = None,
) -> MassEnvelope:
    """Validate the full partition, original-token leaves and independent CFG proofs.

    ``reweight`` may change probabilities only: original state/support must match.
    Old bounds/status are checked against original probabilities before reweighting.
    """
    data = _mapping(value, "mass proof")
    if _integer(data["schema_version"], "version") != 1 or data["kind"] != "token_mass_partition":
        raise ValueError("unsupported probability certificate")
    state = read_state(data["input"])
    inputs = ProbabilityInput(
        state,
        tuple(
            tuple(_fraction(p) for p in _sequence(row, "row"))
            for row in _sequence(data["probabilities"], "probabilities")
        ),
    )
    if inputs.fingerprint != _string(data["input_fingerprint"], "fingerprint"):
        raise ValueError("probability input fingerprint differs")
    if expected_input is not None and inputs != expected_input:
        raise ValueError("certificate does not describe the requested original input")
    if reweight is not None and reweight.state != state:
        raise ValueError("reweighting cannot change grammar/support/canvas/token meanings")
    nodes = [_mapping(n, "node") for n in _sequence(data["nodes"], "nodes")]
    if not nodes:
        raise ValueError("partition has no root")
    boxes: list[Box] = []
    for node in nodes:
        box = tuple(_ints(row, "box row") for row in _sequence(node["box"], "box"))
        if (
            len(box) != len(state.canvas)
            or any(not row or tuple(sorted(set(row))) != row for row in box)
            or any(
                not set(row) <= set(old) for row, old in zip(box, state.support.rows, strict=True)
            )
        ):
            raise ValueError("invalid partition box")
        boxes.append(box)
    if boxes[0] != state.support.rows:
        raise ValueError("partition root must be the complete original support")
    parents: set[int] = set()
    accepted: list[int] = []
    unresolved: list[int] = []
    zeros: list[int] = []
    for index, (node, box) in enumerate(zip(nodes, boxes, strict=True)):
        kind = _string(node["kind"], "leaf kind")
        children = _ints(node.get("children", []), "children")
        if kind == "split":
            if len(children) != 2 or children[0] == children[1]:
                raise ValueError("a split needs two different children")
            if any(child <= index or child >= len(nodes) or child in parents for child in children):
                raise ValueError("partition must be a forward tree without shared/foreign children")
            parents.update(children)
            left, right = (boxes[c] for c in children)
            changed = [i for i, (a, b) in enumerate(zip(left, right, strict=True)) if a != b]
            if len(changed) != 1:
                raise ValueError("split must partition exactly one domain")
            position = changed[0]
            if (
                set(left[position]) & set(right[position])
                or set(left[position]) | set(right[position]) != set(box[position])
                or any(
                    left[i] != box[i] or right[i] != box[i]
                    for i in range(len(box))
                    if i != position
                )
            ):
                raise ValueError("children overlap or fail to cover the parent")
        else:
            if children:
                raise ValueError("a leaf cannot have children")
            if kind == "accepted":
                if any(len(row) != 1 for row in box):
                    raise ValueError("accepted leaves must be singleton token sequences")
                validate_budget_batch(
                    state,
                    budget=0,
                    witness_token_ids=tuple(r[0] for r in box),
                    committed_positions=(),
                )
                accepted.append(index)
            elif kind == "infeasible":
                restricted = restrict_box(state, box)
                compact = _mapping(node["proof"], "infeasibility proof")
                proof = {
                    **compact,
                    "input": state_data(restricted),
                    "input_fingerprint": budget_input_fingerprint(restricted),
                }
                verify_budget_proof(proof, expected_input=restricted)
                _, results = read_budget_proof(proof)
                if (
                    len(results) != 1
                    or results[0].budget != 0
                    or results[0].status is not SolveStatus.INFEASIBLE_ON_SUPPORT
                ):
                    raise ValueError("box proof does not certify infeasibility at budget zero")
            elif kind == "unresolved":
                unresolved.append(index)
            elif kind == "zero":
                if inputs.box_mass(box):
                    raise ValueError("zero box has positive mass")
                zeros.append(index)
            else:
                raise ValueError("unknown partition leaf kind")
    if parents != set(range(1, len(nodes))):
        raise ValueError("unreachable certificate nodes")
    covered = data.get("language_coverage") is not None
    if covered:
        check_language_coverage(state, data["language_coverage"])
    calls = _integer(data["oracle_calls"], "oracle calls")
    if calls < 0:
        raise ValueError("negative oracle calls")

    def envelope(predictive: ProbabilityInput) -> MassEnvelope:
        entries = tuple(
            (tuple(r[0] for r in boxes[i]), predictive.box_mass(boxes[i])) for i in accepted
        )
        # Zero leaves depend on probabilities and cannot silently survive reweighting.
        residual = sum((predictive.box_mass(boxes[i]) for i in (*unresolved, *zeros)), Fraction())
        return MassEnvelope(
            sum((p for _, p in entries), Fraction()),
            residual,
            predictive.omitted_mass,
            entries,
            calls,
            Fraction() if covered else predictive.omitted_mass,
        )

    original = envelope(inputs)
    summary = _mapping(data["envelope"], "mass bounds")
    for name in ("lower", "unresolved", "omitted"):
        if _fraction(summary[name]) != getattr(original, name):
            raise ValueError("forged probability envelope")
    scope = PosteriorScope(_string(data["reference_scope"], "reference scope"))
    epsilon = probability(_fraction(data["requested_tv"]))
    bound = original.tv_bound(scope)
    status = MassStatus(_string(data["status"], "status"))
    if status is MassStatus.CERTIFIED and (bound is None or bound > epsilon):
        raise ValueError("uncertified tolerance presented as certified")
    if status is MassStatus.ZERO_ON_SUPPORT and (original.lower or original.unresolved):
        raise ValueError("positive/unknown mass presented as zero valid probability")
    return envelope(reweight) if reweight is not None else original
