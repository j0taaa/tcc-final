"""Research only: exact rule sampling with counterexample-driven conditioning.

Adaptive rejection and CEGIS are antecedents, not claimed inventions. Unlike
prefix exclusion, each refinement removes every rule failing one record.
The frozen product and all returned original token IDs are preserved.
"""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, replace
from fractions import Fraction
from math import prod
from random import Random

from scripts.exact_commit.semantic_json import (
    SemanticPosterior,
    boolean_rule_grammar,
    evaluate_semantics,
)

from mwpc_exact.cfg_posterior import CfgPosterior, CfgSampler, _binarize_source
from mwpc_exact.mass_certificate import ProbabilityInput
from mwpc_exact.reference.limits import CompilationLimit, WorkBudget
from mwpc_exact.reference.normalization import normalize_to_cnf


def _execute(rule, record):
    op, value = next(iter(rule.items()))
    if op == "var":
        return record[value]
    children = [_execute(child, record) for child in value]
    return not children[0] if op == "!" else all(children) if op == "and" else any(children)


def _sample_work_bound(plan: CfgSampler, records: int) -> int:
    """Bound every possible traversal, so work refusal cannot censor a draw.

    The per-node bound covers all alternative joins and the conditional pair join.
    A CNF derivation has at most twice as many nodes as byte edges; an acyclic
    token path has fewer edges than the compiled graph has vertices.
    Integer-operation wall time is outside the cooperative work model.
    """
    return 2 * plan.graph_vertices * (plan.alternatives + 1) * (12 + 3 * records) * (1 << records)


class AdaptiveSemanticSampler:
    """A reusable stream conditioned on every declared Boolean example.

    At most m rejected complete rules over the entire stream, assuming refinements
    fit the declared budgets. Profile compilation uses only active counterexamples;
    all records are checked before returning a rule. Zero mass and resource refusal
    remain distinct. Refusal makes the session terminal; reset/reweight explicitly
    requires a new session. No probabilities are changed by prompting or a forward.
    """

    def __init__(
        self,
        plan: CfgSampler,
        inputs: ProbabilityInput,
        records: Sequence[Mapping[str, bool]],
        labels: Sequence[bool],
        *,
        max_active: int = 12,
        max_profile_entries: int = 1_000_000,
        max_work: int = 10_000_000,
        identity_operator: bool = False,
    ) -> None:
        if not records or len(records) != len(labels) or any(type(b) is not bool for b in labels):
            raise ValueError("provide equally many nonempty Boolean records and labels")
        fields = tuple(sorted(records[0]))
        if any(
            set(r) != set(fields) or any(type(v) is not bool for v in r.values()) for r in records
        ):
            raise ValueError("records must share exactly the same Boolean fields")
        if type(max_active) is not int or not 0 <= max_active <= 12:
            raise ValueError("max_active must be between zero and twelve")
        if type(max_profile_entries) is not int or max_profile_entries < 0:
            raise ValueError("profile entry cap must be a non-negative integer")
        budget = WorkBudget(max_work=max_work)
        expected = normalize_to_cnf(
            _binarize_source(
                boolean_rule_grammar(fields, identity_operator=identity_operator), budget
            ),
            budget=budget,
        )
        if plan.grammar != expected.grammar:
            raise ValueError("plan does not represent the Boolean rule grammar")
        self._plan, self._inputs = plan, inputs
        self._records = tuple(dict(r) for r in records)
        self._labels = tuple(labels)
        self._max_active, self._max_entries, self._max_work = (
            max_active,
            max_profile_entries,
            max_work,
        )
        self._syntax = plan.evaluate(inputs)
        self._identity_operator = identity_operator
        self._posterior = None
        self._target = 0
        self._active: tuple[int, ...] = ()
        self._refused = False
        self.draws = self.rejections = 0

    @property
    def active(self) -> tuple[int, ...]:
        return self._active

    @property
    def proposal_mass(self) -> Fraction:
        """An exact upper bound on full-specification mass, not that mass itself."""
        return (
            self._posterior.profile_masses[self._target]
            if self._posterior
            else self._syntax.valid_mass
        )

    def sample(self, rng: Random) -> tuple[int, ...]:
        if not isinstance(rng, Random):
            raise TypeError("rng must be an explicitly supplied Random instance")
        if self._refused:
            raise CompilationLimit("session refused a refinement; feasibility remains unresolved")
        while self.proposal_mass:
            path = (
                self._posterior.sample(self._target, rng)
                if self._posterior
                else self._syntax.sample(rng)
            )
            self.draws += 1
            rule = json.loads(self._inputs.state.tokenizer_adapter.detokenize_bytes(path))
            violated = next(
                (i for i, r in enumerate(self._records) if _execute(rule, r) != self._labels[i]),
                None,
            )
            if violated is None:
                return path
            if violated in self._active:
                raise RuntimeError("conditional sample violated an active requirement")
            self.rejections += 1
            active = (*self._active, violated)
            try:
                if len(active) > self._max_active:
                    raise CompilationLimit("active record cap; feasibility remains unresolved")
                posterior = evaluate_semantics(
                    self._plan,
                    self._inputs,
                    tuple(self._records[i] for i in active),
                    max_profile_entries=self._max_entries,
                    max_work=self._max_work,
                    identity_operator=self._identity_operator,
                )
            except CompilationLimit:
                self._refused = True
                raise
            # No path-dependent sampling timeout: reserve a proved traversal bound.
            self._posterior = replace(
                posterior, _max_work=_sample_work_bound(self._plan, len(active))
            )
            self._active = active
            self._target = sum(1 << j for j, i in enumerate(active) if self._labels[i])
        raise ValueError("ZERO_MASS_ON_SUPPORT: no rule satisfies the full specification")


@dataclass(frozen=True)
class CorePosterior:
    """Full-specification mass and exact original-token samples after certification."""

    posterior: CfgPosterior | SemanticPosterior
    target: int | None

    @property
    def valid_mass(self) -> Fraction:
        if isinstance(self.posterior, CfgPosterior):
            return self.posterior.valid_mass
        return self.posterior.profile_masses[self.target]

    def sample(self, rng: Random) -> tuple[int, ...]:
        if isinstance(self.posterior, CfgPosterior):
            return self.posterior.sample(rng)
        return self.posterior.sample(self.target, rng)


@dataclass(frozen=True)
class SemanticCore:
    """A structural implication certificate, valid under admitted reweightings.

    Use compile_semantic_core to construct; verify() recomputes obligations.
    A smaller sufficient subset is certified, not necessarily a minimum subset.
    This record is not an independently verified Python-source proof object.
    """

    _plan: CfgSampler
    _uniform: ProbabilityInput
    fields: tuple[str, ...]
    records: tuple[tuple[bool, ...], ...]
    labels: tuple[bool, ...]
    active: tuple[int, ...]
    violation_counts: tuple[int, ...]
    probe_evaluations: int
    identity_operator: bool
    max_profile_entries: int
    max_work: int

    def _violations(self) -> tuple[int, ...]:
        rows = tuple(dict(zip(self.fields, r, strict=True)) for r in self.records)
        domain_size = prod(map(len, self._uniform.state.support.rows))
        target = sum(1 << j for j, i in enumerate(self.active) if self.labels[i])
        counts = []
        for i, row in enumerate(rows):
            if i in self.active:
                counts.append(0)
                continue
            posterior = evaluate_semantics(
                self._plan,
                self._uniform,
                (*(rows[j] for j in self.active), row),
                max_profile_entries=self.max_profile_entries,
                max_work=self.max_work,
                identity_operator=self.identity_operator,
            )
            wrong = target + (0 if self.labels[i] else 1 << len(self.active))
            count = posterior.profile_masses[wrong] * domain_size
            if count.denominator != 1:
                raise RuntimeError("uniform posterior is not an integer structural path count")
            counts.append(count.numerator)
        return tuple(counts)

    def verify(self) -> bool:
        """Recompute every inactive implication; source-independent oracles are separate."""
        return self.violation_counts == (0,) * len(self.labels) == self._violations()

    def evaluate(self, inputs: ProbabilityInput) -> CorePosterior:
        base, new = self._uniform.state, inputs.state
        if (
            len(base.canvas) != len(new.canvas)
            or any(a is not None and a != b for a, b in zip(base.canvas, new.canvas, strict=True))
            or any(
                not set(b) <= set(a)
                for a, b in zip(base.support.rows, new.support.rows, strict=True)
            )
        ):
            raise ValueError(
                "semantic core reuse expanded its certified support or released a fixed slot"
            )
        # The retained plan separately rejects grammar/tokenizer/EOS changes.
        if not self.active:
            return CorePosterior(self._plan.evaluate(inputs), None)
        rows = tuple(dict(zip(self.fields, self.records[i], strict=True)) for i in self.active)
        posterior = evaluate_semantics(
            self._plan,
            inputs,
            rows,
            max_profile_entries=self.max_profile_entries,
            max_work=self.max_work,
            identity_operator=self.identity_operator,
        )
        posterior = replace(posterior, _max_work=_sample_work_bound(self._plan, len(self.active)))
        target = sum(1 << j for j, i in enumerate(self.active) if self.labels[i])
        return CorePosterior(posterior, target)


def compile_semantic_core(
    plan: CfgSampler,
    inputs: ProbabilityInput,
    records: Sequence[Mapping[str, bool]],
    labels: Sequence[bool],
    *,
    max_active: int = 11,
    max_profile_entries: int = 1_000_000,
    max_work: int = 10_000_000,
    identity_operator: bool = False,
    initial_active: Sequence[int] = (),
) -> SemanticCore:
    """Greedy structural counterexample coverage without enumerating programs.

    Positivity on every represented token, including originally zero-weight
    alternatives, makes the certificate independent of later model weights.
    One extra profile dimension checks each omitted requirement independently;
    their joint distribution is never needed. Preparation costs are additional.
    """
    if type(max_active) is not int or not 0 <= max_active <= 11:
        raise ValueError("core cap must leave one probe dimension (zero to eleven)")
    uniform = replace(
        inputs,
        probabilities=tuple(
            (Fraction(1, len(row)),) * len(row) for row in inputs.state.support.rows
        ),
    )
    checked = AdaptiveSemanticSampler(
        plan,
        uniform,
        records,
        labels,
        max_profile_entries=max_profile_entries,
        max_work=max_work,
        identity_operator=identity_operator,
    )
    fields = tuple(sorted(checked._records[0]))
    active = tuple(initial_active)
    if (
        len(set(active)) != len(active)
        or len(active) > max_active
        or any(type(i) is not int or not 0 <= i < len(checked._labels) for i in active)
    ):
        raise ValueError("initial core must contain distinct admitted record indices")
    core = SemanticCore(
        plan,
        uniform,
        fields,
        tuple(tuple(r[f] for f in fields) for r in checked._records),
        checked._labels,
        active,
        (0,) * len(labels),
        0,
        identity_operator,
        max_profile_entries,
        max_work,
    )
    remaining = (
        core.evaluate(uniform).valid_mass if active else checked._syntax.valid_mass
    ) * prod(map(len, uniform.state.support.rows))
    if remaining.denominator != 1:
        raise RuntimeError("uniform syntax mass is not an integer path count")
    while remaining:
        counts = core._violations()
        probes = core.probe_evaluations + len(core.labels) - len(core.active)
        largest = max(counts)
        if not 0 <= largest <= remaining:
            raise RuntimeError("a structural violation count exceeded the active language")
        if not largest:
            return replace(core, violation_counts=counts, probe_evaluations=probes)
        if len(core.active) >= max_active:
            raise CompilationLimit("semantic core cap; implication remains unresolved")
        chosen = counts.index(largest)
        core = replace(core, active=(*core.active, chosen), probe_evaluations=probes)
        remaining -= largest
    return core  # Empty active language implies every omitted requirement.
