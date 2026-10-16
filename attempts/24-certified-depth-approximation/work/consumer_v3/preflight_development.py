"""Opt-in complete-operation correctness before ANY development timings."""

import argparse
import hashlib
import itertools
import json
from fractions import Fraction
from pathlib import Path

import numpy as np
import torch

from ..consumer_v2.block_stats import Partition
from .development_methods import CPUQuery, SparseQuery
from .termination import surrogate_table


def run():
    torch.set_num_threads(1)
    words = [None] * 50258
    words[:5] = [b"0", b"0", b"[]", b"[[]]", b" "]
    eot, canvas = 50256, (None,) * 5 + (50256,)
    table = surrogate_table(words, eot, eot)
    partition = Partition(tuple(table.class_of), len(table.classes), 1024)
    probabilities = np.zeros((len(canvas), len(words)), dtype=np.float64)
    for p in range(len(canvas)):
        probabilities[p, [0, 1, 2, 3, 4, eot]] = [1, 2, 1, 2**-20, 1 + p % 2, 2]
        probabilities[p] /= probabilities[p].sum()
    law = {}
    supported = [0, 1, 2, 3, 4, eot]
    denominators = [
        sum((Fraction(float(v)) for v in row if v), Fraction()) for row in probabilities
    ]
    for prefix in itertools.product(supported, repeat=5):
        word = (*prefix, eot)
        k = word.index(eot)
        if any(t != eot for t in word[k + 1 :]):
            continue
        try:
            json.loads(b"".join(words[t] for t in word[:k]).decode("utf8"))
        except (ValueError, UnicodeDecodeError):
            continue
        mass = Fraction(1)
        for p in range(5):
            mass *= Fraction(float(probabilities[p, word[p]])) / denominators[p]
        law[word] = mass
    total = sum(law.values(), Fraction())
    assert total > 0 and len(law) > 1
    protocol = json.loads(
        (Path(__file__).resolve().parents[1] / "consumer-v4-development-protocol.json").read_text()
    )
    gpu = torch.from_numpy(probabilities).cuda()
    records = []
    for method in (
        "handoff_cpu",
        "closed_cpu",
        "exact_stack_cpu",
        "sparse_fa_fp32",
        "sparse_fa_fp64",
        "layered_fa_fp32",
        "layered_fa_fp64",
    ):
        query = (
            CPUQuery(method, table, partition, canvas, protocol)
            if method.endswith("cpu")
            else SparseQuery(method, table, canvas, protocol)
        )
        previous = None
        for label in ("cold", "warm"):
            torch.manual_seed(protocol["seed"])
            result = query.query(gpu, protocol["seed"])
            torch.cuda.synchronize()
            word = tuple(result["tokens"].cpu().tolist())
            assert word in law and word[-1] == eot
            expected = [
                float(sum((v for w, v in law.items() if w[p] == t), Fraction()) / total)
                for p, t in enumerate(word)
            ]
            confidence = result["confidence"].cpu().numpy()
            error = float(np.max(np.abs(confidence - expected)))
            allowed = (0.005 if method.endswith("fp32") else 1e-8) + float(
                result["confidence_delta"]
            )
            assert np.isfinite(confidence).all() and error <= allowed, (method, error, allowed)
            exact = {
                p: sum((v for w, v in law.items() if w[p] == word[p]), Fraction()) / total
                for p in range(5)
            }
            exact_set = set(sorted(exact, key=lambda p: (-exact[p], p))[:4])
            actual_set = set(result["commit_mask"].nonzero().flatten().cpu().tolist())
            if result["exact_common_ranking"]:
                assert actual_set == exact_set, (method, actual_set, exact_set)
            signature = word, tuple(sorted(actual_set)), str(result["draw_delta"])
            if previous is not None:
                assert signature == previous, (method, previous, signature)
            previous = signature
            records.append(
                dict(
                    method=method,
                    phase=label,
                    status="pass",
                    sample=word,
                    max_absolute_confidence_error=error,
                    confidence_tolerance=allowed,
                    exact_rank_set_matches=actual_set == exact_set,
                    draw_delta=str(result["draw_delta"]),
                    draw_depth=result["draw_depth"],
                    confidence_delta=str(result["confidence_delta"]),
                    confidence_depth=result["confidence_depth"],
                )
            )
    return dict(
        scope="synthetic tiny-support 50258-ID API correctness only; no neural or timing gate",
        torch=torch.__version__,
        gpu=torch.cuda.get_device_name(),
        valid_original_words=len(law),
        exact_full_mass=str(total),
        records=records,
        source_sha256={
            p.name: hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(Path(__file__).parent.glob("*.py"))
        },
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = run()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({k: v for k, v in result.items() if k not in ("records", "source_sha256")}))


if __name__ == "__main__":
    main()
