"""Opt-in correctness oracle, NOT a neural run or a performance benchmark."""

import argparse
import itertools
import json
import platform
from fractions import Fraction
from pathlib import Path
from time import monotonic

import numpy as np

from ..consumer_v2.test_query import enumerate_words, fixture
from ..stack_control import StackPrepared
from .mosaic_control import accepts, fixed_logits, load, materialize, minimize, sparse_graph


def examples():
    # Positive integer weights, aliases, final NUMBER flush, internal peaks,
    # split Unicode bytes, escapes, and a genuine fixed original-ID alias.
    return [
        ([b"0", b"1", b" ", b"[", b"]", b"0"], (None,) * 3),
        ([b"[]", b"{}", b"[[]]", b"[{}]", b"0", b" "], (None,) * 2),
        ([b'"', b"\xc3", b"\xa9", "é".encode(), b"a", b" ", b'\\"'], (0, None, None, 0)),
        ([b'"', b"\\", b'"a', b"a", b'\\"', b" "], (0, None, None, 0)),
        ([b"-", b"1", b"e", b"+", b" ", b"0"], (None,) * 3),
        ([b"{", b'"x":', b"0", b"}", b"[]", b" "], (0, 1, None, 3)),
        ([b"0", b"0", b"[]", b" ", b"[", b"]"], (1, None, None)),
        ([b"[", b"]", b"[[]]", b"0", b" "], (0, None, 1)),
    ]


def run(source, devices):
    import torch

    started = monotonic()
    before = torch.get_float32_matmul_precision()
    torch.set_float32_matmul_precision("highest")
    module, origin = load(source)
    assert torch.get_float32_matmul_precision() == "highest", "import changed caller precision"
    torch.set_num_threads(1)
    records, language_checks, marginal_checks, sample_checks = [], 0, 0, 0
    try:
        for case, (words, initial) in enumerate(examples()):
            rows = [
                [1 + ((p + 1) * (t + 3) + case) % 7 for t in range(len(words))]
                for p in range(len(initial))
            ]
            table, weights, _ = fixture(
                words, [rows[p] for p, t in enumerate(initial) if t is None], initial
            )
            for depth in (0, 1, 2, None):
                prepared = StackPrepared(
                    table,
                    initial,
                    max_depth=depth,
                    timeout_seconds=30,
                    max_cells=100_000,
                    max_edges=100_000,
                    max_terms=100_000,
                )
                raw_graph = sparse_graph(prepared)
                for representation, graph in (
                    ("descriptor", raw_graph),
                    ("minimal", minimize(raw_graph, table)),
                ):
                    # Reuse the SAME graph on a stricter canvas, not a recompilation.
                    canvases = [initial]
                    original_law = enumerate_words(table, weights, depth)
                    if original_law and sum(t is None for t in initial) > 1:
                        witness = next(iter(original_law))
                        p = next(p for p, t in enumerate(initial) if t is None)
                        canvases.append(
                            tuple(witness[i] if i == p else t for i, t in enumerate(initial))
                        )
                    for clamp, canvas in enumerate(canvases):
                        _, current, _ = fixture(
                            words,
                            np.asarray(
                                [rows[p] for p, t in enumerate(canvas) if t is None]
                            ).reshape(-1, len(words)),
                            canvas,
                        )
                        law = enumerate_words(table, current, depth)
                        domains = [(t,) if t is not None else range(len(words)) for t in canvas]
                        for word in itertools.product(*domains):
                            assert accepts(graph, word) == (word in law), (
                                case,
                                depth,
                                canvas,
                                word,
                            )
                            language_checks += 1
                        mass = sum(law.values(), Fraction())
                        if not mass:
                            records.append(
                                dict(
                                    case=case,
                                    depth=depth,
                                    clamp=clamp,
                                    representation=representation,
                                    status="zero_mass",
                                )
                            )
                            continue
                        expected = np.array(
                            [
                                [
                                    float(
                                        sum((v for w, v in law.items() if w[p] == t), Fraction())
                                        / mass
                                    )
                                    for t in range(len(words))
                                ]
                                for p in range(len(canvas))
                            ]
                        )
                        for device in devices:
                            modes = (
                                ("fp32", torch.float32, None, 5e-3),
                                ("fp32_product64", torch.float32, torch.float64, 5e-3),
                                ("fp64", torch.float64, torch.float64, 1e-10),
                            )
                            for kind in ("sequential", "parallel"):
                                for mode, dtype, product, tolerance in modes:
                                    if kind == "sequential" and mode == "fp32_product64":
                                        continue  # this kernel has no tree matmul_dtype option
                                    sampler, graph_stats = materialize(
                                        graph, module, kind=kind, dtype=dtype, device=device
                                    )
                                    if kind == "parallel":
                                        sampler.matmul_dtype = product
                                    # Native import normally enables high; retain it for the oracle.
                                    torch.set_float32_matmul_precision("high")
                                    logits = torch.tensor(rows, dtype=dtype, device=device).log()[
                                        None
                                    ]
                                    logits = fixed_logits(logits, canvas)
                                    forced = torch.tensor(
                                        [-1 if t is None else t for t in canvas], device=device
                                    )
                                    actual = (
                                        sampler._compute_marginal_log(
                                            logits.log_softmax(-1), forced[None]
                                        )
                                        .exp()[0]
                                        .cpu()
                                        .numpy()
                                    )
                                    error = float(np.max(np.abs(actual - expected)))
                                    assert np.isfinite(actual).all() and error <= tolerance, (
                                        case,
                                        depth,
                                        clamp,
                                        device,
                                        kind,
                                        mode,
                                        error,
                                        actual,
                                        expected,
                                    )
                                    marginal_checks += actual.size
                                    torch.manual_seed(1729 + case)
                                    sampled, confidence = sampler.sample(
                                        logits.expand(8, -1, -1), forced, return_marginal=True
                                    )
                                    sampled = sampled.cpu().tolist()
                                    confidence = confidence.cpu().numpy()
                                    sample_error = 0.0
                                    for b, word in enumerate(sampled):
                                        assert tuple(word) in law, (case, kind, mode, word)
                                        target = [expected[p, t] for p, t in enumerate(word)]
                                        sample_error = max(
                                            sample_error,
                                            float(np.max(np.abs(confidence[b] - target))),
                                        )
                                        sample_checks += 1
                                    assert (
                                        np.isfinite(confidence).all() and sample_error <= tolerance
                                    )
                                    records.append(
                                        dict(
                                            case=case,
                                            representation=representation,
                                            depth=depth,
                                            clamp=clamp,
                                            device=device,
                                            kind=kind,
                                            mode=mode,
                                            status="pass",
                                            **graph_stats,
                                            max_absolute_marginal_error=error,
                                            max_absolute_sampled_confidence_error=sample_error,
                                            absolute_tolerance=tolerance,
                                        )
                                    )
    finally:
        torch.set_float32_matmul_precision(before)
    return dict(
        scope="small language and floating-point oracle; no neural heads or speed gate",
        mosaic=origin,
        python=platform.python_version(),
        torch=torch.__version__,
        cuda=torch.version.cuda,
        gpu=torch.cuda.get_device_name() if "cuda" in devices else None,
        import_precision_restored=True,
        native_kernel_matmul_precision="high",
        language_checks=language_checks,
        original_id_marginal_checks=marginal_checks,
        valid_sample_checks=sample_checks,
        diagnostic_wall_seconds=monotonic() - started,
        records=records,
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
    print(json.dumps({k: v for k, v in result.items() if k not in ("records", "mosaic")}))


if __name__ == "__main__":
    main()
