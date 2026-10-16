"""Opt-in sparse-FA numerical oracle against independent original-word JSON."""

import argparse
import hashlib
import json
import platform
import warnings
from fractions import Fraction
from pathlib import Path

import numpy as np
import torch

from .layered_fa_control import LayeredFA
from .sparse_fa_control import SparseFA
from .termination import prepare_graph, terminated_graph
from .test_termination import LIMITS, enumerate_terminated, examples, fixture


def run(devices, backend="sparse"):
    records, checks, samples = [], 0, 0
    torch.set_num_threads(1)
    with warnings.catch_warnings(record=True) as observed_warnings:
        warnings.simplefilter("always")
        for case, (words, canvas, eot, pad) in enumerate(examples()):
            rows = [
                [1 + (case + p + 3 * t) % 5 for t in range(len(words))] for p in range(len(canvas))
            ]
            table, _ = fixture(words, rows, canvas, eot, pad)
            for depth in (0, 1, None):
                graph = terminated_graph(table, canvas, depth, eot, pad, symbolic=True, **LIMITS)
                caches = {}
                prepared = None
                for update in (False, True):
                    current = canvas
                    new_rows = [
                        [v + (p % 2) if update else v for v in row] for p, row in enumerate(rows)
                    ]
                    _, weights = fixture(words, new_rows, current, eot, pad)
                    law = enumerate_terminated(words, weights, eot, pad, depth)
                    if not law:
                        records.append(
                            dict(case=case, depth=depth, update=update, status="zero_mass")
                        )
                        continue
                    if update:
                        witness = next(iter(law))
                        first_free = next(p for p, t in enumerate(current) if t is None)
                        current = tuple(
                            witness[p] if p == first_free else t for p, t in enumerate(current)
                        )
                        _, weights = fixture(words, new_rows, current, eot, pad)
                        law = enumerate_terminated(words, weights, eot, pad, depth)
                    mass = sum(law.values(), Fraction())
                    expected = np.array(
                        [
                            [
                                float(
                                    sum((v for w, v in law.items() if w[p] == t), Fraction()) / mass
                                )
                                for t in range(len(words))
                            ]
                            for p in range(len(canvas))
                        ]
                    )
                    for device in devices:
                        for mode, dtype, tolerance in (
                            ("fp32", torch.float32, 0.005),
                            ("fp64", torch.float64, 1e-10),
                        ):
                            key = device, mode
                            if key not in caches:
                                if backend == "layered":
                                    if prepared is None:
                                        prepared = prepare_graph(graph, table, canvas, **LIMITS)
                                    caches[key] = LayeredFA(prepared, device=device, dtype=dtype)
                                else:
                                    caches[key] = SparseFA(graph, table, device=device, dtype=dtype)
                            sampler = caches[key]
                            torch.manual_seed(2026101624)
                            actual = sampler.query(new_rows, current, return_all_marginals=True)
                            marginals = actual["marginals"].cpu().numpy()
                            error = float(np.max(np.abs(marginals - expected)))
                            assert np.isfinite(marginals).all() and error <= tolerance, (
                                case,
                                depth,
                                update,
                                device,
                                mode,
                                error,
                            )
                            checks += marginals.size
                            word = tuple(actual["tokens"].cpu().tolist())
                            assert word in law, (case, depth, device, mode, word)
                            target = [expected[p, t] for p, t in enumerate(word)]
                            conf = actual["confidence"].cpu().numpy()
                            conf_error = float(np.max(np.abs(conf - target)))
                            assert np.isfinite(conf).all() and conf_error <= tolerance
                            samples += 1
                            records.append(
                                dict(
                                    case=case,
                                    depth=depth,
                                    update=update,
                                    device=device,
                                    mode=mode,
                                    status="pass",
                                    **sampler.stats,
                                    max_absolute_marginal_error=error,
                                    max_absolute_sampled_confidence_error=conf_error,
                                    absolute_tolerance=tolerance,
                                )
                            )
    return dict(
        scope="independent classical sparse-FA control, no native Mosaic execution or model heads",
        backend=backend,
        torch=torch.__version__,
        cuda=torch.version.cuda,
        python=platform.python_version(),
        gpu=torch.cuda.get_device_name() if "cuda" in devices else None,
        original_id_marginal_checks=checks,
        valid_sample_checks=samples,
        python_warnings=sorted({str(w.message) for w in observed_warnings}),
        records=records,
        own_source_sha256={
            p.name: hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(Path(__file__).parent.glob("*.py"))
        },
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--devices", nargs="+", default=["cpu", "cuda"])
    parser.add_argument("--backend", choices=["sparse", "layered"], default="sparse")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = run(args.devices, args.backend)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(
        json.dumps({k: v for k, v in result.items() if k not in ("records", "own_source_sha256")})
    )


if __name__ == "__main__":
    main()
