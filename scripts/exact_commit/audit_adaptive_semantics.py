"""Frozen-capture complete-label audit, including competent shared controls.

Prefix control implements CARS Algorithm 1/Equation 1 for a finite frozen
distribution with a perfect enumeration-backed oracle. Not native CARS timing.
This developmental audit is not a newly invented held-out benchmark.
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import itertools
import json
import platform
import subprocess
from datetime import UTC, datetime
from fractions import Fraction
from functools import partial
from math import prod
from pathlib import Path
from random import Random
from statistics import median
from time import perf_counter

from scripts.exact_commit.adaptive_semantics import AdaptiveSemanticSampler, compile_semantic_core
from scripts.exact_commit.capture_semantic_reference import execute
from scripts.exact_commit.semantic_json import boolean_rule_grammar, evaluate_semantics

from mwpc_exact.cfg_posterior import _categorical, compile_cfg_sampler
from mwpc_exact.conflict_proof import read_state
from mwpc_exact.mass_certificate import ProbabilityInput
from mwpc_exact.reference.limits import CompilationLimit

ROOT = Path(__file__).resolve().parents[2]
CONFIG = ROOT / "configs/experiments/m36_adaptive_semantics_v1.json"


def _enumerated_draw(paths, weights, rng):
    return paths[_categorical(weights, rng)]


class PrefixControl:
    """Exact trie subtraction with every invalid successor of visited prefixes."""

    def __init__(self, paths, target):
        self.root = {"mass": 0, "valid": False, "children": {}}
        self.draws = self.rejections = self.prunes = 0
        for path, weight, profile in paths:
            node = self.root
            for token in (*path, None):
                node["mass"] += weight
                node["valid"] |= profile == target
                if token is not None:
                    node = node["children"].setdefault(
                        token, {"mass": 0, "valid": False, "children": {}}
                    )

    def sample(self, rng):
        while self.root["mass"] and self.root["valid"]:
            node, visited, path = self.root, [], []
            while node["children"]:
                visited.append(node)
                choices = tuple(sorted(node["children"]))
                token = choices[
                    _categorical(tuple(node["children"][t]["mass"] for t in choices), rng)
                ]
                path.append(token)
                node = node["children"][token]
            self.draws += 1
            valid = node["valid"]
            for parent in reversed(visited):
                for child in parent["children"].values():
                    if not child["valid"] and child["mass"]:
                        child["mass"] = 0
                        self.prunes += 1
                parent["mass"] = sum(c["mass"] for c in parent["children"].values())
            if valid:
                return tuple(path)
            self.rejections += 1
        raise ValueError("ZERO_MASS_ON_SUPPORT")


def load(config):
    archive = ROOT / config["input_archive"]
    for line in (archive / "SHA256SUMS").read_text().splitlines():
        digest, name = line.split()
        if hashlib.sha256((archive / name).read_bytes()).hexdigest() != digest:
            raise ValueError("source archive changed")
    if (
        hashlib.sha256((archive / "input.json.gz").read_bytes()).hexdigest()
        != config["input_sha256"]
    ):
        raise ValueError("frozen input changed")
    with gzip.open(archive / "input.json.gz", "rt") as stream:
        raw = json.load(stream)
    data = ProbabilityInput(
        read_state(raw["input"]),
        tuple(tuple(Fraction(*p) for p in row) for row in raw["probabilities"]),
    )
    capture = json.loads((archive / "config.json").read_text())
    return raw, data, capture


def replay(output):
    """Independent finite execution/path audit, not a solver correctness proof."""
    for line in (output / "SHA256SUMS").read_text().splitlines():
        digest, name = line.split()
        if hashlib.sha256((output / name).read_bytes()).hexdigest() != digest:
            raise ValueError("adaptive archive changed")
    config = json.loads((output / "config.json").read_text())
    _, data, capture = load(config)
    preparation = json.loads((output / "preparation.json").read_text())
    rows = [json.loads(line) for line in (output / "rows.jsonl").read_text().splitlines()]
    paths, masses = {}, [Fraction(0)] * (1 << len(capture["records"]))
    for path in itertools.product(*data.state.support.rows):
        rule = json.loads(data.state.tokenizer_adapter.detokenize_bytes(path))
        profile = sum(1 << i for i, r in enumerate(capture["records"]) if execute(rule, r))
        weight = prod(
            data.probabilities[i][support.index(t)]
            for i, (t, support) in enumerate(zip(path, data.state.support.rows, strict=True))
        )
        paths[path] = profile
        masses[profile] += weight
    expected_keys = set(itertools.product(range(len(masses)), config["seeds"]))
    observed_keys = [(r["target"], r["metadata"]["seed"]) for r in rows]
    if len(observed_keys) != len(expected_keys) or set(observed_keys) != expected_keys:
        raise ValueError("archive omitted or duplicated a target/seed")
    expected_methods = {"adaptive", "eager", "enumeration", "prefix_control", "certified_core"}
    for row in rows:
        target, core = row["target"], row["core"]
        if Fraction(*row["mass"]) != masses[target]:
            raise ValueError("archived target mass differs from direct enumeration")
        metadata = dict(row["metadata"])
        metadata.pop("seed")
        if metadata != preparation["metadata"] or set(row["methods"]) != expected_methods:
            raise ValueError("inconsistent provenance/methods")
        if core["active"] is not None:
            mask = sum(1 << i for i in core["active"])
            if core["violation_counts"] != [0] * len(capture["records"]) or any(
                (profile & mask == target & mask) != (profile == target)
                for profile in paths.values()
            ):
                raise ValueError("structural core lost or gained an original token path")
        for method, result in row["methods"].items():
            expected_status = (
                "exact_on_support" if masses[target] else "zero_valid_probability_on_support"
            )
            if result["status"] not in (expected_status, "UNRESOLVED_RESOURCE_LIMIT"):
                raise ValueError("method status contradicts exhaustive finite oracle")
            if (
                result["status"] == "exact_on_support"
                and len(result["samples"]) != config["samples_per_positive_target"]
            ):
                raise ValueError("positive target has an incomplete sample batch")
            if any(paths.get(tuple(path)) != target for path in result["samples"]):
                raise ValueError("sample fails independent all-record execution")
            if method == "adaptive" and (
                result["rejections"] > len(capture["records"])
                or result["draws"] > len(result["samples"]) + len(capture["records"])
            ):
                raise ValueError("finite refinement bound failed")
    return config, preparation, rows


def summarize(output):
    config, prep, rows = replay(output)
    positive = [r for r in rows if Fraction(*r["mass"]) > 0]
    lines = [
        "# Complete developmental execution-conditioning audit",
        "",
        f"Producing commit: `{prep['metadata']['git_commit']}`.",
        "Config: `configs/experiments/m36_adaptive_semantics_v1.json`; "
        f"raw: `{output.relative_to(ROOT)}`.",
        "",
        f"All {prep['targets']} labels x {len(config['seeds'])} seeds = {len(rows)} rows; "
        f"{prep['programs']} original-token programs; {prep['positive_targets']} positive labels. "
        "Every archived mass, core equivalence and returned path was checked "
        "by independent enumeration/execution.",
        "",
        "This reuses one developmental MDLM canvas, not an external/held-out benchmark. "
        "Prefix timing is a finite control with a perfect precomputed oracle, "
        "not native CARS/EPIC. "
        "All methods receive identical archived rational probabilities; no model forward is timed.",
        "",
        "| Method | Exact positive rows | Correct zero rows | Resource refusals | "
        "Median positive batch (ms) | Sum of all batch times (s) |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for name in rows[0]["methods"]:
        results = [r["methods"][name] for r in rows]
        durations = [r["methods"][name]["query_seconds"] for r in positive]
        counts = {
            status: sum(r["status"] == status for r in results)
            for status in (
                "exact_on_support",
                "zero_valid_probability_on_support",
                "UNRESOLVED_RESOURCE_LIMIT",
            )
        }
        lines.append(
            f"| {name} | {counts['exact_on_support']} | "
            f"{counts['zero_valid_probability_on_support']} | "
            f"{counts['UNRESOLVED_RESOURCE_LIMIT']} | {median(durations) * 1000:.3f} | "
            f"{sum(r['query_seconds'] for r in results):.6f} |"
        )
    unique = {r["target"]: r for r in rows}
    certified = [r for r in unique.values() if r["core"]["active"] is not None]
    histogram = {k: sum(len(r["core"]["active"]) == k for r in certified) for k in range(12)}
    lines.extend(
        [
            "",
            f"Shared CFG compile: {prep['compile_seconds']:.6f} s; full-profile eager preparation: "
            f"{prep['eager_shared_seconds']:.6f} s; enumeration/oracle preparation: "
            f"{prep['enumeration_and_oracle_shared_seconds']:.6f} s.",
            f"Core certification (once per label, not once per seed): "
            f"{sum(r['core']['certification_shared_seconds'] for r in unique.values()):.6f} s; "
            f"core evaluation once per label: "
            f"{sum(r['core']['evaluate_shared_seconds'] for r in unique.values()):.6f} s.",
            f"Certified core sizes: `{ {k: v for k, v in histogram.items() if v} }`; "
            "maximum adaptive rejections: "
            f"{max(r['methods']['adaptive']['rejections'] for r in rows)}.",
            "",
            "Preparation is necessary and must be added before comparing total cost. "
            "Enumeration and full-profile inference share their preparation across all labels; "
            "core certification is shared only within a label. These are reusable controls. "
            "Four samples per positive row do not establish long-run amortization, "
            "denoising speed, universal superiority or scientific priority. "
            "Recorded slow paths and zeros are retained.",
        ]
    )
    return "\n".join(lines) + "\n"


def run(config, output):
    if subprocess.check_output(["git", "status", "--porcelain"], cwd=ROOT).strip():
        raise ValueError("commit producing code and protocol before audit")
    raw, data, capture = load(config)
    started = perf_counter()
    plan = compile_cfg_sampler(boolean_rule_grammar(capture["fields"]), data.state)
    compile_seconds = perf_counter() - started
    started = perf_counter()
    eager = evaluate_semantics(
        plan,
        data,
        capture["records"],
        max_profile_entries=config["max_profile_entries"],
        max_work=config["max_work"],
    )
    eager_seconds = perf_counter() - started
    started = perf_counter()
    paths, groups = [], [[] for _ in eager.profile_masses]
    for path in itertools.product(*data.state.support.rows):
        rule = json.loads(data.state.tokenizer_adapter.detokenize_bytes(path))
        profile = sum(1 << i for i, r in enumerate(capture["records"]) if execute(rule, r))
        weight = prod(
            eager._weights[i][row.index(t)]
            for i, (t, row) in enumerate(zip(path, data.state.support.rows, strict=True))
        )
        paths.append((path, weight, profile))
        groups[profile].append((path, weight))
    totals = tuple(sum(w for _, w in group) for group in groups)
    if tuple(Fraction(t, sum(totals)) * eager.syntax_mass for t in totals) != eager.profile_masses:
        raise ValueError("independent enumeration disagrees with every target mass")
    enumeration_seconds = perf_counter() - started
    metadata = {
        k: raw["metadata"][k]
        for k in (
            "model_id",
            "model_revision",
            "tokenizer_revision",
            "grammar_sha256",
            "support_policy",
            "exactness_scope",
            "hardware",
        )
    }
    metadata.update(
        git_commit=subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
        ).strip(),
        source_capture_commit=raw["metadata"]["git_commit"],
        config_sha256=hashlib.sha256(CONFIG.read_bytes()).hexdigest(),
        input_sha256=config["input_sha256"],
        python=platform.python_version(),
        platform=platform.platform(),
        claim_scope=config["claim_scope"],
        model_forward="not rerun",
        created_at_utc=datetime.now(UTC).isoformat(),
        model_capture_torch=raw["metadata"]["torch"],
    )
    output.mkdir(parents=True, exist_ok=False)
    (output / "config.json").write_bytes(CONFIG.read_bytes())
    (output / "preparation.json").write_text(
        json.dumps(
            {
                "metadata": metadata,
                "compile_seconds": compile_seconds,
                "eager_shared_seconds": eager_seconds,
                "enumeration_and_oracle_shared_seconds": enumeration_seconds,
                "programs": len(paths),
                "targets": len(groups),
                "positive_targets": sum(bool(t) for t in totals),
            },
            indent=2,
        )
        + "\n"
    )
    with (output / "rows.jsonl").open("w") as stream:
        for target, group in enumerate(groups):
            labels = tuple(bool(target & (1 << i)) for i in range(len(capture["records"])))
            start = perf_counter()
            core = core_posterior = None
            try:
                core = compile_semantic_core(
                    plan,
                    data,
                    capture["records"],
                    labels,
                    max_active=11,
                    max_profile_entries=config["max_profile_entries"],
                    max_work=config["max_work"],
                )
            except CompilationLimit:
                pass  # Record refusal for all seeds; never replace it with zero mass.
            core_setup_seconds = perf_counter() - start
            start = perf_counter()
            if core is not None:
                try:
                    core_posterior = core.evaluate(data)
                except CompilationLimit:
                    pass
            core_evaluate_seconds = perf_counter() - start
            if (
                core_posterior is not None
                and core_posterior.valid_mass != eager.profile_masses[target]
            ):
                raise ValueError("core does not reproduce full-specification mass")
            for seed in config["seeds"]:
                count = config["samples_per_positive_target"]
                labels = tuple(bool(target & (1 << i)) for i in range(len(capture["records"])))
                methods = {}
                for method in (
                    "adaptive",
                    "eager",
                    "enumeration",
                    "prefix_control",
                    "certified_core",
                ):
                    rng, samples, status = Random(seed), [], "exact_on_support"
                    start = perf_counter()
                    session = None
                    try:
                        if method == "adaptive":
                            session = AdaptiveSemanticSampler(
                                plan,
                                data,
                                capture["records"],
                                labels,
                                max_active=config["max_active"],
                                max_profile_entries=config["max_profile_entries"],
                                max_work=config["max_work"],
                            )
                            draw = partial(session.sample, rng)
                        elif method == "prefix_control":
                            session = PrefixControl(paths, target)
                            draw = partial(session.sample, rng)
                        elif method == "eager":
                            draw = partial(eager.sample, target, rng)
                        elif method == "certified_core":
                            if core_posterior is None:
                                raise CompilationLimit("core certification/evaluation refused")
                            draw = partial(core_posterior.sample, rng)
                        else:
                            draw = partial(
                                _enumerated_draw,
                                tuple(p for p, _ in group),
                                tuple(w for _, w in group),
                                rng,
                            )
                        if method in ("eager", "enumeration") and not totals[target]:
                            raise ValueError("ZERO_MASS_ON_SUPPORT")
                        for _ in range(count):
                            path = draw()
                            samples.append(path)
                    except CompilationLimit:
                        status = "UNRESOLVED_RESOURCE_LIMIT"
                    except ValueError as error:
                        if "ZERO_MASS_ON_SUPPORT" not in str(error):
                            raise
                        status = "zero_valid_probability_on_support"
                    result = {
                        "status": status,
                        "query_seconds": perf_counter() - start,
                        "samples": samples,
                    }
                    if any(path not in {p for p, _ in group} for path in samples):
                        raise RuntimeError("returned sample violates the full specification")
                    if session is not None:
                        result.update(draws=session.draws, rejections=session.rejections)
                        if method == "adaptive":
                            result.update(
                                active=list(session.active),
                                proposal_mass=[
                                    session.proposal_mass.numerator,
                                    session.proposal_mass.denominator,
                                ],
                            )
                            if session.rejections > len(labels) or session.draws > count + len(
                                labels
                            ):
                                raise RuntimeError("refinement theorem bound violated")
                        else:
                            result["pruned_prefixes"] = session.prunes
                    expected = (
                        "exact_on_support"
                        if totals[target]
                        else "zero_valid_probability_on_support"
                    )
                    if status != expected and status != "UNRESOLVED_RESOURCE_LIMIT":
                        raise RuntimeError(
                            f"{method} target {target} incorrectly classified/unresolved: {status}"
                        )
                    methods[method] = result
                stream.write(
                    json.dumps(
                        {
                            "metadata": dict(metadata, seed=seed),
                            "target": target,
                            "mass": [
                                eager.profile_masses[target].numerator,
                                eager.profile_masses[target].denominator,
                            ],
                            "methods": methods,
                            "core": {
                                "active": core.active if core else None,
                                "violation_counts": core.violation_counts if core else None,
                                "probe_evaluations": core.probe_evaluations if core else None,
                                "certification_shared_seconds": core_setup_seconds,
                                "evaluate_shared_seconds": core_evaluate_seconds,
                            },
                        },
                        sort_keys=True,
                    )
                    + "\n"
                )
            if target % 32 == 31:
                print(f"audited targets 0..{target}", flush=True)
    sums = "".join(
        f"{hashlib.sha256((output / n).read_bytes()).hexdigest()}  {n}\n"
        for n in ("config.json", "preparation.json", "rows.jsonl")
    )
    (output / "SHA256SUMS").write_text(sums)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--summary", action="store_true")
    args = parser.parse_args()
    if args.summary:
        print(summarize(args.output.resolve()), end="")
    elif args.check:
        config, preparation, rows = replay(args.output)
        print(
            f"Independent replay: {len(rows)} target/seed rows; complete path/core/mass checks PASS"
        )
    else:
        run(json.loads(CONFIG.read_text()), args.output)
