"""AFTER-data scalar score and independently reconstructed moment audit."""

import argparse
import json
import math
from decimal import Decimal
from pathlib import Path

import numpy as np

from .conditional_audit_v17 import actor_scalar
from .consumer_resource import write_json
from .llada_suffix_v10 import NumericSuffixJSON
from .llada_tokenizer_v10 import EOS, emissions
from .prefix_floating import PrefixFloatPlan

METHODS = (
    "full_triple",
    "anchor_integrated",
    "class_integrated",
    "length_integrated",
    "combined_partial",
    "known_anchor",
    "collapsed",
)
BLOCKS = {
    "total": slice(0, 9),
    "gate": slice(0, 5),
    "anchor": slice(5, 8),
    "confidence": slice(8, 9),
}


def run(capture, analysis, auxiliary, tables, features_path, model_dir):
    from tokenizers import Tokenizer

    tokenizer = Tokenizer.from_file(str(model_dir / "tokenizer.json"))
    plan = PrefixFloatPlan(NumericSuffixJSON(emissions(model_dir), EOS, EOS))
    rows = [json.loads(s) for s in (capture / "rows.jsonl").read_text().splitlines()]
    records = [json.loads(s) for s in (auxiliary / "records.jsonl").read_text().splitlines()]
    preps = json.loads((auxiliary / "preparations.json").read_text())
    features = [json.loads(s) for s in features_path.read_text().splitlines()]
    labels = json.loads((analysis / "known-labels-provenance.json").read_text())["labels"]
    report = json.loads((auxiliary / "summary.json").read_text())
    assert len(records) == 8960 and report["status"] == "PASS"
    assert (
        report["new_model_forwards"] == report["new_decoder_trajectories"] == report["updates"] == 0
    )
    assert report["global_Python_NumPy_RNG_unchanged"] and not report["CUDA_used"]
    assert report["peak_CPU_process_RSS_bytes"] <= 2 * 1024**3
    groups = {}
    for r in records:
        groups.setdefault((r["case"], r["replica"], r["step"]), []).append(r)
    maximum, checked, verified, ordinal = 0.0, 0, 0, 0

    def compare(a, b):
        nonlocal maximum, checked
        a, b = np.asarray(a), np.asarray(b)
        assert a.shape == b.shape and np.isfinite(a).all() and np.isfinite(b).all()
        error = float(np.max(np.abs(a - b)))
        maximum, checked = max(maximum, error), checked + a.size
        assert error < 5e-11, error

    score = np.zeros((2, 16, 64, 7, 9))
    baseline = np.zeros((2, 16, 64, 7, 4, 9))
    sem_full, sem_anchor = np.zeros((2, 16, 64, 9)), np.zeros((2, 16, 64, 9))
    regular, rewards = np.zeros((16, 9)), np.zeros(16)
    for row in rows:
        path = 2 * row["case"] + row["replica"]
        for t in row["transitions"]:
            fixed, retained = dict(t["fixed_before"]), dict(t["action"])
            extent = t["prefix_extent"]
            prep, f = preps[ordinal], features[ordinal]
            compare(prep["C_regular_actor"], f["controls"][0])
            compare(prep["baselines"], f["baselines"])
            assert (prep["case"], prep["replica"], prep["step"]) == (
                row["case"],
                row["replica"],
                t["step"],
            )
            with np.load(capture / "heads" / (t["head"] + ".npz")) as packet:
                bits, positions = packet["logits_bf16"], packet["positions"].tolist()
            logits = (bits.astype(np.uint32) << 16).view(np.float32).astype(np.float64)
            logits -= logits.max(axis=1, keepdims=True)
            logden = np.log(np.exp(logits).sum(axis=1))
            logc = logits - logden[:, None]
            probabilities = np.exp(logc)
            lookup = {i: j for j, i in enumerate(positions)}
            max_logs = {i: -float(logden[j]) for i, j in lookup.items()}
            z = row["root_feature"] + logc - math.log(0.01)
            gates = np.exp(-np.logaddexp(0.0, -z))
            terms = {i: 1 / gates[lookup[i], v] for i, v in retained.items()}
            rho = {i: v / sum(terms.values()) for i, v in terms.items()}
            # Independent sums over original IDs, not the planner's derivative arrays.
            unret = probabilities * (1 - gates)
            den = np.stack(
                [np.bincount(plan.mapping, weights=v, minlength=plan.class_count) for v in unret]
            )
            da = np.stack(
                [
                    np.bincount(plan.mapping, weights=v, minlength=plan.class_count)
                    for v in -unret * gates
                ]
            )
            db = np.stack(
                [
                    np.bincount(plan.mapping, weights=v, minlength=plan.class_count)
                    for v in -unret * gates * logc
                ]
            )
            collapsed = t["scores"]["collapsed"]
            rewards[path] = float(prep["old_final_reward"])
            pieces, i = [], 0
            while i in fixed and fixed[i] != EOS:
                pieces.append(plan.language.emissions[fixed[i]])
                i += 1
            try:
                parsed = json.loads(
                    '{"answer":' + b"".join(pieces).decode(), parse_int=Decimal, parse_float=Decimal
                )
                certificate = set(parsed) == {"answer"} and isinstance(parsed["answer"], Decimal)
            except (ValueError, UnicodeError):
                certificate = False
            assert certificate == prep["tail_certificate"]
            if certificate:
                assert (parsed["answer"] == Decimal(labels[row["case"]]["answer"])) == bool(
                    rewards[path]
                )
            else:
                regular[path] += prep["C_regular_actor"]
            subset = groups[row["case"], row["replica"], t["step"]]
            assert len(subset) == 128
            seen = set()
            for record in subset:
                word, anchor = record["word"], record["anchor"]
                mode = ("iid", "prefix_stratified").index(record["method"])
                index = record["draw_index"]
                assert (mode, index) not in seen and 0 <= index < 64
                seen.add((mode, index))
                assert record["status"] == "PASS" and record["head"] == t["head"]
                assert word[-1] == EOS and EOS not in word[:-1]
                assert anchor in retained and all(
                    word[i] == v for i, v in (*fixed.items(), *retained.items())
                )
                text = tokenizer.decode([12657, 31113, 2275, *word[:-1]], skip_special_tokens=False)
                assert text == record["json"]
                parsed_word = json.loads(text, parse_int=Decimal, parse_float=Decimal)
                assert set(parsed_word) == {"answer"}
                semantic = parsed_word["answer"] == Decimal(labels[row["case"]]["answer"])
                assert (
                    semantic == record["semantic_correct_proposal"]
                    and record["secondary_Decimal_representable"]
                )
                active = [i for i in range(len(word)) if i not in fixed]
                values = {}
                for name in METHODS:
                    if name == "collapsed":
                        values[name] = actor_scalar(collapsed, extent, fixed, max_logs)
                        continue
                    aa, rr, bb = [0.0] * 64, [0.0] * 64, 0.0
                    if name == "known_anchor":
                        aa = list(collapsed["alpha"][:64])
                        aa += [0.0] * (64 - len(aa))
                        bb = collapsed["beta"]
                        for i, v in retained.items():
                            delta = (rho[i] - int(i == anchor)) * (1 - gates[lookup[i], v])
                            aa[i] += delta
                            bb += delta * logc[lookup[i], v]
                        for i in range(extent):
                            rr[i] = collapsed["anchor"][i] + int(i == anchor) - rho.get(i, 0.0)
                    else:
                        for i in active:
                            j, v = lookup[i], word[i]
                            factor = int(i in retained) - gates[j, v]
                            if name == "full_triple":
                                aa[i] = int(i != anchor) * factor
                                bb += aa[i] * logc[j, v]
                            elif name in ("anchor_integrated", "length_integrated"):
                                aa[i] = (1 - rho.get(i, 0.0)) * factor
                                bb += aa[i] * logc[j, v]
                            elif i in retained:
                                aa[i] = (1 - rho[i]) * factor
                                bb += aa[i] * logc[j, v]
                            else:
                                cls = plan.mapping[v]
                                aa[i] = da[j, cls] / den[j, cls]
                                bb += db[j, cls] / den[j, cls]
                            rr[i] = (
                                int(i == anchor) if name == "full_triple" else rho.get(i, 0.0)
                            ) - 1 / len(active)
                        if name in ("length_integrated", "combined_partial"):
                            rr = list(collapsed["anchor"][:64])
                            rr += [0.0] * (64 - len(rr))
                    values[name] = actor_scalar(
                        {"alpha": aa, "anchor": rr, "beta": bb}, extent, fixed, max_logs
                    )
                for name in METHODS:
                    compare(values[name], record["actor_scores"][name])
                if not certificate:
                    v = np.asarray([values[m] for m in METHODS])
                    score[mode, path, index] += v
                    baseline[mode, path, index] += (
                        np.asarray(prep["baselines"])[None, :, None] * v[:, None, :]
                    )
                    sem_full[mode, path, index] += semantic * v[0]
                    sem_anchor[mode, path, index] += semantic * v[1]
                verified += 1
            ordinal += 1
    with np.load(tables / "path-sufficient-statistics.npz") as saved:
        for name, value in (
            ("score", score),
            ("baseline", baseline),
            ("semantic_full", sem_full),
            ("semantic_anchor", sem_anchor),
            ("regular", regular),
            ("rewards", rewards),
        ):
            compare(value, saved[name])
    table = json.loads((tables / "ALL2268-estimates.json").read_text())
    assert len(table) == 2268
    for entry in table:
        m = METHODS.index(entry["method"])
        b = ("zero", "half", "proxy_state", "proxy_root").index(entry["baseline"])
        a, c, d = entry["coefficients"]
        g = (
            rewards[None, :, None, None] * score[:, :, :, m]
            - baseline[:, :, :, m, b]
            - a * regular[None, :, None, :]
            - c * sem_full
            - d * sem_anchor
        )
        total = dict.fromkeys(BLOCKS, 0.0)
        for q in range(8):
            x, y = g[0, 2 * q], g[0, 2 * q + 1]
            n = len(x)
            # All distinct ordered inner products, an independent U-statistic formula.
            u = 0.5 * ((x.sum(0) ** 2 - (x * x).sum(0)) + (y.sum(0) ** 2 - (y * y).sum(0))) / (
                n * (n - 1)
            ) - x.mean(0) * y.mean(0)
            if entry["variant"] == "prefix_stratified8":
                x, y = (
                    g[1, 2 * q].reshape(8, 8, 9).mean(1),
                    g[1, 2 * q + 1].reshape(8, 8, 9).mean(1),
                )
                scale = 1
            else:
                scale = 1 if entry["variant"] == "iid1" else 8
            hidden = (
                (x * x).sum(0) - x.sum(0) ** 2 / len(x) + (y * y).sum(0) - y.sum(0) ** 2 / len(y)
            ) / (2 * (len(x) - 1) * scale)
            for block, s in BLOCKS.items():
                total[block] += float((u + hidden)[s].sum()) / 64
        for block in BLOCKS:
            compare(total[block], entry["actor_blocks"][block])
        compare(total["total"], entry["estimate"])
    summary = json.loads((tables / "summary.json").read_text())
    for family, candidates, controls in (
        (
            "family_A",
            [e for e in table if e["variant"] == "iid1" and e["method"] == "collapsed"],
            [e for e in table if e["variant"] == "iid1" and e["method"] != "collapsed"],
        ),
        (
            "family_B",
            [e for e in table if e["variant"] == "prefix_stratified8"],
            [e for e in table if e["variant"] == "iid1"],
        ),
    ):
        minimum, control = (
            min(e["estimate"] for e in candidates),
            min(e["estimate"] for e in controls),
        )
        compare(minimum, summary[family]["selected"]["estimate"])
        compare(minimum / control, summary[family]["ratio_to_best_control"])
        assert all(e["estimate"] > 0 for e in controls)
        assert minimum / control > 0.8 and summary[family]["status"] == "NECESSITY_NEGATIVE"
    rloo = json.loads((tables / "RLOO-conditional-noise-NOT-total-variance.json").read_text())
    assert len(rloo) == 189 and all(e["full_unconditional_variance"] is None for e in rloo)
    result = {
        "status": "PASS",
        "scope": "AFTER-data consistency; not independent population evaluation",
        "states": ordinal,
        "words_official_tokenizer_Decimal": verified,
        "all_seven_actor_coordinate_and_moment_checks": checked,
        "all_table_entries": len(table),
        "maximum_absolute_difference": maximum,
        "new_model_forwards": 0,
        "new_auxiliary_words": 0,
        "updates": 0,
    }
    write_json(tables / "post-capture-independent-audit.json", result)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    for name in ("capture", "analysis", "auxiliary", "tables", "features-path", "model-dir"):
        p.add_argument("--" + name, type=Path, required=True)
    a = p.parse_args()
    run(a.capture, a.analysis, a.auxiliary, a.tables, a.features_path, a.model_dir)
