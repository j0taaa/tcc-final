"""Reconstruct upper provenance output law; compare independent literal words."""

import argparse
import importlib
import itertools
import json
import math
import random
import subprocess
import traceback
from fractions import Fraction as F
from functools import lru_cache
from pathlib import Path

from mwpc_exact.cfg_posterior import compile_cfg_sampler
from mwpc_exact.reference.json_grammar import json_source_grammar

base = importlib.import_module("attempts.50-grammar-residual-coupling.work.verify")
ref = importlib.import_module("attempts.50-grammar-residual-coupling.work.upper")


def portions(cumulative):
    previous = 0
    for weight in cumulative:
        yield F(weight - previous, cumulative[-1]) if cumulative[-1] else F(0)
        previous = weight


def reconstruction(solver):
    def combine(first, second):
        result = {}
        for x, px in first.items():
            for y, py in second.items():
                assert not {i for i, _ in x} & {i for i, _ in y}
                marks = tuple(sorted((*x, *y)))
                result[marks] = result.get(marks, F(0)) + px * py
        return result

    def mark(term):
        if term.choice is None:
            return {(): F(1)}
        i, j = term.choice
        return {((i, solver.ids[i][j]),): F(1)}

    @lru_cache(None)
    def common(node, index):
        _, _, cumulative, actions = solver.profiles[node][index]
        result = {}
        for probability, action in zip(portions(cumulative), actions, strict=True):
            term = solver.plan.terms[node][action[0]]
            values = (
                combine(common(term.children[0], action[1]), common(term.children[1], action[2]))
                if term.children
                else mark(term)
            )
            for word, value in values.items():
                result[word] = result.get(word, F(0)) + probability * value
        return result

    @lru_cache(None)
    def exact(node, mode):
        result = {}
        for probability, term in zip(
            portions(solver.exact_cdfs[node][mode]), solver.plan.terms[node], strict=True
        ):
            if not probability:
                continue
            if not term.children:
                values = mark(term)
            elif mode != 2:
                values = combine(exact(term.children[0], mode), exact(term.children[1], mode))
            else:
                left, right = term.children
                a, b = solver.totals[left], solver.totals[right]
                branch_weights = [(a[0] - a[2]) * b[0], a[2] * (b[0] - b[2])]
                values = {}
                for chance, modes in zip(
                    portions(ref.cdf(branch_weights)), [(2, 0), (1, 2)], strict=True
                ):
                    if chance:
                        for word, value in combine(
                            exact(left, modes[0]), exact(right, modes[1])
                        ).items():
                            values[word] = values.get(word, F(0)) + chance * value
            for word, value in values.items():
                result[word] = result.get(word, F(0)) + probability * value
        return result

    return common, exact


def tail_oracle():
    checks = merges = 0
    choices = tuple(itertools.product([F(0), F(1, 2), F(1), F(2)], [1, 2, 8]))
    for size in range(5):
        for atoms in itertools.product(choices, repeat=size):
            for eta in [F(1), F(1, 2), F(1, 10)]:
                upper = ref.upper_groups([(r, w, i) for i, (r, w) in enumerate(atoms)], eta)
                assert sum(w for _, w in atoms) == sum(row[1] for row in upper)
                assert sorted(a for row in upper for a in row[3]) == list(range(size))
                merges += len(upper) < len({r for r, _ in atoms})
                for threshold in [F(0), F(1, 4), F(1, 2), F(3, 4), F(1), F(3, 2), F(2)]:
                    truth = sum(w for r, w in atoms if r > threshold)
                    bound = sum(row[1] for row in upper if row[0] > threshold)
                    assert truth <= bound <= (1 + eta) * truth
                    checks += 1
    return checks, merges


def fixtures():
    yield from base.fixtures()
    emissions = (
        b"[",
        b"]",
        *(str(i).encode() + b"," for i in range(6)),
        *(str(i).encode() for i in range(6)),
    )
    yield (
        "json-array-wide",
        "json",
        emissions,
        ((0,), tuple(range(2, 8)), tuple(range(2, 8)), tuple(range(8, 14)), (1,)),
        (0, None, None, None, 1),
    )


def run(output):
    output.mkdir(parents=True, exist_ok=False)
    try:
        tail_checks, merges = tail_oracle()
        counts = dict(
            tail_checks=tail_checks,
            nontrivial_merges=merges,
            word_checks=0,
            proposal_laws=0,
            singular_laws=0,
            sampled_valid=0,
            undefined=0,
            compressed_words=0,
        )
        rng = random.Random(20261013055)
        with (output / "rows.jsonl").open("w") as stream:
            for name, kind, emissions, rows, canvas in fixtures():
                source = base.source_dyck() if kind == "dyck" else json_source_grammar()
                for mode in ["equal", "different", "singular", "tiny", "low-mass", "zero-target"]:
                    target, draft = base.inputs(source, emissions, rows, canvas, mode, rng)
                    paths = list(itertools.product(*target.state.support.rows))
                    raw = [
                        {
                            ids: math.prod(
                                data.probabilities[i][rows[i].index(v)] for i, v in enumerate(ids)
                            )
                            if base.valid(b"".join(emissions[v] for v in ids), kind)
                            else F(0)
                            for ids in paths
                        }
                        for data in [target, draft]
                    ]
                    masses = [sum(row.values(), F(0)) for row in raw]
                    plan = compile_cfg_sampler(source, target.state)
                    if not all(masses):
                        try:
                            ref.UpperResidual(plan, target, draft)
                        except ValueError:
                            counts["undefined"] += 1
                            stream.write(
                                json.dumps(dict(case=name, mode=mode, undefined=True)) + "\n"
                            )
                            continue
                        raise AssertionError("undefined posterior admitted")
                    p, q = [
                        {ids: v / z for ids, v in rawrow.items()}
                        for rawrow, z in zip(raw, masses, strict=True)
                    ]
                    residual = {ids: max(F(0), p[ids] - q[ids]) for ids in paths}
                    delta = sum(residual.values(), F(0))
                    solver = ref.UpperResidual(plan, target, draft)
                    upper = solver.upper_raw / solver.za
                    assert delta <= upper <= solver.factor * delta
                    common, exact = reconstruction(solver)
                    proposal = {ids: F(0) for ids in paths}
                    accepted = dict(proposal)
                    seen = set()
                    for atom, (ratio, mass, _, _) in enumerate(solver.profiles[plan.root]):
                        words = common(plan.root, atom)
                        assert sum(words.values(), F(0)) == 1
                        for marks, probability in words.items():
                            ids = tuple(v for _, v in marks)
                            assert len(ids) == len(rows) and ids not in seen
                            seen.add(ids)
                            assert q[ids] and probability == q[ids] * solver.zb / mass
                            assert ratio >= (p[ids] * solver.za) / (q[ids] * solver.zb)
                            counts["compressed_words"] += ratio != (p[ids] * solver.za) / (
                                q[ids] * solver.zb
                            )
                            if ratio > solver.threshold:
                                value = (
                                    F(mass, solver.za) * (ratio - solver.threshold) * probability
                                )
                                proposal[ids] += value / upper
                                acceptance = solver.correction(
                                    p[ids] * solver.za, q[ids] * solver.zb, ratio
                                )
                                accepted[ids] += value / upper * acceptance
                    if solver.singular:
                        words = exact(plan.root, 2)
                        assert sum(words.values(), F(0)) == 1
                        for marks, probability in words.items():
                            ids = tuple(v for _, v in marks)
                            assert not q[ids] and p[ids] > 0
                            assert probability == p[ids] * solver.za / solver.singular
                            assert ids not in seen
                            seen.add(ids)
                            value = F(solver.singular, solver.za) * probability / upper
                            proposal[ids] += value
                            accepted[ids] += value
                        counts["singular_laws"] += 1
                    counts["word_checks"] += len(paths)
                    if delta:
                        assert sum(proposal.values(), F(0)) == 1
                        rate = sum(accepted.values(), F(0))
                        assert rate > F(1, 2)
                        assert all(accepted[ids] / rate == residual[ids] / delta for ids in paths)
                        counts["proposal_laws"] += 1
                        for _ in range(24):
                            ids, attempts = solver.sample(rng)
                            assert residual[ids] > 0 and attempts >= 1
                            counts["sampled_valid"] += 1
                        assert solver.sample(rng, max_attempts=0) == (None, 0)
                    else:
                        assert not upper
                        try:
                            solver.sample(rng)
                        except ValueError:
                            pass
                        else:
                            raise AssertionError("undefined residual returned")
                    stream.write(
                        json.dumps(
                            dict(
                                case=name,
                                mode=mode,
                                delta=str(delta),
                                upper=str(upper),
                                stored_parts=solver.stored_parts,
                                **counts,
                            )
                        )
                        + "\n"
                    )
        summary = dict(
            status="CORRECTNESS_ONLY",
            **counts,
            producer=subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
        )
        (output / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
        print(json.dumps(summary), flush=True)
    except Exception:
        (output / "failure.txt").write_text(traceback.format_exc())
        raise


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    run(parser.parse_args().output)
