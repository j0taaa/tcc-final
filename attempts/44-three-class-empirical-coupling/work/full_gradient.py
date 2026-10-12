"""Opt-in small full-parameter falsification audit; no training/performance win."""

import argparse
import hashlib
import json
import platform
import subprocess
from fractions import Fraction
from itertools import permutations
from pathlib import Path
from random import Random
from time import perf_counter, process_time

import numpy as np
import torch
from transformers import AutoTokenizer

from .count_source import CountSource
from .mdlm_loader import load_cpu_model
from .noise_features import classify, features, fit_proxy, roles
from .oracle import joint

HERE = Path(__file__).parent
CHUNK = 1_000_000


def geometry(sums, counts, squared, observations, h_variance):
    gram, rss_norm, cv_norm = np.zeros((3, 3)), 0.0, 0.0
    for array in sums:
        for lo in range(0, array.shape[1], CHUNK):
            block = array[:, lo : lo + CHUNK]
            means = block[:3] / torch.tensor(np.maximum(counts, 1))[:, None]
            gram += (means @ means.T).numpy()
            rss_norm += block[3].square().sum().item()
            cv_norm += block[4].square().sum().item()
    p = counts / observations
    variance = squared / observations - p @ gram @ p
    between = np.sum(p * np.diag(gram)) - p @ gram @ p
    probabilities = tuple(Fraction(int(c), observations) for c in counts)
    methods = {"iid2": variance / 2, "continuous_rss": (variance - rss_norm) / 2}
    methods["oracle_scalar_cv"] = (
        (variance - cv_norm / h_variance) / 2 if h_variance else variance / 2
    )
    for budget in (4, 32):
        j = np.array(joint(probabilities, budget), dtype=float)
        methods[f"class_c{budget}"] = (variance + np.sum((j - np.outer(p, p)) * gram)) / 2
    rss = []
    for order in permutations(range(3)):
        d = np.zeros(3)
        for position, i in enumerate(order):
            d[i] = p[i] * (
                sum(p[j] for j in order[position + 1 :]) - sum(p[j] for j in order[:position])
            )
        rss.append(float((variance - d @ gram @ d) / 2))
    methods["best_three_class_rss"] = min(rss)
    diagonal = [max(Fraction(0), 2 * q - 1) for q in probabilities]
    ideal = np.array(
        [
            [
                diagonal[i]
                if i == j
                else (
                    probabilities[i]
                    + probabilities[j]
                    - probabilities[3 - i - j]
                    - diagonal[i]
                    - diagonal[j]
                    + diagonal[3 - i - j]
                )
                / 2
                for j in range(3)
            ]
            for i in range(3)
        ],
        dtype=float,
    )
    methods["known_bank_mass_inverse"] = (variance + np.sum((ideal - np.outer(p, p)) * gram)) / 2
    return dict(
        source_observations=observations,
        class_counts=counts.tolist(),
        class_mean_gram=gram.tolist(),
        full_gradient_trace=variance,
        between_fraction=float(between / variance),
        pair_trace={k: float(v) for k, v in methods.items()},
        class_c32_fraction_below={
            k: float(1 - methods["class_c32"] / v) for k, v in methods.items() if v
        },
        screen_pass=all(
            methods["class_c32"] <= 0.8 * methods[k] for k in ("continuous_rss", "oracle_scalar_cv")
        ),
        scope=(
            "DESCRIPTIVE complete known empirical law WITH replacement; "
            "no population/training/runtime guarantee."
        ),
    )


def run(output, cache):
    if output.exists():
        raise ValueError("Refuse to overwrite observations")
    if subprocess.check_output(["git", "status", "--porcelain"]).strip():
        raise ValueError("Freeze sources and protocol before model observations")
    protocol = json.loads((HERE / "feasibility-protocol-v3.json").read_text())
    config = json.loads((HERE / protocol["model_config"]).read_text())
    documents = json.loads((HERE / protocol["documents"]).read_text())
    teacher = json.loads((HERE / "teacher-fit-v3.json").read_text())
    output.mkdir(parents=True)
    metadata = dict(
        source_commit=subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
        files={
            p.name: hashlib.sha256(p.read_bytes()).hexdigest()
            for p in HERE.iterdir()
            if p.suffix in (".py", ".json")
        },
        python=platform.python_version(),
        torch=torch.__version__,
        protocol=protocol,
        calls=0,
        completed_documents=0,
        status="RUNNING",
        model_updates=0,
    )

    def save():
        (output / "metadata.json").write_text(json.dumps(metadata, indent=2) + "\n")

    save()
    try:
        torch.set_num_threads(protocol["threads"])
        torch.manual_seed(protocol["seed"])
        begin, cpu = perf_counter(), process_time()
        tokenizer = AutoTokenizer.from_pretrained(
            config["tokenizer_id"],
            revision=config["tokenizer_revision"],
            cache_dir=str(cache),
            local_files_only=True,
        )
        model, hashes, adapter = load_cpu_model(config, cache)
        assert not model.config.time_conditioning
        parameters = list(model.named_parameters())
        metadata.update(
            checkpoint_hashes=hashes,
            adapter_sha256=adapter,
            parameters=sum(p.numel() for _, p in parameters),
            load_wall=perf_counter() - begin,
            load_cpu=process_time() - cpu,
        )
        save()
        rng = Random(protocol["seed"])
        with (output / "rows.jsonl").open("x") as stream:
            for document in documents:
                json.loads(document["text"])
                encoded = tokenizer(
                    document["text"], add_special_tokens=False, return_offsets_mapping=True
                )
                assert encoded["input_ids"] == document["tokens"]
                role = roles(document["text"], encoded["offset_mapping"])
                original = torch.tensor([document["tokens"]])
                source = CountSource(original.shape[1])
                past = [r for r in teacher if r["document"] == document["key"]]
                assert len(past) == 32
                masks = [np.isin(np.arange(source.n), r["mask"]) for r in past]
                target = np.array([[r["score"], *r["projections"]] for r in past])
                beta, centers = fit_proxy(np.array([features(m, role) for m in masks]), target)
                addresses = [
                    rng.randrange(source.size) for _ in range(protocol["evaluations_per_document"])
                ]
                masks = [source.decode(a) for a in addresses]
                xs = np.array([features(m, role) for m in masks])
                labels, h = classify(xs[:, None, :], beta, centers), (xs @ beta)[:, 0]
                n, counts = len(masks), np.bincount(labels, minlength=3)
                rank_weights = np.array([(np.sum(h > v) - np.sum(h < v)) / n**2 for v in h])
                cv_weights = (h - h.mean()) / n
                sums = [torch.zeros((5, p.numel()), dtype=torch.float64) for _, p in parameters]
                normsum, bias_errors, unused = 0.0, [], set()
                for index, (address, mask, label) in enumerate(
                    zip(addresses, masks, labels, strict=True)
                ):
                    model.zero_grad(set_to_none=True)
                    ids = original.clone()
                    ids[0, mask] = config["mask_token_id"]
                    tick, cp = perf_counter(), process_time()
                    logits = model(input_ids=ids, timesteps=torch.ones(1), return_dict=False)[
                        0, mask
                    ].double()
                    logits[:, config["mask_token_id"]] = -torch.inf
                    logq = logits.log_softmax(-1)
                    targets = original[0, mask]
                    loss = -logq.gather(1, targets[:, None]).mean()
                    metadata["calls"] += 1
                    if not torch.isfinite(loss):
                        raise ValueError("Nonfinite original loss")
                    loss.backward()
                    neural_wall, neural_cpu = perf_counter() - tick, process_time() - cp
                    expected = logq.detach().exp().mean(0)
                    expected.scatter_add_(
                        0,
                        targets,
                        torch.full((len(targets),), -1 / len(targets), dtype=torch.float64),
                    )
                    actual = model.backbone.output_layer.linear.bias.grad.double()
                    torch.testing.assert_close(actual, expected, atol=5e-6, rtol=2e-4)
                    bias_errors.append((actual - expected).abs().max().item())
                    tick, cp, squared = perf_counter(), process_time(), 0.0
                    for (name, parameter), accum in zip(parameters, sums, strict=True):
                        if parameter.grad is None:
                            unused.add(name)
                            continue
                        flat = parameter.grad.flatten()
                        for lo in range(0, flat.numel(), CHUNK):
                            gradient = flat[lo : lo + CHUNK].double()
                            if not torch.isfinite(gradient).all():
                                raise ValueError(f"Nonfinite gradient: {name}")
                            squared += gradient.square().sum().item()
                            accum[label, lo : lo + CHUNK].add_(gradient)
                            accum[3, lo : lo + CHUNK].add_(gradient, alpha=rank_weights[index])
                            accum[4, lo : lo + CHUNK].add_(gradient, alpha=cv_weights[index])
                    normsum += squared
                    row = dict(
                        document=document["key"],
                        index=index,
                        address=str(address),
                        mask=np.flatnonzero(mask).tolist(),
                        label=int(label),
                        score=loss.item(),
                        proxy=float(h[index]),
                        gradient_squared_norm=squared,
                        neural_wall=neural_wall,
                        neural_cpu=neural_cpu,
                        statistics_wall=perf_counter() - tick,
                        statistics_cpu=process_time() - cp,
                        bias_max_abs_error=bias_errors[-1],
                    )
                    stream.write(json.dumps(row) + "\n")
                    stream.flush()
                    save()
                report = geometry(sums, counts, normsum, n, float(np.var(h)))
                report.update(
                    document=document,
                    unused_gradient_parameters=sorted(unused),
                    max_bias_error=max(bias_errors),
                )
                (output / f"{document['key']}.json").write_text(json.dumps(report, indent=2) + "\n")
                metadata["completed_documents"] += 1
                save()
                print(
                    json.dumps(
                        {
                            "document": document["key"][:12],
                            "between": report["between_fraction"],
                            "reductions": report["class_c32_fraction_below"],
                            "screen": report["screen_pass"],
                        }
                    ),
                    flush=True,
                )
                del sums
        metadata["status"] = "COMPLETE"
        save()
    except BaseException as error:
        metadata.update(status="ERROR", error=repr(error))
        save()
        raise


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--cache", type=Path, required=True)
    args = parser.parse_args()
    run(args.output, args.cache)
