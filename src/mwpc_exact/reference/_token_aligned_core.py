"""Token-aligned max-plus CKY reference implementation."""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from functools import partial
from math import fsum, isclose, isfinite
from types import MappingProxyType
from typing import TypeAlias

from mwpc_exact.reference.grammar import CnfGrammar
from mwpc_exact.reference.lexical import (
    NEGATIVE_INFINITY,
    LexicalRewardTable,
    build_lexical_rewards,
)
from mwpc_exact.reference.recognizer import recognizes_cnf
from mwpc_exact.types import (
    ExactCommitResult,
    ExactnessScope,
    Proposal,
    SolveStatus,
    SupportKind,
    TerminalEdge,
    TerminalLabel,
    WeightedTerminalDAG,
)
from mwpc_exact.validator import validate_exact_commit_certificate


@dataclass(frozen=True, slots=True)
class EmptyBackpointer:
    """The explicit empty witness accepted by a zero-slot grammar."""


@dataclass(frozen=True, slots=True)
class TerminalBackpointer:
    """A terminal production selected for a unit-width span."""

    production_id: int
    terminal_id: int


@dataclass(frozen=True, slots=True)
class BinaryBackpointer:
    """A binary production and split selected for a wider span."""

    production_id: int
    split: int
    left_nonterminal_id: int
    right_nonterminal_id: int


CkyBackpointer: TypeAlias = EmptyBackpointer | TerminalBackpointer | BinaryBackpointer
ChartKey: TypeAlias = tuple[int, int, int]


@dataclass(frozen=True, slots=True)
class ChartEntry:
    """Best known max-plus value and its reconstructible decision."""

    score: float
    backpointer: CkyBackpointer

    def __post_init__(self) -> None:
        if isinstance(self.score, bool) or not isinstance(self.score, (int, float)):
            raise TypeError("chart score must be a real number")
        normalized = float(self.score)
        if not isfinite(normalized) or normalized < 0:
            raise ValueError("stored chart scores must be finite and non-negative")
        if not isinstance(
            self.backpointer,
            (EmptyBackpointer, TerminalBackpointer, BinaryBackpointer),
        ):
            raise TypeError("invalid CKY backpointer type")
        object.__setattr__(self, "score", normalized)


@dataclass(frozen=True, slots=True)
class CkyChart:
    """Immutable sparse chart for one grammar and lexical table."""

    grammar: CnfGrammar
    lexical_rewards: LexicalRewardTable
    entries: Mapping[ChartKey, ChartEntry]

    def __post_init__(self) -> None:
        if not isinstance(self.grammar, CnfGrammar):
            raise TypeError("grammar must be a CnfGrammar")
        if not isinstance(self.lexical_rewards, LexicalRewardTable):
            raise TypeError("lexical_rewards must be a LexicalRewardTable")
        entries = dict(self.entries)
        nonterminal_ids = {item.symbol_id for item in self.grammar.nonterminals}
        slot_count = self.lexical_rewards.slot_count
        for key, entry in entries.items():
            if (
                not isinstance(key, tuple)
                or len(key) != 3
                or any(isinstance(item, bool) or not isinstance(item, int) for item in key)
            ):
                raise TypeError("chart keys must be (nonterminal_id, start, end) integers")
            nonterminal_id, start, end = key
            if nonterminal_id not in nonterminal_ids:
                raise ValueError("chart key references an unknown nonterminal")
            if not 0 <= start <= end <= slot_count:
                raise ValueError("chart key span is outside the finite canvas")
            if not isinstance(entry, ChartEntry):
                raise TypeError("chart values must be ChartEntry instances")
        object.__setattr__(self, "entries", MappingProxyType(entries))

    @property
    def root_key(self) -> ChartKey:
        return (
            self.grammar.start_nonterminal_id,
            0,
            self.lexical_rewards.slot_count,
        )

    @property
    def root_entry(self) -> ChartEntry | None:
        return self.entries.get(self.root_key)

    def entry(self, nonterminal_id: int, start: int, end: int) -> ChartEntry | None:
        """Look up one sparse chart entry."""
        return self.entries.get((nonterminal_id, start, end))


@dataclass(frozen=True, slots=True)
class CkySolve:
    """Internal CKY outcome before public certificate reconstruction."""

    status: SolveStatus
    chart: CkyChart

    def __post_init__(self) -> None:
        if self.status not in {
            SolveStatus.OPTIMAL,
            SolveStatus.INFEASIBLE_ON_SUPPORT,
        }:
            raise ValueError("CKY outcome must be OPTIMAL or INFEASIBLE_ON_SUPPORT")
        if not isinstance(self.chart, CkyChart):
            raise TypeError("chart must be a CkyChart")
        if (self.chart.root_entry is not None) != (self.status is SolveStatus.OPTIMAL):
            raise ValueError("CKY status must agree with start-symbol chart reachability")


@dataclass(frozen=True, slots=True)
class ReconstructedCkyCertificate:
    """Parser-local certificate before it is wrapped in the public result."""

    objective_value: float
    selected_proposal_ids: tuple[int, ...]
    witness_token_ids: tuple[int, ...]
    witness_terminal_ids: tuple[int, ...]
    witness_terminal_labels: tuple[TerminalLabel, ...]


class CertificateReconstructionError(ValueError):
    """A chart backpointer or score is not independently reconstructible."""


def run_cky(grammar: CnfGrammar, lexical_rewards: LexicalRewardTable) -> CkySolve:
    """Run deterministic max-plus CKY over exactly the finite lexical rows."""
    if not isinstance(grammar, CnfGrammar):
        raise TypeError("grammar must be a CnfGrammar")
    if not isinstance(lexical_rewards, LexicalRewardTable):
        raise TypeError("lexical_rewards must be a LexicalRewardTable")
    grammar_terminal_ids = {item.symbol_id for item in grammar.terminals}
    if set(lexical_rewards.terminal_token_ids) != grammar_terminal_ids:
        raise ValueError("lexical terminal IDs do not match the grammar")

    entries: dict[ChartKey, ChartEntry] = {}
    slot_count = lexical_rewards.slot_count
    terminal_productions = sorted(grammar.terminal_productions, key=lambda item: item.production_id)
    binary_productions = sorted(grammar.binary_productions, key=lambda item: item.production_id)

    for position in range(slot_count):
        for terminal_production in terminal_productions:
            lexical = lexical_rewards.reward(position, terminal_production.terminal_id)
            if lexical.score == NEGATIVE_INFINITY:
                continue
            _stable_update(
                entries,
                (terminal_production.head_id, position, position + 1),
                lexical.score,
                TerminalBackpointer(
                    terminal_production.production_id,
                    terminal_production.terminal_id,
                ),
            )

    for span_width in range(2, slot_count + 1):
        for start in range(0, slot_count - span_width + 1):
            end = start + span_width
            for binary_production in binary_productions:
                for split in range(start + 1, end):
                    left = entries.get((binary_production.left_id, start, split))
                    if left is None:
                        continue
                    right = entries.get((binary_production.right_id, split, end))
                    if right is None:
                        continue
                    candidate = left.score + right.score
                    if not isfinite(candidate):
                        raise ValueError("CKY objective overflowed finite float range")
                    _stable_update(
                        entries,
                        (binary_production.head_id, start, end),
                        candidate,
                        BinaryBackpointer(
                            production_id=binary_production.production_id,
                            split=split,
                            left_nonterminal_id=binary_production.left_id,
                            right_nonterminal_id=binary_production.right_id,
                        ),
                    )

    if slot_count == 0 and grammar.accepts_empty:
        entries[(grammar.start_nonterminal_id, 0, 0)] = ChartEntry(
            score=0.0,
            backpointer=EmptyBackpointer(),
        )

    chart = CkyChart(grammar, lexical_rewards, entries)
    status = (
        SolveStatus.OPTIMAL if chart.root_entry is not None else SolveStatus.INFEASIBLE_ON_SUPPORT
    )
    return CkySolve(status, chart)


def reconstruct_cky_certificate(
    solve: CkySolve, *, proposals: Iterable[Proposal]
) -> ReconstructedCkyCertificate:
    """Reconstruct and locally re-score an optimal CKY chart."""
    if not isinstance(solve, CkySolve):
        raise TypeError("solve must be a CkySolve")
    if solve.status is not SolveStatus.OPTIMAL:
        raise CertificateReconstructionError("cannot reconstruct an infeasible chart")
    proposal_items = tuple(proposals)
    if not all(isinstance(item, Proposal) for item in proposal_items):
        raise TypeError("proposals must contain only Proposal instances")
    proposal_by_id: dict[int, Proposal] = {}
    for proposal in proposal_items:
        if proposal.proposal_id in proposal_by_id:
            raise ValueError(f"duplicate proposal_id: {proposal.proposal_id}")
        proposal_by_id[proposal.proposal_id] = proposal

    chart = solve.chart
    terminal_productions = {item.production_id: item for item in chart.grammar.terminal_productions}
    binary_productions = {item.production_id: item for item in chart.grammar.binary_productions}
    terminal_labels = chart.grammar.terminal_labels
    terminal_ids: list[int] = []
    token_ids: list[int] = []
    labels: list[TerminalLabel] = []
    selected_ids: list[int] = []

    def visit(nonterminal_id: int, start: int, end: int) -> float:
        entry = chart.entry(nonterminal_id, start, end)
        if entry is None:
            raise CertificateReconstructionError(
                f"missing child chart entry ({nonterminal_id}, {start}, {end})"
            )
        pointer = entry.backpointer
        if isinstance(pointer, EmptyBackpointer):
            if start != end or start != 0 or not chart.grammar.accepts_empty:
                raise CertificateReconstructionError("invalid empty backpointer span")
            if entry.score != 0:
                raise CertificateReconstructionError("empty backpointer must have score zero")
            return 0.0
        if isinstance(pointer, TerminalBackpointer):
            if end != start + 1:
                raise CertificateReconstructionError(
                    "terminal backpointer must cover exactly one slot"
                )
            terminal_production = terminal_productions.get(pointer.production_id)
            if terminal_production is None:
                raise CertificateReconstructionError(
                    f"unknown terminal production ID: {pointer.production_id}"
                )
            if (
                terminal_production.head_id != nonterminal_id
                or terminal_production.terminal_id != pointer.terminal_id
            ):
                raise CertificateReconstructionError(
                    "terminal backpointer does not match its production and chart key"
                )
            lexical = chart.lexical_rewards.reward(start, pointer.terminal_id)
            if lexical.score == NEGATIVE_INFINITY or not isclose(
                entry.score, lexical.score, rel_tol=1e-12, abs_tol=1e-12
            ):
                raise CertificateReconstructionError(
                    "terminal chart score does not match the lexical reward"
                )
            terminal_ids.append(pointer.terminal_id)
            token_ids.append(chart.lexical_rewards.terminal_token_ids[pointer.terminal_id])
            labels.append(terminal_labels[pointer.terminal_id])
            selected_ids.extend(lexical.matched_proposal_ids)
            return lexical.score
        if not isinstance(pointer, BinaryBackpointer):
            raise CertificateReconstructionError("unknown backpointer type")
        if (
            isinstance(pointer.split, bool)
            or not isinstance(pointer.split, int)
            or not start < pointer.split < end
        ):
            raise CertificateReconstructionError("binary split is outside its span")
        binary_production = binary_productions.get(pointer.production_id)
        if binary_production is None:
            raise CertificateReconstructionError(
                f"unknown binary production ID: {pointer.production_id}"
            )
        if (
            binary_production.head_id != nonterminal_id
            or binary_production.left_id != pointer.left_nonterminal_id
            or binary_production.right_id != pointer.right_nonterminal_id
        ):
            raise CertificateReconstructionError(
                "binary backpointer does not match its production and chart key"
            )
        left_score = visit(
            pointer.left_nonterminal_id,
            start,
            pointer.split,
        )
        right_score = visit(
            pointer.right_nonterminal_id,
            pointer.split,
            end,
        )
        recomputed = left_score + right_score
        if not isfinite(recomputed) or not isclose(
            entry.score, recomputed, rel_tol=1e-12, abs_tol=1e-12
        ):
            raise CertificateReconstructionError(
                "binary chart score does not equal its child-score sum"
            )
        return recomputed

    root_score = visit(*chart.root_key)
    if len(set(selected_ids)) != len(selected_ids):
        raise CertificateReconstructionError("reconstructed proposal IDs contain duplicates")
    try:
        selected_proposals = tuple(proposal_by_id[item] for item in selected_ids)
    except KeyError as exc:
        raise CertificateReconstructionError(
            f"lexical backpointer references unknown proposal ID: {exc.args[0]}"
        ) from exc
    for proposal in selected_proposals:
        if (
            proposal.weight <= 0
            or proposal.position >= len(token_ids)
            or token_ids[proposal.position] != proposal.token_id
        ):
            raise CertificateReconstructionError(
                f"proposal {proposal.proposal_id} does not match the reconstructed witness"
            )
    objective = fsum(proposal.weight for proposal in selected_proposals)
    if not isclose(objective, root_score, rel_tol=1e-12, abs_tol=1e-12):
        raise CertificateReconstructionError(
            "recomputed proposal objective does not match the root chart score"
        )
    return ReconstructedCkyCertificate(
        objective_value=objective,
        selected_proposal_ids=tuple(selected_ids),
        witness_token_ids=tuple(token_ids),
        witness_terminal_ids=tuple(terminal_ids),
        witness_terminal_labels=tuple(labels),
    )


def build_token_aligned_support_graph(
    grammar: CnfGrammar, lexical_rewards: LexicalRewardTable
) -> WeightedTerminalDAG:
    """Build the canonical finite per-slot DAG used by the public certificate."""
    if not isinstance(grammar, CnfGrammar):
        raise TypeError("grammar must be a CnfGrammar")
    if not isinstance(lexical_rewards, LexicalRewardTable):
        raise TypeError("lexical_rewards must be a LexicalRewardTable")
    if set(lexical_rewards.terminal_token_ids) != {item.symbol_id for item in grammar.terminals}:
        raise ValueError("lexical terminal IDs do not match the grammar")

    labels = grammar.terminal_labels
    ordered_terminal_ids = sorted(labels)
    edges: list[TerminalEdge] = []
    next_edge_id = 0
    for position in range(lexical_rewards.slot_count):
        for terminal_id in ordered_terminal_ids:
            lexical = lexical_rewards.reward(position, terminal_id)
            if lexical.score == NEGATIVE_INFINITY:
                continue
            edges.append(
                TerminalEdge(
                    edge_id=next_edge_id,
                    source_state=position,
                    target_state=position + 1,
                    terminal_label=labels[terminal_id],
                    weight=lexical.score,
                    provenance_token_edge_id=next_edge_id,
                    matched_proposal_ids=lexical.matched_proposal_ids,
                )
            )
            next_edge_id += 1
    slot_count = lexical_rewards.slot_count
    return WeightedTerminalDAG(
        node_ids=tuple(range(slot_count + 1)),
        start_node_id=0,
        final_node_ids=(slot_count,),
        edges=tuple(edges),
    )


def solve_token_aligned(
    *,
    grammar: CnfGrammar,
    canvas: Sequence[int | None],
    proposals: Iterable[Proposal],
    exactness_scope: ExactnessScope,
    terminal_token_ids: Mapping[int, int] | None = None,
    per_position_support: Sequence[Sequence[int]] | None = None,
) -> ExactCommitResult:
    """Solve one finite token-aligned MWPC instance and validate its certificate."""
    if not isinstance(exactness_scope, ExactnessScope):
        raise TypeError("exactness_scope must be an ExactnessScope")
    if exactness_scope.kind not in {SupportKind.FULL, SupportKind.EXPLICIT}:
        raise ValueError("token-aligned reference solves require FULL or EXPLICIT support")
    canvas_tokens = tuple(canvas)
    proposal_items = tuple(proposals)
    lexical = build_lexical_rewards(
        grammar=grammar,
        canvas=canvas_tokens,
        proposals=proposal_items,
        terminal_token_ids=terminal_token_ids,
        per_position_support=per_position_support,
    )
    represented_token_ids = tuple(lexical.terminal_token_ids.values())
    if any(token_id >= exactness_scope.vocabulary_size for token_id in represented_token_ids):
        raise ValueError("terminal token ID is outside the exactness-scope vocabulary")
    if any(
        token_id is not None and token_id >= exactness_scope.vocabulary_size
        for token_id in canvas_tokens
    ):
        raise ValueError("fixed canvas token is outside the exactness-scope vocabulary")
    if any(proposal.token_id >= exactness_scope.vocabulary_size for proposal in proposal_items):
        raise ValueError("proposal token is outside the exactness-scope vocabulary")
    if per_position_support is not None and any(
        token_id >= exactness_scope.vocabulary_size
        for support in per_position_support
        for token_id in support
    ):
        raise ValueError("support token is outside the exactness-scope vocabulary")

    solve = run_cky(grammar, lexical)
    base_diagnostics: dict[str, object] = {
        "algorithm": "python_token_aligned_cky",
        "chart_entries": len(solve.chart.entries),
        "slot_count": lexical.slot_count,
    }
    if solve.status is SolveStatus.INFEASIBLE_ON_SUPPORT:
        return ExactCommitResult(
            status=SolveStatus.INFEASIBLE_ON_SUPPORT,
            exactness_scope=exactness_scope,
            diagnostics=base_diagnostics,
        )
    root = solve.chart.root_entry
    assert root is not None
    if isinstance(root.backpointer, EmptyBackpointer):
        return ExactCommitResult(
            status=SolveStatus.UNSUPPORTED,
            exactness_scope=exactness_scope,
            diagnostics={
                **base_diagnostics,
                "reason": "public result contract does not yet encode an empty path certificate",
            },
        )

    try:
        certificate = reconstruct_cky_certificate(solve, proposals=proposal_items)
        graph = build_token_aligned_support_graph(grammar, lexical)
        edge_by_position_and_label = {
            (edge.source_state, edge.terminal_label): edge.edge_id for edge in graph.edges
        }
        witness_edge_ids = tuple(
            edge_by_position_and_label[(position, label)]
            for position, label in enumerate(certificate.witness_terminal_labels)
        )
        preliminary = ExactCommitResult(
            status=SolveStatus.OPTIMAL,
            exactness_scope=exactness_scope,
            objective_value=certificate.objective_value,
            selected_proposal_ids=certificate.selected_proposal_ids,
            witness_token_ids=certificate.witness_token_ids,
            witness_terminal_labels=certificate.witness_terminal_labels,
            witness_graph_edge_ids=witness_edge_ids,
            diagnostics=base_diagnostics,
        )
        token_id_by_label = {
            grammar.terminal_labels[terminal_id]: token_id
            for terminal_id, token_id in lexical.terminal_token_ids.items()
        }
        report = validate_exact_commit_certificate(
            preliminary,
            expected_scope=exactness_scope,
            canvas=canvas_tokens,
            proposals=proposal_items,
            graph=graph,
            grammar_recognizer=partial(recognizes_cnf, grammar),
            tokenizer_validator=lambda token_ids, labels: (
                len(token_ids) == len(labels)
                and all(
                    token_id_by_label.get(label) == token_id
                    for token_id, label in zip(token_ids, labels, strict=True)
                )
            ),
            eos_validator=lambda token_ids: len(token_ids) == len(canvas_tokens),
        )
        if not report.is_valid:
            return ExactCommitResult(
                status=SolveStatus.ERROR,
                exactness_scope=exactness_scope,
                diagnostics={
                    **base_diagnostics,
                    "reason": "independent certificate validation failed",
                    "certificate_validation": report.to_dict(),
                },
            )
        return ExactCommitResult(
            status=SolveStatus.OPTIMAL,
            exactness_scope=exactness_scope,
            objective_value=certificate.objective_value,
            selected_proposal_ids=certificate.selected_proposal_ids,
            witness_token_ids=certificate.witness_token_ids,
            witness_terminal_labels=certificate.witness_terminal_labels,
            witness_graph_edge_ids=witness_edge_ids,
            diagnostics={
                **base_diagnostics,
                "certificate_validation": report.to_dict(),
            },
        )
    except (CertificateReconstructionError, KeyError) as exc:
        return ExactCommitResult(
            status=SolveStatus.ERROR,
            exactness_scope=exactness_scope,
            diagnostics={
                **base_diagnostics,
                "reason": "certificate reconstruction failed",
                "exception_type": type(exc).__name__,
                "exception_message": str(exc),
            },
        )


def _stable_update(
    entries: dict[ChartKey, ChartEntry],
    key: ChartKey,
    candidate_score: float,
    backpointer: CkyBackpointer,
) -> None:
    existing = entries.get(key)
    if existing is None or candidate_score > existing.score:
        entries[key] = ChartEntry(candidate_score, backpointer)
