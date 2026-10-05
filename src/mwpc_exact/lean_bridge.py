"""Export resource certificates as kernel-checked Lean proofs.

The exporter is untrusted: Lean checks the generated productions, arcs,
potential inequalities, and witness constructors. Original-input graph
correspondence remains an independently checked Python boundary; this module
does not claim source-level verification of Python/Rust or model inference.
"""

from __future__ import annotations

import hashlib
import os
import re
import shutil
import signal
import subprocess
import tempfile
from dataclasses import dataclass
from fractions import Fraction
from math import lcm
from pathlib import Path

from mwpc_exact.budget_proof import read_budget_proof, verify_budget_proof
from mwpc_exact.reference.budget_types import ResourceArc
from mwpc_exact.reference.grammar import CnfGrammar
from mwpc_exact.types import SolveStatus, TerminalLabel


def _run_lean(command: list[str], *, cwd: Path, timeout: float) -> subprocess.CompletedProcess[str]:
    """Terminate the whole Lake/Lean process tree on a formal-check deadline."""
    with subprocess.Popen(
        command,
        cwd=cwd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        start_new_session=True,
    ) as process:
        try:
            stdout, stderr = process.communicate(timeout=timeout)
        except subprocess.TimeoutExpired:
            if os.name == "posix":
                os.killpg(process.pid, signal.SIGKILL)
            else:
                process.kill()
            process.communicate()
            raise
    return subprocess.CompletedProcess(command, process.returncode, stdout, stderr)


@dataclass(frozen=True)
class LeanExport:
    source: str
    input_fingerprint: str
    denominator: int
    theorem_names: tuple[str, ...]


def audit_lean_axioms(
    output: str, expected_theorems: tuple[str, ...]
) -> dict[str, tuple[str, ...]]:
    """Require every named proof and reject dependencies beyond Lean's logic."""
    checked: dict[str, tuple[str, ...]] = {}
    standard = {"propext", "Quot.sound", "Classical.choice"}
    for name, dependencies in re.findall(
        r"'([^']+)' (?:depends on axioms: \[([^\]]*)\]|does not depend on any axioms)", output
    ):
        axioms = tuple(x.strip() for x in dependencies.split(",") if x.strip())
        if name in checked or set(axioms) - standard:
            raise ValueError(f"Unapproved or duplicate Lean axiom dependency for {name}: {axioms}")
        checked[name] = axioms
    if set(checked) != set(expected_theorems):
        raise ValueError("Lean axiom audit does not cover exactly the expected theorems")
    return checked


@dataclass(frozen=True)
class _Tree:
    head: int
    lo: int
    hi: int
    left: _Tree | None = None
    right: _Tree | None = None


def _parse(grammar: CnfGrammar, labels: tuple[TerminalLabel, ...]) -> _Tree:
    """Boolean witness parsing, independent of weighted parser/backpointers."""
    cells: dict[tuple[int, int, int], _Tree] = {}
    for i, label in enumerate(labels):
        for rule in grammar.terminal_productions:
            if grammar.terminal_labels[rule.terminal_id] == label:
                cells.setdefault((rule.head_id, i, i + 1), _Tree(rule.head_id, i, i + 1))
    for length in range(2, len(labels) + 1):
        for lo in range(len(labels) - length + 1):
            hi = lo + length
            for middle in range(lo + 1, hi):
                for binary in grammar.binary_productions:
                    left = cells.get((binary.left_id, lo, middle))
                    right = cells.get((binary.right_id, middle, hi))
                    if left is not None and right is not None:
                        cells.setdefault(
                            (binary.head_id, lo, hi), _Tree(binary.head_id, lo, hi, left, right)
                        )
    tree = cells.get((grammar.start_nonterminal_id, 0, len(labels)))
    if tree is None:
        raise ValueError("witness has no independent Boolean CNF derivation")
    return tree


def export_lean_budget_proof(value: object) -> LeanExport:
    """Export every cap in a v2 original-input proof, with exact integer units."""
    checked = verify_budget_proof(value)
    state, results = read_budget_proof(value)
    graph = results[0].proof_graph
    certificate = results[0].path_result.certificate
    weights = [a.reward for a in graph.arcs]
    weights += [r[-1] for r in certificate.epsilon_bounds]
    weights += [r[-1] for r in certificate.grammar_bounds]
    weights += [r.objective_value for r in results if r.objective_value is not None]
    denominator = lcm(*(v.denominator for v in weights))

    def units(value: Fraction) -> int:
        scaled = value * denominator
        if scaled.denominator != 1 or scaled < 0:
            raise ValueError("reward has no exact nonnegative integer representation")
        return scaled.numerator

    rank = {node: i for i, node in enumerate(graph.nodes)}
    node_count = len(rank)

    def node(node_id: int) -> str:
        return f"(⟨{rank[node_id]}, by decide⟩ : Fin {node_count})"

    strings = sorted(
        {label for label in state.grammar.terminal_labels.values() if isinstance(label, str)}
        | {a.label for a in graph.arcs if isinstance(a.label, str)}
    )
    string_ids = {label: 256 + i for i, label in enumerate(strings)}

    def label_id(label: TerminalLabel) -> int:
        return string_ids[label] if isinstance(label, str) else label

    fingerprint = str(checked["input_fingerprint"])
    lines = [
        "import MWPC",
        "-- Generated; edit the original JSON proof, never this certificate.",
        f"-- Original-input SHA-256: {fingerprint}",
        f"-- Integer reward unit: 1/{denominator}",
        "-- Scope: finite resource CFG graph; Python independently checks input correspondence.",
        "set_option maxRecDepth 100000",
        "set_option maxHeartbeats 100000000",
        "namespace MWPC.Generated",
    ]
    arc_names = {a.arc_id: f"arc{i}" for i, a in enumerate(graph.arcs)}
    for arc in graph.arcs:
        label = "none" if arc.label is None else f"some {label_id(arc.label)}"
        lines.append(
            f"def {arc_names[arc.arc_id]} : Arc {node_count} := "
            f"⟨{node(arc.source)}, {node(arc.target)}, {label}, {units(arc.reward)}, {arc.cost}⟩"
        )
    terminals = ", ".join(
        f"({r.head_id}, {label_id(state.grammar.terminal_labels[r.terminal_id])})"
        for r in state.grammar.terminal_productions
    )
    binaries = ", ".join(
        f"({r.head_id}, {r.left_id}, {r.right_id})" for r in state.grammar.binary_productions
    )
    lines += [
        f"def grammar : Grammar := ⟨{state.grammar.start_nonterminal_id}, [{terminals}], "
        f"[{binaries}], {str(state.grammar.accepts_empty).lower()}⟩",
        f"def graph : Graph {node_count} := ⟨{node(graph.start)}, "
        f"[{', '.join(node(f) for f in graph.finals)}], [{', '.join(arc_names.values())}]⟩",
        f"def epsilonTable (u v : Fin {node_count}) (k : Nat) : Option Nat :=",
        "  match u.val, v.val, k with",
    ]
    for u, v, k, weight in certificate.epsilon_bounds:
        lines.append(f"  | {rank[u]}, {rank[v]}, {k} => some {units(weight)}")
    lines += [
        "  | _, _, _ => none",
        f"def grammarTable (head : Nat) (u v : Fin {node_count}) (k : Nat) : Option Nat :=",
        "  match head, u.val, v.val, k with",
    ]
    for head, u, v, k, weight in certificate.grammar_bounds:
        lines.append(f"  | {head}, {rank[u]}, {rank[v]}, {k} => some {units(weight)}")
    lines += [
        "  | _, _, _, _ => none",
        f"def potentials : Potentials {node_count} := "
        f"⟨{certificate.max_budget}, epsilonTable, grammarTable⟩",
        "theorem valid : ValidPotentials grammar graph potentials := by",
        "  constructor <;> decide",
    ]

    def epsilon(arcs: tuple[ResourceArc, ...], source: int) -> str:
        proof = f"(Epsilon.identity {node(source)})"
        for arc in arcs:
            if arc.label is not None:
                raise ValueError("visible arc in epsilon witness")
            proof = f"(Epsilon.step {arc_names[arc.arc_id]} (by decide) (by rfl) {proof})"
        return proof

    def derivation(tree: _Tree, segments: list[tuple[ResourceArc, ...]]) -> str:
        if tree.left is not None and tree.right is not None:
            return (
                f"(Derivation.binary (head := {tree.head}) (left := {tree.left.head}) "
                f"(right := {tree.right.head}) (by decide) {derivation(tree.left, segments)} "
                f"{derivation(tree.right, segments)})"
            )
        segment = segments[tree.lo]
        visible = next(i for i, a in enumerate(segment) if a.label is not None)
        arc = segment[visible]
        return (
            f"(Derivation.terminal {arc_names[arc.arc_id]} (head := {tree.head}) "
            f"(label := {label_id(arc.label) if arc.label is not None else 0}) "
            f"(by decide) (by rfl) "
            f"(by decide) {epsilon(segment[:visible], segment[0].source)} "
            f"{epsilon(segment[visible + 1 :], arc.target)})"
        )

    arc_by_id = {a.arc_id: a for a in graph.arcs}
    names = []
    for result in results:
        budget = result.budget
        if result.status is SolveStatus.INFEASIBLE_ON_SUPPORT:
            name = f"infeasible_{budget}"
            lines += [
                f"theorem absent_{budget} : AbsentRoots grammar graph potentials {budget} := by",
                "  unfold AbsentRoots; decide",
                f"theorem {name} : ¬ ∃ reward, Accepted grammar graph {budget} reward :=",
                f"  certified_infeasible valid (by decide) absent_{budget}",
            ]
        else:
            if result.objective_value is None or result.path_result.witness_arc_ids is None:
                raise ValueError("Lean export requires certified optimum or infeasibility")
            objective = units(result.objective_value)
            path = tuple(arc_by_id[i] for i in result.path_result.witness_arc_ids)
            final = path[-1].target if path else graph.start
            cost = sum(a.cost for a in path)
            labels = tuple(a.label for a in path if a.label is not None)
            if labels:
                indices = [i for i, a in enumerate(path) if a.label is not None]
                ends = [i + 1 for i in indices[:-1]] + [len(path)]
                starts = [0, *ends[:-1]]
                segments = [path[lo:hi] for lo, hi in zip(starts, ends, strict=True)]
                witness = "Or.inl " + derivation(_parse(state.grammar, labels), segments)
            else:
                witness = f"Or.inr ⟨by decide, {epsilon(path, graph.start)}⟩"
            name = f"optimal_{budget}"
            lines += [
                f"theorem roots_{budget} : RootUpper grammar graph potentials {budget} "
                f"{objective} := by",
                "  unfold RootUpper; decide",
                f"theorem witness_{budget} : Accepted grammar graph {budget} {objective} := by",
                f"  exact ⟨{node(final)}, by decide, {cost}, by decide, {witness}⟩",
                f"theorem {name} : Accepted grammar graph {budget} {objective} ∧",
                f"    ∀ reward, Accepted grammar graph {budget} reward → reward ≤ {objective} :=",
                f"  certified_optimal valid (by decide) roots_{budget} witness_{budget}",
            ]
        names.append(f"MWPC.Generated.{name}")
        lines.append(f"#print axioms {name}")
    lines += ["end MWPC.Generated", ""]
    return LeanExport("\n".join(lines), fingerprint, denominator, tuple(names))


def verify_with_lean(
    value: object, *, formal_directory: Path, lake: str = "lake", timeout_seconds: float = 180
) -> dict[str, object]:
    """Build pinned formal library and ask Lean's kernel to check the export.

    Does not install a toolchain or use network access. Missing Lean is an
    explicit failure, not a passing/skipped formal verification.
    """
    export = export_lean_budget_proof(value)
    executable = shutil.which(lake)
    if executable is None:
        raise FileNotFoundError("Lean/Lake is required; install the pinned formal/lean-toolchain")
    root = formal_directory.resolve(strict=True)
    toolchain = (root / "lean-toolchain").read_text().strip()
    sibling_elan = Path(executable).with_name("elan")
    elan = str(sibling_elan) if sibling_elan.is_file() else shutil.which("elan")
    # `elan run` without --install fails locally if the pinned toolchain is
    # missing. Unlike the usual Lake proxy it cannot download it implicitly.
    command = [elan, "run", toolchain, "lake"] if elan is not None else [executable]
    version = _run_lean(
        [*command, "env", "lean", "--version"],
        cwd=root,
        timeout=timeout_seconds,
    )
    if version.returncode or f"version {toolchain.split(':v')[-1]}" not in version.stdout:
        raise RuntimeError(
            f"Installed Lean does not match {toolchain}: {version.stdout}{version.stderr}"
        )
    build = _run_lean([*command, "build"], cwd=root, timeout=timeout_seconds)
    if build.returncode:
        raise RuntimeError(f"Lean library build failed: {build.stdout}{build.stderr}")
    with tempfile.TemporaryDirectory(prefix="mwpc-lean-") as temporary:
        source = Path(temporary) / "Certificate.lean"
        source.write_text(export.source, encoding="utf-8")
        run = _run_lean(
            [*command, "env", "lean", str(source)],
            cwd=root,
            timeout=timeout_seconds,
        )
    if run.returncode or "sorryAx" in run.stdout or "Lean.ofReduceBool" in run.stdout:
        raise RuntimeError(f"Lean kernel certificate failed: {run.stdout}{run.stderr}")
    dependencies = audit_lean_axioms(run.stdout, export.theorem_names)
    return {
        "verification": "PASS",
        "verification_scope": "kernel_checked_resource_cfg_optimality",
        "original_input_correspondence": "independent_python_checker",
        "input_fingerprint": export.input_fingerprint,
        "integer_denominator": export.denominator,
        "lean_version": version.stdout.strip(),
        "lean_source_sha256": hashlib.sha256(export.source.encode()).hexdigest(),
        "theorems": export.theorem_names,
        "axiom_audit": run.stdout.strip(),
        "axiom_dependencies": dependencies,
    }
