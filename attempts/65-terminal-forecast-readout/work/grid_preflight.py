"""Prospective classical grid-control oracles; no real model or data."""

from __future__ import annotations

import argparse
import itertools
import json
import time
from fractions import Fraction as F
from pathlib import Path

import torch
from grid_control import SPELLINGS, SemanticParser, moments, native_moments
from native_adapter import load_native, restore_rng, rng_digest, rng_state
from native_path_oracle import enumeration, independent_marginal_error
from native_preflight import SCHEMA, SyntheticTokenizer, fixtures, run_step


def syntax_oracle():
    checks = 0
    for spelling, value in SPELLINGS.items():
        text = '{"probabilities":{"a":' + spelling + ',"b":0.20}}'
        parser = SemanticParser(("a", "b"), {2: text}, 0, 1)
        state, events = parser.prefix((2, 0, 1))
        obj = json.loads(text, parse_float=F, parse_int=F)["probabilities"]
        assert state.ended and dict(events) == {0: value, 1: 20}
        assert value == 100 * obj["a"] and obj["b"] == F(1, 5)
        checks += 1
    bad = [
        '{"probabilities":{"b":0,"a":0}}',
        '{"probabilities":{"a":00,"b":0}}',
        '{"probabilities":{"a":0.001,"b":0}}',
        '{"probabilities":{"a":1.01,"b":0}}',
        '{"probabilities":{"a":0 .1,"b":0}}',
        '{"probabilities":{"a":-0.1,"b":0}}',
        '{"probabilities":{"a":0,"b":0.}}',
        '{"probabilities":{"a":0,"b":0}}X',
    ]
    for text in bad:
        parser = SemanticParser(("a", "b"), {2: text}, 0, 1)
        try:
            parser.prefix((2, 0))
        except ValueError:
            pass
        else:
            raise AssertionError(text)
    parser = SemanticParser(("a", "b"), {2: '{"probabilities":{"a":0,"b":0}}'}, 0, 1)
    for ids in ((2,), (1,), (2, 1), (2, 0, 2)):
        try:
            state, _ = parser.prefix(ids)
        except ValueError:
            pass
        else:
            assert not state.ended
    return {
        "status": "PASS",
        "valid_spellings": checks,
        "invalid_spellings": len(bad),
        "control_guards": 4,
    }


def rational_oracle():
    specifications = [
        ("", [("0.40", "0.60"), ("0.01", "0.01"), ("0.00", "0.00")], [F(1, 3)] * 3),
        (
            '{"probabilities":{"a":0.',
            [("40", "0.60"), ("01", "0.01"), ("00", "0.00")],
            [F(1, 7), F(2, 7), F(4, 7)],
        ),
        (
            '{"probabilities":{"a":0.20,"b":',
            [(None, "0.80"), (None, "0.10"), (None, "0.00")],
            [F(1, 2), F(1, 3), F(1, 6)],
        ),
    ]
    reports = []
    for index, (prefix, values, weights) in enumerate(specifications):
        texts, layer0, layer1 = {9: prefix}, {0: []}, {}
        rows = []
        for j, ((a, b), weight) in enumerate(zip(values, weights, strict=True)):
            body = (
                (a + ',"b":' + b + "}}")
                if index == 1
                else b + "}}"
                if index == 2
                else '{"probabilities":{"a":' + a + ',"b":' + b + "}}"
            )
            texts[j + 2] = body
            layer0[0].append((j + 1, j + 2, weight))
            layer1[j + 1] = [(5, 0, F(3, 4)), (6, 8, F(1, 4))]
            raw = json.loads(prefix + body, parse_float=F, parse_int=F)["probabilities"]
            rows.append((weight * F(3, 4), tuple(raw.values())))
        texts[8] = ""
        parser = SemanticParser(("a", "b"), texts, 0, 1)
        prefix_ids = (9,) if prefix else ()
        result = moments([layer0, layer1], 0, {5: F(1), 6: F(1)}, parser, prefix_ids)
        mass = sum(p for p, _ in rows)
        points = [
            (p / mass, tuple(v / sum(raw) for v in raw) if sum(raw) else (F(1, 2), F(1, 2)))
            for p, raw in rows
        ]
        mean = tuple(sum(p * point[j] for p, point in points) for j in range(2))
        second = sum(p * sum(x * x for x in point) for p, point in points)
        assert result["alpha"] == F(3, 4)
        assert result["mean"] == mean and result["second_norm"] == second
        assert result["variance"] == second - sum(x * x for x in mean)
        dp_mass = sum(v[0] for v in result["by_sum"].values())
        for total, value in result["by_sum"].items():
            relevant = [
                (p, tuple(int(100 * x) for x in raw))
                for p, raw in rows
                if int(100 * sum(raw)) == total
            ]
            expected = [
                sum(p for p, _ in relevant),
                *[sum(p * raw[j] for p, raw in relevant) for j in range(2)],
                sum(p * sum(x * x for x in raw) for p, raw in relevant),
            ]
            assert tuple(v / dp_mass for v in value) == tuple(v / mass for v in expected)
        raw_mean = tuple(sum(p * raw[j] for p, raw in rows) / mass for j in range(2))
        shortcut = tuple(v / sum(raw_mean) for v in raw_mean)
        if index < 2:
            assert shortcut != mean
        reports.append(
            {
                "status": "PASS",
                "law": index,
                "alpha": str(result["alpha"]),
                "mean": list(map(str, mean)),
                "variance": str(result["variance"]),
                "completed_sum_states": len(result["by_sum"]),
                "naive_field_shortcut_equal": shortcut == mean,
            }
        )
    return reports


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    started = time.monotonic()
    before = rng_state()
    threads, precision = torch.get_num_threads(), torch.get_float32_matmul_precision()
    report = {
        "status": "RUNNING",
        "new_neural_forwards": 0,
        "real_model_tokenizer_loaded": False,
        "rows": [],
    }
    try:
        torch.set_num_threads(1)
        torch.set_float32_matmul_precision("highest")
        report["syntax"] = syntax_oracle()
        report["rational"] = rational_oracle()
        runtime, tokenizer = load_native(), SyntheticTokenizer()
        counters = {"native_propose_calls": 0, "synthetic_native_steps": 0, "additional_helpers": 0}
        expected = set(itertools.product(("cpu", "cuda:0"), (f["name"] for f in fixtures())))
        for device in ("cpu", "cuda:0"):
            compiler = runtime["matcher"].ConstraintCompiler(
                tokenizer,
                eos_token="<pad>",
                eot_token="<eot>",
                device=device,
                matmul_dtype=torch.float64,
                cache_size=1,
                compile_workers=0,
            )
            compiled = compiler.compile_json_schema(SCHEMA)
            for index, fixture in enumerate(fixtures()):
                if time.monotonic() - started > 600:
                    raise RuntimeError("Declared whole-check guard exceeded")
                actual = run_step(
                    runtime, compiled, tokenizer, fixture, index, device, 17, False, True, counters
                )
                snapshot = actual["snapshot"]
                result, reference = native_moments(snapshot), enumeration(snapshot)
                marginal_error = independent_marginal_error(snapshot, actual["initial_scores"])
                discrepancies = [
                    abs(result["alpha"] - reference["complete_probability_ideal_arithmetic"]),
                    abs(result["variance"] - reference["conditional_variance_ideal_arithmetic"]),
                    *[
                        abs(a - b)
                        for a, b in zip(
                            result["mean"],
                            reference["conditional_mean_ideal_arithmetic"],
                            strict=True,
                        )
                    ],
                ]
                assert max(discrepancies) <= 5e-5 and marginal_error <= 5e-5
                row = {
                    "device": device,
                    "fixture": fixture["name"],
                    "status": "PASS",
                    "alpha": result["alpha"],
                    "mean": result["mean"],
                    "variance": result["variance"],
                    "peak_states": result["peak_states"],
                    "semantic_transitions": result["semantic_transitions"],
                    "max_semantic_error": max(discrepancies),
                    "max_marginal_error": marginal_error,
                }
                report["rows"].append(row)
                with (args.output / "records.jsonl").open("a") as stream:
                    stream.write(json.dumps(row) + "\n")
                print(json.dumps(row), flush=True)
            compiler.close()
        assert {(r["device"], r["fixture"]) for r in report["rows"]} == expected and len(
            report["rows"]
        ) == 12
        report.update(status="PASS", **counters)
    except Exception as error:
        report.update(status="ERROR", error=repr(error))
        raise
    finally:
        restore_rng(before)
        torch.set_num_threads(threads)
        torch.set_float32_matmul_precision(precision)
        report["caller_rng_restored"] = rng_digest() == rng_digest(before)
        (args.output / "summary.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({k: v for k, v in report.items() if k != "rows"}))


if __name__ == "__main__":
    main()
