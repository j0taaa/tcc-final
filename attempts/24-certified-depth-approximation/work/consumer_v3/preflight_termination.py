"""Opt-in native terminated-language oracle; no model forward or speed claim."""

import argparse
import hashlib
import itertools
import json
import platform
from fractions import Fraction
from pathlib import Path

import numpy as np

from ..certificate import CounterTable
from .mosaic_control import accepts, fixed_logits, load, materialize, minimize
from .termination import posterior, terminated_graph
from .test_termination import LIMITS, enumerate_terminated, examples, fixture


def run(source, devices):
    import torch

    old_precision = torch.get_float32_matmul_precision()
    module, origin = load(source)
    torch.set_num_threads(1)
    records, language_checks, marginal_checks, sample_checks, mass_checks = [], 0, 0, 0, 0
    try:
        torch.set_float32_matmul_precision("high")
        for case, (words, canvas, eot, pad) in enumerate(examples()):
            rows = [
                [1 + (p + 2 * t + case) % 3 for t in range(len(words))] for p in range(len(canvas))
            ]
            table, weights = fixture(words, rows, canvas, eot, pad)
            full_mass = sum(enumerate_terminated(words, weights, eot, pad).values(), Fraction())
            for depth in (0, 1, 2, None):
                raw = terminated_graph(table, canvas, depth, eot, pad, symbolic=True, **LIMITS)
                graph = minimize(raw, table)
                law = enumerate_terminated(words, weights, eot, pad, depth)
                mass = sum(law.values(), Fraction())
                domains = [(t,) if t is not None else range(len(words)) for t in canvas]
                for word in itertools.product(*domains):
                    assert accepts(graph, word) == (word in law), (case, depth, word)
                    language_checks += 1
                post = posterior(graph, table, weights, **LIMITS)
                assert post.mass == mass
                mass_checks += 1
                if depth is not None:
                    upper, _ = CounterTable(table).tail(weights, depth, sums=weights.sums)
                    assert upper >= full_mass - mass
                    mass_checks += 1
                if not mass:
                    records.append(dict(case=case, depth=depth, status="zero_mass"))
                    continue
                expected = np.array(
                    [
                        [
                            float(sum((v for w, v in law.items() if w[p] == t), Fraction()) / mass)
                            for t in range(len(words))
                        ]
                        for p in range(len(canvas))
                    ]
                )
                for device in devices:
                    for kind in ("sequential", "parallel"):
                        for mode, dtype, product, tolerance in (
                            ("fp32", torch.float32, None, 5e-3),
                            ("fp32_product64", torch.float32, torch.float64, 5e-3),
                            ("fp64", torch.float64, torch.float64, 1e-10),
                        ):
                            if kind == "sequential" and mode == "fp32_product64":
                                continue
                            sampler, stats = materialize(
                                graph, module, kind=kind, dtype=dtype, device=device
                            )
                            if kind == "parallel":
                                sampler.matmul_dtype = product
                            logits = fixed_logits(
                                torch.tensor(rows, dtype=dtype, device=device).log()[None], canvas
                            )
                            forced = torch.tensor(
                                [-1 if t is None else t for t in canvas], device=device
                            )
                            actual = (
                                sampler._compute_marginal_log(logits.log_softmax(-1), forced[None])
                                .exp()[0]
                                .cpu()
                                .numpy()
                            )
                            error = float(np.max(np.abs(actual - expected)))
                            assert np.isfinite(actual).all() and error <= tolerance
                            marginal_checks += actual.size
                            torch.manual_seed(1733 + case)
                            tokens, confidence = sampler.sample(
                                logits.expand(8, -1, -1), forced, return_marginal=True
                            )
                            confidence = confidence.cpu().numpy()
                            sample_error = 0.0
                            for b, word in enumerate(tokens.cpu().tolist()):
                                assert tuple(word) in law
                                sample_error = max(
                                    sample_error,
                                    float(
                                        np.max(
                                            np.abs(
                                                confidence[b]
                                                - [expected[p, t] for p, t in enumerate(word)]
                                            )
                                        )
                                    ),
                                )
                                sample_checks += 1
                            assert np.isfinite(confidence).all() and sample_error <= tolerance
                            records.append(
                                dict(
                                    case=case,
                                    depth=depth,
                                    kind=kind,
                                    mode=mode,
                                    device=device,
                                    status="pass",
                                    **stats,
                                    max_absolute_marginal_error=error,
                                    max_absolute_sampled_confidence_error=sample_error,
                                    absolute_tolerance=tolerance,
                                )
                            )
    finally:
        torch.set_float32_matmul_precision(old_precision)
    return dict(
        scope="variable JSON EOT PAD*; small correctness only; no forward or speed gate",
        mosaic=origin,
        torch=torch.__version__,
        python=platform.python_version(),
        cuda=torch.version.cuda,
        gpu=torch.cuda.get_device_name() if "cuda" in devices else None,
        native_kernel_matmul_precision="high",
        language_checks=language_checks,
        exact_mass_tail_checks=mass_checks,
        original_id_marginal_checks=marginal_checks,
        valid_sample_checks=sample_checks,
        records=records,
        own_source_sha256={
            p.name: hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(Path(__file__).parent.glob("*.py"))
        },
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--devices", nargs="+", default=["cpu"])
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = run(args.source, args.devices)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(
        json.dumps(
            {k: v for k, v in result.items() if k not in ("records", "mosaic", "own_source_sha256")}
        )
    )


if __name__ == "__main__":
    main()
