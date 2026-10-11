"""Opt-in full-vocabulary noising information audit, NOT a performance gate."""

import argparse
import hashlib
import json
import platform
import subprocess
from pathlib import Path
from random import Random
from time import perf_counter, process_time

import numpy as np
import torch
from transformers import AutoTokenizer

from .mdlm_loader import load_cpu_model
from .noise_features import classify, corruption, features, fit_proxy, roles

WORK = Path(__file__).resolve().parent
ROOT = WORK.parents[2]


def bank_geometry(values, labels):
    """Exact joint-law trace on the OBSERVED known finite bank, numerical scores."""
    values = np.atleast_2d(values)
    if values.shape[0] == 1:
        values = values.T
    m = len(values)
    mu = values.mean(axis=0)
    variance = np.mean(np.sum((values - mu) ** 2, axis=1))
    groups = [values[labels == c] for c in sorted(set(labels))]
    n = np.array([len(g) for g in groups])
    means = np.array([g.mean(axis=0) - mu for g in groups])
    within = [np.mean(np.sum((g - g.mean(axis=0)) ** 2, axis=1)) for g in groups]
    denominator = m * (m - 1) * (m - 2) * (m - 3)
    squared = np.sum(means**2, axis=1)
    covariance = (
        -(m * m - n @ n) * (n**2 @ squared)
        - np.sum((n**2 @ means) ** 2)
        + (4 * m - 6) * (n @ squared)
    ) / denominator
    for size, var in zip(n, within, strict=True):
        if size >= 2:
            diagonal = size * (size - 1) * (size - 2) * (2 * m - size - 3) / denominator
            covariance -= diagonal * var / (size - 1)
    return dict(
        variance=float(variance),
        class_sizes=n.tolist(),
        covariance=float(covariance),
        iid2_mean_variance=float(variance / 2),
        derangement_mean_variance=float(variance * (m - 2) / (2 * (m - 1))),
        c4_mean_variance=float((variance + covariance) / 2),
        c4_fraction_below_iid2=float(-covariance / variance) if variance else None,
        c4_fraction_below_derangement=(
            float(1 - (variance + covariance) / (variance * (m - 2) / (m - 1)))
            if variance
            else None
        ),
    )


def run(output, cache):
    if subprocess.check_output(["git", "status", "--porcelain"], cwd=ROOT).strip():
        raise ValueError("freeze producer/protocol before model outputs")
    protocol = json.loads((WORK / "information-protocol-v5.json").read_text())
    config = json.loads((WORK / protocol["model_config"]).read_text())
    output.mkdir(parents=True, exist_ok=False)
    metadata = dict(
        source_commit=subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
        ).strip(),
        protocol_sha256=hashlib.sha256(
            (WORK / "information-protocol-v5.json").read_bytes()
        ).hexdigest(),
        document_sha256=hashlib.sha256(
            (WORK / protocol["external_documents"]).read_bytes()
        ).hexdigest(),
        files={
            p.name: hashlib.sha256(p.read_bytes()).hexdigest()
            for p in (
                WORK / "noise_information.py",
                WORK / "noise_features.py",
                WORK / "mdlm_loader.py",
            )
        },
        scope=protocol["purpose"],
        python=platform.python_version(),
        torch=torch.__version__,
        threads=4,
        calls=0,
        completed=0,
    )
    torch.set_num_threads(4)
    torch.manual_seed(protocol["seed"])
    load_start, load_cpu = perf_counter(), process_time()
    tokenizer = AutoTokenizer.from_pretrained(
        config["tokenizer_id"],
        revision=config["tokenizer_revision"],
        cache_dir=str(cache),
        local_files_only=True,
    )
    model, hashes, adapted = load_cpu_model(config, cache)
    assert not model.config.time_conditioning
    for parameter in model.parameters():
        parameter.requires_grad_(False)
    metadata.update(
        checkpoint_hashes=hashes,
        adapter_sha256=adapted,
        load_wall=perf_counter() - load_start,
        load_cpu=process_time() - load_cpu,
        load_scope="Reported separately; excluded from per-document tally. No model-output cache.",
    )
    (output / "metadata.json").write_text(json.dumps(metadata, indent=2) + "\n")
    directions = np.random.default_rng(protocol["seed"]).choice(
        (-1.0, 1.0), (8, model.config.vocab_size)
    )
    source_rng = Random(protocol["seed"])
    with (output / "rows.jsonl").open("x") as stream:
        for document in json.loads((WORK / protocol["external_documents"]).read_text()):
            start, cpu = perf_counter(), process_time()
            json.loads(document["text"])
            encoded = tokenizer(
                document["text"], add_special_tokens=False, return_offsets_mapping=True
            )
            assert encoded["input_ids"] == document["tokens"]
            role = roles(document["text"], encoded["offset_mapping"])
            original = torch.tensor([document["tokens"]], dtype=torch.long)
            xs, scores, gradients = [], [], []
            beta = centers = None
            for index in range(protocol["fit"] + protocol["evaluate"]):
                if index == protocol["fit"]:
                    target = np.column_stack((scores, np.array(gradients) @ directions.T))
                    beta, centers = fit_proxy(np.array(xs), target)
                seed = source_rng.getrandbits(128)
                mask = corruption(seed, original.shape[1])
                x = features(mask, role)
                label = int(classify(x, beta, centers)) if beta is not None else None
                ids = original.clone()
                ids[0, mask] = config["mask_token_id"]
                tick, cp = perf_counter(), process_time()
                with torch.inference_mode():
                    logits = model(input_ids=ids, timesteps=torch.ones(1), return_dict=False)[
                        0, mask
                    ].double()
                    logits[:, config["mask_token_id"]] = -torch.inf
                    logq = logits.log_softmax(dim=-1)
                    targets = original[0, mask]
                    score = -logq.gather(1, targets[:, None]).mean().item()
                    gradient = logq.exp().mean(dim=0)
                    gradient.scatter_add_(
                        0,
                        targets,
                        torch.full((len(targets),), -1 / len(targets), dtype=torch.float64),
                    )
                wall, elapsed_cpu = perf_counter() - tick, process_time() - cp
                gradient = gradient.numpy()
                metadata["calls"] += 1
                row = dict(
                    document=document["key"],
                    phase="fit" if label is None else "evaluate",
                    index=index,
                    seed=str(seed),
                    mask=np.flatnonzero(mask).tolist(),
                    label=label,
                    score=score,
                    bias_squared_norm=float(gradient @ gradient),
                    projections=(directions @ gradient).tolist(),
                    wall=wall,
                    cpu=elapsed_cpu,
                )
                stream.write(json.dumps(row) + "\n")
                stream.flush()
                xs.append(x)
                scores.append(score)
                gradients.append(gradient)
            xeval = np.array(xs[protocol["fit"] :])
            labels = classify(xeval[:, None, :], beta, centers)
            values = np.array(gradients[protocol["fit"] :])
            report = dict(
                document=document,
                role_counts=[int(np.sum(role == c)) for c in range(4)],
                observations=protocol["evaluate"],
                score=bank_geometry(np.array(scores[protocol["fit"] :]), labels),
                bias=bank_geometry(values, labels),
                evaluation_score_gram=(values @ values.T).tolist(),
                score_values=scores[protocol["fit"] :],
                labels=labels.tolist(),
                wall=perf_counter() - start,
                cpu=process_time() - cpu,
                scope=(
                    "Known finite-bank geometry ONLY; all labels/masses available. "
                    "Not a practical/novelty/training gate."
                ),
            )
            (output / (document["key"] + ".json")).write_text(json.dumps(report, indent=2) + "\n")
            metadata["completed"] += 1
            (output / "metadata.json").write_text(json.dumps(metadata, indent=2) + "\n")
            print(
                document["key"][:12],
                report["score"]["c4_fraction_below_iid2"],
                report["bias"]["c4_fraction_below_iid2"],
                metadata["calls"],
                flush=True,
            )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--cache", type=Path, default=ROOT / ".cache/mdlm")
    args = parser.parse_args()
    run(args.output, args.cache)
