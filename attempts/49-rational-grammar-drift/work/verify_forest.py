"""Original-ID exhaustive oracle with separate stack/JSON recognizers."""

import argparse
import importlib
import itertools
import json
import math
import random
import subprocess
import traceback
from fractions import Fraction as F
from pathlib import Path

from mwpc_exact.cfg_posterior import compile_cfg_sampler
from mwpc_exact.eos_policy import EOSMode, EOSPolicy
from mwpc_exact.mass_certificate import ProbabilityInput
from mwpc_exact.reference.byte_grammars import _SourceGrammarBuilder
from mwpc_exact.reference.json_grammar import json_source_grammar
from mwpc_exact.reference.normalization import normalize_to_cnf
from mwpc_exact.state import SelectionInput
from mwpc_exact.support import SupportPolicy, build_per_position_support
from mwpc_exact.tokenizer_bytes import CompositionalByteLevelAdapter
from mwpc_exact.types import SupportKind

certificate = importlib.import_module("attempts.49-rational-grammar-drift.work.forest").certificate


def dyck_source():
    builder = _SourceGrammarBuilder(("S", "N"), start="S")
    builder.rule("S", "N", "S")
    builder.rule("S")
    builder.rule("N", b"(", "S", b")")
    builder.rule("N", b"[", "S", b"]")
    return builder.build()


def recognizes(word, kind):
    if kind == "json":
        try:
            json.loads(word)
            return True
        except (ValueError, UnicodeError):
            return False
    stack = []
    for byte in word:
        if byte in b"([":
            stack.append(byte)
        elif not stack or stack.pop() != {41: 40, 93: 91}.get(byte):
            return False
    return not stack


def fixtures():
    yield "dyck-alias", "dyck", (b"(", b")", b"[", b"]", b"("), ((0, 1, 2, 3, 4),) * 4
    yield (
        "dyck-macro",
        "dyck",
        (b"(", b")", b"[", b"]", b"()", b"[]", b"([])", b"()"),
        (
            (0, 2, 4, 7),
            (0, 1, 2, 4, 6),
            (1, 3, 4, 5),
            (1, 3, 4, 7),
        ),
    )
    yield (
        "json-macro",
        "json",
        (b"[", b"0", b"]", b"[]", b"null", b"0", b'{"k":', b"}"),
        (
            (0, 3, 4, 6),
            (1, 4, 5, 7),
            (1, 2, 3, 7),
        ),
    )
    yield (
        "json-nesting",
        "json",
        (b"[", b'{"a":', b"0", b"1", b",", b"]", b"}", b" ", b'{"b":'),
        (
            (0, 1),
            (0, 2, 8),
            (2, 3, 4, 5, 6),
            (2, 3, 5, 6, 7),
            (5, 6, 7),
        ),
    )
    yield "json-infeasible", "json", (b"]", b"}"), ((0, 1),) * 2


def make_inputs(source, emissions, rows, mode, rng):
    support = build_per_position_support(
        canvas=(None,) * len(rows),
        policy=SupportPolicy(kind=SupportKind.EXPLICIT, vocabulary_size=len(emissions)),
        explicit_support=dict(enumerate(rows)),
    )
    state = SelectionInput(
        normalize_to_cnf(source).grammar,
        (None,) * len(rows),
        (),
        support,
        CompositionalByteLevelAdapter(emissions),
        EOSPolicy(EOSMode.ABSENT),
    )
    first = tuple(tuple(F(1, len(row)) for _ in row) for row in support.rows)
    if mode == "equal":
        second = first
    elif mode == "tiny-scale":
        second = tuple(tuple(p / (1 << (64 * (i + 1))) for p in row) for i, row in enumerate(first))
    elif mode == "zero":
        second = tuple((F(),) * len(row) for row in first)
    elif mode == "near-equal":
        second = tuple(
            tuple(
                p + (F(1, 1 << 256) if j == 0 else -F(1, 1 << 256) if j == 1 else F())
                for j, p in enumerate(row)
            )
            for row in first
        )
    else:
        raw = [tuple(rng.randrange(1, 10) for _ in row) for row in first]
        second = tuple(tuple(F(v, sum(row)) for v in row) for row in raw)
    return ProbabilityInput(state, first), ProbabilityInput(state, second)


def expected(first, second, emissions, kind):
    left, right = [], []
    for path in itertools.product(*[range(len(row)) for row in first.state.support.rows]):
        ids = tuple(first.state.support.rows[i][j] for i, j in enumerate(path))
        if recognizes(b"".join(emissions[t] for t in ids), kind):
            left.append(math.prod(first.probabilities[i][j] for i, j in enumerate(path)))
            right.append(math.prod(second.probabilities[i][j] for i, j in enumerate(path)))
    a, b = sum(left, F()), sum(right, F())
    return (
        None
        if not a or not b
        else sum((abs(x / a - y / b) for x, y in zip(left, right, strict=True)), F()) / 2
    )


def run(output, known_root=False):
    output.mkdir(parents=True, exist_ok=False)
    rng = random.Random(202610120492)
    count = certified = zero = 0
    engines = (
        [
            importlib.import_module("attempts.49-rational-grammar-drift.work." + name)
            for name in [
                "adaptive_angular",
                "calibrated_endpoint",
                "hybrid_endpoint",
                "ordered_planar",
            ]
        ]
        if known_root
        else [None]
    )
    try:
        with (output / "rows.jsonl").open("w") as stream:
            for name, kind, emissions, rows in fixtures():
                source = dyck_source() if kind == "dyck" else json_source_grammar()
                for mode in ["equal", "tiny-scale", "zero", "near-equal", "different"]:
                    first, second = make_inputs(source, emissions, rows, mode, rng)
                    plan = compile_cfg_sampler(source, first.state)
                    truth = expected(first, second, emissions, kind)
                    for epsilon in [F(1), F(1, 2), F(1, 10)]:
                        for engine in engines:
                            report = certificate(
                                plan,
                                first,
                                second,
                                epsilon,
                                compressor=engine,
                                exact_passthrough=known_root,
                                known_root_query=known_root,
                            )
                            if truth is None:
                                assert report["status"] == "ZERO_VALID_MASS_UNDEFINED_TV"
                                zero += 1
                            else:
                                assert (
                                    report["lower"]
                                    <= truth
                                    <= report["upper"]
                                    <= (1 + epsilon) * report["lower"]
                                )
                                if known_root:
                                    assert (
                                        report["root_rows"] == 0
                                        and report["root_streamed_candidates"] >= 0
                                    )
                                certified += 1
                            count += 1
                            row = dict(
                                case=name,
                                mode=mode,
                                epsilon=str(epsilon),
                                engine=None
                                if engine is None
                                else engine.__name__.rsplit(".", 1)[-1],
                                expected=str(truth),
                                **report,
                            )
                            stream.write(json.dumps(row, default=str) + "\n")
        summary = dict(
            status="CORRECTNESS_ONLY",
            cases=count,
            certified=certified,
            zero_mass=zero,
            known_root_query=known_root,
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
    parser.add_argument("--known-root", action="store_true")
    args = parser.parse_args()
    run(args.output, args.known_root)
