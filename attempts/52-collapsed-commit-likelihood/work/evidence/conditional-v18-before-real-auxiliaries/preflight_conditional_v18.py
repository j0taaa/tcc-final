"""V18 synthetic full-V M8 conditional resource checks; zero pretrained heads."""

import argparse
import json
import random
import resource
from pathlib import Path

import numpy as np

from .conditional_floating import ConditionalFloatSampler
from .consumer_resource import bounded, serial, write_json
from .llada_suffix_v10 import NumericSuffixJSON, full_text
from .llada_tokenizer_v10 import EOS, VOCABULARY, emissions, verify_files
from .prefix_floating import PrefixFloatPlan, PrefixPlanner
from .prefix_runtime import assemble


def run(model_dir, output):
    from tokenizers import Tokenizer

    output.mkdir(parents=True, exist_ok=False)
    verify_files(model_dir)
    tokenizer = Tokenizer.from_file(str(model_dir / "tokenizer.json"))
    original = emissions(model_dir)
    grammar = NumericSuffixJSON(original, EOS, EOS)
    plan = PrefixFloatPlan(grammar)
    ids = {b: i for i, b in enumerate(original) if b in (b"0", b"1", b"}")}
    assert set(ids) == {b"0", b"1", b"}"}
    private = np.random.default_rng(52180)
    weights = private.uniform(0.25, 1.25, (64, VOCABULARY))
    weights /= weights.sum(1, keepdims=True)
    global_python, global_numpy = random.getstate(), np.random.get_state()
    records = []
    configs = (
        (64, {}, {0: ids[b"0"], 62: ids[b"}"], 63: EOS}),
        (64, {0: ids[b"1"], 40: 126349, 63: EOS}, {62: ids[b"}"]}),
        (4, {0: ids[b"1"], 3: EOS}, {1: 126349, 2: ids[b"}"]}),
    )
    for index, (n, fixed, retained) in enumerate(configs):
        with bounded(60):
            active = [i for i in range(n) if i not in fixed]
            rows = assemble(weights[active], active, fixed, n, VOCABULARY)
            planner = PrefixPlanner(plan, rows, fixed, 0.0)
            action = tuple(sorted(retained.items()))
            sampler = ConditionalFloatSampler(planner, action)
            for correlated in (False, True):
                draws = sampler.sample(8, random.Random(52180 + 2 * index + correlated), correlated)
                for word, anchor in draws:
                    text = full_text(grammar, word)
                    decoded = tokenizer.decode(
                        [12657, 31113, 2275, *word[:-1]], skip_special_tokens=False
                    )
                    if decoded != text:
                        raise AssertionError("independent original tokenizer differs")
                    if any(i >= len(word) or word[i] != v for i, v in (*fixed.items(), *action)):
                        raise AssertionError("sampled proposal changed fixed/retained original ID")
                    scores = planner.controls(word, anchor, action, sampler.statistics)
                    if not all(np.isfinite(v).all() for s in scores.values() for v in s.values()):
                        raise AssertionError("nonfinite conditional control score")
                    records.append(
                        {
                            "case": index,
                            "correlated": correlated,
                            "word": word,
                            "anchor": anchor,
                            "json": text,
                            "score_methods": sorted(scores),
                        }
                    )
            if resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * 1024 > 2 * 1024**3:
                raise ValueError("synthetic CPU peak RSS exceeds2GiB")
    assert random.getstate() == global_python
    after = np.random.get_state()
    assert after[0] == global_numpy[0] and after[2:] == global_numpy[2:]
    np.testing.assert_array_equal(after[1], global_numpy[1])
    write_json(output / "SYNTHETIC-records.json", serial(records))
    report = {
        "status": "PASS",
        "SYNTHETIC_full_V_words": len(records),
        "pretrained_heads": 0,
        "model_forwards": 0,
        "real_old_head_auxiliary_draws": 0,
        "vocabulary": VOCABULARY,
        "classes": plan.class_count,
        "peak_CPU_process_RSS_bytes": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * 1024,
        "global_Python_NumPy_RNG_unchanged": True,
        "CUDA_used": False,
        "updates": 0,
    }
    write_json(output / "summary.json", report)
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--model-dir", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    a = ap.parse_args()
    run(a.model_dir, a.output)
