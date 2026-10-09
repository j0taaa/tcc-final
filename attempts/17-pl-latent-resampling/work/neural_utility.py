"""Frozen external-input output-head gradient efficiency audit (opt-in model).

No optimizer learning-curve or full-backbone gradient claim. Full-softmax PL
scores are represented isometrically by a small Gram matrix, not truncated to
support logits. Enumerated finite actions provide population variances.
"""

from __future__ import annotations

import argparse
import hashlib
import itertools
import json
import math
import subprocess
from fractions import Fraction as Q
from functools import partial
from pathlib import Path
from random import Random
from time import monotonic, perf_counter, process_time

import numpy as np
import torch
from replay import EnumeratedTarget
from resampling import (
    BaseRejection,
    Problem,
    SingleTilt,
    TangentMixture,
    decision_cache_statistics,
    select_order,
)
from scripts.exact_commit.mdlm_cpu import load_cpu_model
from scripts.exact_commit.run_cfg_posterior_audit import source_grammar
from stationary_control import proposed_move
from transformers import AutoTokenizer

from mwpc_exact.cfg_posterior import compile_cfg_sampler
from mwpc_exact.conflict_proof import state_data
from mwpc_exact.eos_policy import EOSMode, EOSPolicy
from mwpc_exact.mass_certificate import ProbabilityInput
from mwpc_exact.reference.normalization import normalize_to_cnf
from mwpc_exact.state import SelectionInput
from mwpc_exact.support import SupportPolicy, build_per_position_support
from mwpc_exact.tokenizer_bytes import CompositionalByteLevelAdapter
from mwpc_exact.types import SupportKind

WORK = Path(__file__).resolve().parent
ROOT = WORK.parents[2]


def digest(data):
    return hashlib.sha256(data).hexdigest()


def instances(folder, tokenizer, seed):
    found = {}
    for path in sorted((folder / "tests/draft2020-12").glob("*.json")):
        for group in json.loads(path.read_text()):
            for test in group["tests"]:
                if not isinstance(test["data"], (dict, list)):
                    continue
                text = json.dumps(
                    test["data"], sort_keys=True, separators=(",", ":"), ensure_ascii=True
                )
                tokens = tokenizer.encode(text, add_special_tokens=False)
                if 12 <= len(tokens) <= 96:
                    key = digest(f"{seed}/{text}".encode())
                    found.setdefault(
                        key,
                        dict(
                            key=key,
                            text=text,
                            tokens=tokens,
                            file=path.name,
                            description=test["description"],
                        ),
                    )
    return [found[k] for k in sorted(found)[:6]]


def recognized(path, adapter):
    try:
        json.loads(
            adapter.detokenize_bytes(path).decode(),
            parse_constant=lambda s: (_ for _ in ()).throw(ValueError(s)),
        )
        return True
    except (ValueError, UnicodeDecodeError):
        return False


class Scores:
    def __init__(self, free, rows, q, hidden, marginals):
        self.free, self.q, self.hidden = free, q, hidden
        self.direction = np.random.default_rng(20261009).choice((-1.0, 1.0), q.shape[1])
        self.projection = (
            hidden[:, 0, None]
            * np.tile(
                np.r_[
                    self.direction[sorted(set(t for i in free for t in rows[i]))],
                    q @ self.direction,
                ],
                (len(free), 1),
            )
        ).flatten()
        self.vocab = sorted(set(t for i in free for t in rows[i]))
        self.indices = {t: j for j, t in enumerate(self.vocab)}
        self.d = len(self.vocab) + len(free)
        gram = np.eye(self.d)
        gram[: len(self.vocab), len(self.vocab) :] = q[:, self.vocab].T
        gram[len(self.vocab) :, : len(self.vocab)] = q[:, self.vocab]
        gram[len(self.vocab) :, len(self.vocab) :] = q @ q.T
        features = hidden @ hidden.T + 1  # output weights AND bias
        self.metric = np.kron(features, gram)
        eigen, vectors = np.linalg.eigh(self.metric)
        assert eigen.min() >= -1e-10 * max(eigen.max(), 1)
        self.embedding = vectors * np.sqrt(np.maximum(eigen, 0))[None, :]
        self.offset = np.zeros((len(free), self.d))
        for j, i in enumerate(free):
            for t, m in zip(rows[i], marginals[i], strict=True):
                self.offset[j, self.indices[t]] = -float(m)

    def coefficients(self, path, order, power, reward):
        picked = self.q[np.arange(len(self.free)), [path[i] for i in self.free]] ** power
        inverse = np.zeros(len(self.free))
        remaining = list(range(len(self.free)))
        for chosen in order:
            inverse[remaining] += 1 / picked[remaining].sum()
            remaining.remove(self.free.index(chosen))
        b = np.array([i in order for i in self.free]) - picked * inverse
        out = self.offset.copy()
        for j, i in enumerate(self.free):
            out[j, self.indices[path[i]]] += 1 + power * b[j]
            out[j, len(self.vocab) + j] -= power * b[j]
        return reward * out.flatten()

    def vector(self, path, order, power, reward):
        return self.coefficients(path, order, power, reward) @ self.embedding

    def adjoint(self, coefficients):
        coeff = coefficients.reshape(len(self.free), self.d)
        out = coeff[:, len(self.vocab) :] @ self.q
        out[:, self.vocab] += coeff[:, : len(self.vocab)]
        return out


def variance_oracle(paths, weights, p0, scores, targets, power):
    groups, all_prob, all_score = {}, [], []
    direction_mean = 0.0
    rates = tuple(tuple(q**power for q in row) for row in p0.probabilities)
    for order in itertools.permutations(p0.free, 2):
        for path, base_w in zip(paths, weights, strict=True):
            p = Problem(p0.plan, p0.probabilities, rates, order, {i: path[i] for i in order})
            probability = float(base_w * p.likelihood(path))
            reward = sum(path[i] == targets[i] for i in order) / len(order)
            coeff = scores.coefficients(path, order, power, reward)
            score = coeff @ scores.embedding
            direction_mean += probability * (coeff @ scores.projection)
            key = (order, tuple(path[i] for i in order))
            groups.setdefault(key, []).append((path, probability, score))
            all_prob.append(probability)
            all_score.append(score)
    probabilities, vectors = np.asarray(all_prob), np.asarray(all_score)
    assert abs(probabilities.sum() - 1) < 1e-10
    mean = probabilities @ vectors
    second = (probabilities * np.einsum("ij,ij->i", vectors, vectors)).sum()
    totals = {name: 0.0 for name in ("conditional_mean", "base_imh_rb", "single_imh_rb")}
    for (order, observed), entries in groups.items():
        paths_g = [x[0] for x in entries]
        w = np.array([x[1] for x in entries])
        mass = w.sum()
        w /= mass
        v = np.array([x[2] for x in entries])
        group_mean = w @ v
        totals["conditional_mean"] += mass * (group_mean @ group_mean)
        norms = np.einsum("ij,ij->i", v, v)
        pair_gram = v @ v.T
        if not np.any(v):
            continue
        p = Problem(
            p0.plan, p0.probabilities, rates, order, dict(zip(order, observed, strict=True))
        )
        for name, constructor in (
            ("base_imh_rb", BaseRejection),
            ("single_imh_rb", partial(SingleTilt, dyadic_coefficients=True)),
        ):
            sampler = constructor(p)
            proposal = np.array(
                [
                    float(
                        math.prod(
                            sampler.base.probabilities[i][p.indices[i][path[i]]] for i in p.free
                        )
                    )
                    for path in paths_g
                ]
            )
            proposal /= proposal.sum()
            ratio = w / proposal
            a = np.minimum(1, ratio[None, :] / ratio[:, None])
            b = a / 2
            pair_weights = w[:, None] * proposal[None, :]
            norm = (
                (1 - b) ** 2 * norms[:, None] + b**2 * norms[None, :] + 2 * b * (1 - b) * pair_gram
            )
            totals[name] += mass * (pair_weights * norm).sum()
            pair_mean = (pair_weights * (1 - b)).sum(axis=1) @ v + (pair_weights * b).sum(
                axis=0
            ) @ v
            assert np.allclose(pair_mean, group_mean, rtol=1e-8, atol=1e-8)
    original = max(0, second - mean @ mean)
    variances = {name: max(0, value - mean @ mean) for name, value in totals.items()}
    variances["original"] = original
    variances["two_iid"] = (original + variances["conditional_mean"]) / 2
    for value in variances.values():
        assert value <= original + 1e-8 * max(original, 1)
    return dict(
        events=len(probabilities),
        observable_events=len(groups),
        variances=variances,
        gradient_norm_squared=float(mean @ mean),
        directional_mean=float(direction_mean),
        mean_reward=float(
            sum(
                probability * sum(path[i] == targets[i] for i in order) / 2
                for (order, _), entries in groups.items()
                for path, probability, _ in entries
            )
        ),
    )


def directional_check(paths, scores, targets, power):
    epsilon = 1e-5 / max(1, abs(scores.hidden[:, 0]).max())
    selections = np.array([[path[i] for i in scores.free] for path in paths])

    def objective(shift):
        q = scores.q * np.exp(shift * scores.hidden[:, 0, None] * scores.direction[None, :])
        q /= q.sum(axis=1, keepdims=True)
        picked = q[np.arange(len(scores.free))[None, :], selections]
        weights = picked.prod(axis=1)
        weights /= weights.sum()
        rates = picked**power
        total = 0.0
        for order in itertools.permutations(range(len(scores.free)), 2):
            probability = weights.copy()
            remaining = list(range(len(scores.free)))
            for chosen in order:
                probability *= rates[:, chosen] / rates[:, remaining].sum(axis=1)
                remaining.remove(chosen)
            reward = sum(selections[:, j] == targets[scores.free[j]] for j in order) / 2
            total += probability @ reward
        return total

    return (objective(epsilon) - objective(-epsilon)) / (2 * epsilon)


def run(args):
    if subprocess.check_output(["git", "status", "--porcelain"], cwd=ROOT).strip():
        raise ValueError("commit code/protocol before measuring")
    protocol_path = WORK / "neural-utility-protocol.json"
    protocol = json.loads(protocol_path.read_text())
    config = json.loads((ROOT / protocol["model_config"]).read_text())
    torch.set_num_threads(4)
    torch.manual_seed(protocol["seed"])
    tokenizer = AutoTokenizer.from_pretrained(
        config["tokenizer_id"],
        revision=config["tokenizer_revision"],
        cache_dir=str(ROOT / ".cache/mdlm"),
        local_files_only=True,
    )
    selected = instances(args.source, tokenizer, protocol["seed"])
    assert len(selected) == 6
    args.output.mkdir(parents=True, exist_ok=False)
    model, hashes, adapted = load_cpu_model(config, ROOT / ".cache/mdlm")
    for parameter in model.parameters():
        parameter.requires_grad_(False)
    head = (
        model.backbone.output_layer.linear
        if hasattr(model, "backbone")
        else model.output_layer.linear
    )
    head.weight.requires_grad_(True)
    head.bias.requires_grad_(True)
    captures = []
    hook = head.register_forward_pre_hook(
        lambda module, arguments: captures.__setitem__(slice(None), [arguments[0].detach()])
    )
    adapter = CompositionalByteLevelAdapter.from_token_pieces(
        (
            *(
                tokenizer.convert_ids_to_tokens(i) if i not in tokenizer.all_special_ids else None
                for i in range(len(tokenizer))
            ),
            None,
        )
    )
    source = source_grammar("json")
    grammar = normalize_to_cnf(source).grammar
    metadata = dict(
        commit=subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        protocol_sha256=digest(protocol_path.read_bytes()),
        model_hashes=hashes,
        adapted_sha256=adapted,
        torch=torch.__version__,
        cpu_threads=4,
        source_revision=protocol["external_source"]["revision"],
        selected=selected,
    )
    (args.output / "metadata.json").write_text(json.dumps(metadata, indent=2) + "\n")
    with (args.output / "rows.jsonl").open("x") as stream:

        def emit(row):
            stream.write(json.dumps(row) + "\n")
            stream.flush()

        for case in selected:
            key = case["key"]
            tokens = case["tokens"]
            n = len(tokens)
            offset = int(digest(case["text"].encode()), 16) % (n - 4 + 1)
            free = tuple(range(offset, offset + 4))
            targets = dict(zip(range(n), tokens, strict=True))
            canvas = tuple(None if i in free else t for i, t in enumerate(tokens))
            inputs = torch.tensor([[config["mask_token_id"] if t is None else t for t in canvas]])
            start = perf_counter()
            logits_all = model(input_ids=inputs, timesteps=torch.zeros(1))
            forward = perf_counter() - start
            input_start = perf_counter()
            logits = logits_all[0, list(free)].detach().to(torch.float64)
            logits[:, config["mask_token_id"]] = float("-inf")
            q = logits.softmax(-1).numpy()
            rows = {i: (t,) for i, t in enumerate(canvas) if t is not None}
            distributions = [(Q(1),)] * n
            for j, i in enumerate(free):
                row = np.argsort(-q[j], kind="stable")[:8].tolist()
                rows[i] = tuple(sorted(row))
                total = sum(map(Q.from_float, map(float, q[j])), Q())
                distributions[i] = tuple(Q.from_float(float(q[j, t])) / total for t in rows[i])
            support = build_per_position_support(
                canvas=canvas,
                policy=SupportPolicy(
                    kind=SupportKind.EXPLICIT,
                    vocabulary_size=adapter.vocabulary_size,
                    pruning_description="original top8; no answer injection",
                ),
                explicit_support=rows,
            )
            state = SelectionInput(grammar, canvas, (), support, adapter, EOSPolicy(EOSMode.ABSENT))
            data = ProbabilityInput(state, tuple(distributions))
            input_seconds = perf_counter() - input_start
            try:
                start = perf_counter()
                plan = compile_cfg_sampler(
                    source,
                    state,
                    timeout_seconds=30,
                    max_chart_cells=200000,
                    max_alternatives=1000000,
                )
                compile_seconds = perf_counter() - start
                start = perf_counter()
                posterior = plan.evaluate(data)
                normalization = perf_counter() - start
                if not posterior.valid_mass:
                    raise ValueError("zero syntax mass on original top8")
                paths = []
                weights = []
                for choices in itertools.product(*(rows[i] for i in free)):
                    path = list(tokens)
                    for i, t in zip(free, choices, strict=True):
                        path[i] = t
                    if recognized(path, adapter):
                        paths.append(tuple(path))
                        weights.append(
                            math.prod(data.probabilities[i][rows[i].index(path[i])] for i in free)
                        )
                z = sum(weights, Q())
                assert z == posterior.valid_mass
                weights = [w / z for w in weights]
                hidden = captures[-1][0, list(free)].numpy().astype(np.float64)
                scores = Scores(free, state.support.rows, q, hidden, posterior.marginals)
                p0 = Problem(plan, data.probabilities, data.probabilities, (), {})
                capture = dict(
                    input=state_data(state),
                    probabilities=[
                        [[p.numerator, p.denominator] for p in row] for row in data.probabilities
                    ],
                    q_selected=q[:, scores.vocab].tolist(),
                    q_gram=(q @ q.T).tolist(),
                    head_feature_gram=(hidden @ hidden.T + 1).tolist(),
                    omitted_mass=str(data.omitted_mass),
                    target_missing=[i for i in free if targets[i] not in rows[i]],
                )
                (args.output / f"{key}-input.json").write_text(json.dumps(capture) + "\n")
                for power in (1, 2):
                    oracle = variance_oracle(paths, weights, p0, scores, targets, power)
                    finite_difference = directional_check(paths, scores, targets, power)
                    derivative_error = abs(finite_difference - oracle["directional_mean"]) / max(
                        1, abs(finite_difference)
                    )
                    assert derivative_error < 1e-5
                    oracle.update(
                        finite_difference=finite_difference,
                        relative_derivative_error=derivative_error,
                    )
                    emit(
                        dict(
                            case=key,
                            stage="variance",
                            power=power,
                            status="complete",
                            **oracle,
                            forward_seconds=forward,
                            normalization_seconds=normalization,
                            compilation_seconds=compile_seconds,
                            valid_token_paths=len(paths),
                            omitted_mass=str(data.omitted_mass),
                            target_missing=capture["target_missing"],
                        )
                    )
                    rates = tuple(tuple(v**power for v in row) for row in data.probabilities)
                    constructors = [
                        ("base_iid", partial(BaseRejection, tight_bounds=True)),
                        ("single_iid", partial(SingleTilt, dyadic_coefficients=True)),
                        (
                            "mixture_iid",
                            partial(
                                TangentMixture,
                                decision_cache_statistics,
                                dyadic_unaries=True,
                                tight_bounds=True,
                                dyadic_coefficients=True,
                            ),
                        ),
                        ("base_imh_rb", partial(BaseRejection, tight_bounds=True)),
                        ("single_imh_rb", partial(SingleTilt, dyadic_coefficients=True)),
                        ("conditional_mean", EnumeratedTarget),
                    ]
                    for rollout in range(12):
                        seed = protocol["seed"] + int(key[:8], 16) + 1000 * power + rollout
                        rng = Random(seed)
                        primitive_start = perf_counter()
                        original = posterior.sample(rng)
                        indices = [
                            dict((t, j) for j, t in enumerate(row)) for row in state.support.rows
                        ]
                        order = select_order(free, rates, original, indices, 2, rng)
                        p = Problem(
                            plan, data.probabilities, rates, order, {i: original[i] for i in order}
                        )
                        reward = sum(original[i] == targets[i] for i in order) / 2
                        c0 = scores.coefficients(original, order, power, reward)
                        scores.adjoint(c0)
                        primitive_seconds = perf_counter() - primitive_start
                        # Actual output-head backward; all parameters except head frozen.
                        backward_times = []
                        backward_cpu = []
                        forward_cpu = []
                        forwards = []
                        norm_error = None
                        for _rep in range(3):
                            start = perf_counter()
                            cpu_start = process_time()
                            with torch.no_grad():
                                model(input_ids=inputs, timesteps=torch.zeros(1))
                            forwards.append(perf_counter() - start)
                            forward_cpu.append(process_time() - cpu_start)
                            features = captures[-1][0, list(free)]
                            if not reward:
                                backward_times.append(0.0)
                                backward_cpu.append(0.0)
                                norm_error = 0.0
                                continue
                            adjoint = torch.from_numpy(scores.adjoint(c0)).to(features.dtype)
                            start = perf_counter()
                            cpu_start = process_time()
                            out = head(features)
                            grads = torch.autograd.grad(
                                out, (head.weight, head.bias), grad_outputs=adjoint
                            )
                            backward_times.append(perf_counter() - start)
                            backward_cpu.append(process_time() - cpu_start)
                            measured = sum(float(g.double().square().sum()) for g in grads)
                            expected = float(c0 @ scores.metric @ c0)
                            norm_error = abs(measured - expected) / max(1, expected)
                            assert norm_error < 1e-5
                        emit(
                            dict(
                                case=key,
                                stage="neural_cost",
                                power=power,
                                rollout=rollout,
                                status="complete",
                                forward_seconds=forwards,
                                backward_seconds=backward_times,
                                forward_cpu_seconds=forward_cpu,
                                backward_cpu_seconds=backward_cpu,
                                load_average=Path("/proc/loadavg").read_text().strip(),
                                autograd_relative_norm_error=norm_error,
                                input_seconds=input_seconds,
                                normalization_seconds=normalization,
                                compilation_seconds=compile_seconds,
                                primitive_seconds=primitive_seconds,
                                zero_reward_shortcut=not bool(reward),
                            )
                        )
                        for rep in range(3):
                            for name, constructor in constructors[rep:] + constructors[:rep]:
                                start = perf_counter()
                                cpu_start = process_time()
                                try:
                                    if not reward:
                                        emit(
                                            dict(
                                                case=key,
                                                stage="extra_cost",
                                                power=power,
                                                rollout=rollout,
                                                repetition=rep,
                                                method=name,
                                                status="complete",
                                                seconds=0.0,
                                                cpu_seconds=0.0,
                                                zero_reward_shortcut=True,
                                            )
                                        )
                                        continue
                                    end = monotonic() + 10
                                    sampler = constructor(p, end=end)
                                    if name.endswith("imh_rb"):
                                        proposed, a = proposed_move(
                                            sampler, original, Random(seed + rep), end
                                        )
                                        c1 = scores.coefficients(proposed, order, power, reward)
                                        average = (1 - float(a) / 2) * c0 + float(a) * c1 / 2
                                    elif name == "conditional_mean":
                                        average = sum(
                                            float(w / sampler.target_mass)
                                            * scores.coefficients(y, order, power, reward)
                                            for y, w in zip(
                                                sampler.paths, sampler.weights, strict=True
                                            )
                                        )
                                    else:
                                        proposed, _ = sampler.sample(Random(seed + rep), end)
                                        average = (
                                            c0 + scores.coefficients(proposed, order, power, reward)
                                        ) / 2
                                    scores.adjoint(
                                        average
                                    )  # dense head adjoint, same backward shape
                                    emit(
                                        dict(
                                            case=key,
                                            stage="extra_cost",
                                            power=power,
                                            rollout=rollout,
                                            repetition=rep,
                                            method=name,
                                            status="complete",
                                            seconds=perf_counter() - start,
                                            cpu_seconds=process_time() - cpu_start,
                                            order=order,
                                            observed=p.observed,
                                            **decision_cache_statistics(sampler),
                                        )
                                    )
                                except Exception as error:
                                    emit(
                                        dict(
                                            case=key,
                                            stage="extra_cost",
                                            power=power,
                                            rollout=rollout,
                                            repetition=rep,
                                            method=name,
                                            status="unresolved",
                                            seconds=perf_counter() - start,
                                            cpu_seconds=process_time() - cpu_start,
                                            error=repr(error),
                                        )
                                    )
                    print(key[:12], power, oracle["variances"], flush=True)
            except Exception as error:
                emit(dict(case=key, stage="case", status="unresolved", error=repr(error)))
                print(key[:12], repr(error), flush=True)
    hook.remove()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    run(parser.parse_args())
