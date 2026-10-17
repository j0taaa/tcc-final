"""Independent small path enumeration, not an exact finite-RNG law verifier."""

from __future__ import annotations

import math
from collections import Counter, defaultdict

import numpy as np
import torch


def enumeration(snapshot, limit: int = 500_000) -> dict:
    sampler = snapshot.compiled.sampler
    matcher = snapshot.new_matcher()
    k = snapshot.offset
    scores = snapshot.scores[0, k:, : sampler.vocab_size]
    log_probs = torch.log_softmax(scores.float(), dim=-1).cpu().double().numpy()
    forced = snapshot.tokens[0, k:].cpu().numpy().copy()
    budget = matcher.budget()
    if budget is not None and budget < len(forced):
        forced[budget:] = snapshot.compiled.eos_token_id
    emit = sampler.emission.cpu().double().numpy()
    src, dst = sampler.edge_src.cpu().tolist(), sampler.edge_index.cpu().tolist()
    end = matcher.end_log(len(forced)).cpu().double().numpy()
    outgoing = defaultdict(list)
    for e, s in enumerate(src):
        outgoing[s].append(e)
    transitions = []
    for p, pin in enumerate(forced):
        layer = {}
        for e in range(len(src)):
            ids = np.flatnonzero(emit[e] > 0)
            if pin >= 0:
                if pin not in ids:
                    continue
                weight, chosen = 1.0, int(pin)
            else:
                weights = np.exp(log_probs[p, ids]) * emit[e, ids]
                weight = math.fsum(weights)
                if not weight:
                    continue
                # argmax over ORIGINAL IDs, with the native first-index tie rule.
                chosen = int(ids[np.argmax(log_probs[p, ids] + np.log(emit[e, ids]))])
            layer[e] = weight, chosen
        transitions.append(layer)
    rows: Counter = Counter()
    stack = [(0, snapshot.node, 1.0, tuple(snapshot.tokens[0, :k].tolist()))]
    leaves = steps = 0
    while stack:
        p, node, weight, tokens = stack.pop()
        steps += 1
        if steps > limit:
            raise RuntimeError("declared path enumeration guard exceeded")
        if p == len(transitions):
            if math.isfinite(end[node]):
                rows[tokens] += weight * math.exp(end[node])
                leaves += 1
            continue
        for e in outgoing[node]:
            if e in transitions[p]:
                probability, chosen = transitions[p][e]
                stack.append((p + 1, dst[e], weight * probability, (*tokens, chosen)))
    mass = math.fsum(rows.values())
    assert mass > 0 and all(math.isfinite(v) and v > 0 for v in rows.values())
    law = {tokens: p / mass for tokens, p in rows.items()}
    complete_mass = math.fsum(p for ids, p in law.items() if snapshot.observe(ids) is not None)
    means = [0.0] * len(snapshot.labels)
    second = 0.0
    for ids, p in law.items():
        raw = snapshot.observe(ids)
        if raw is None:
            continue
        total = sum(raw)
        point = [float(v / total) if total else 1 / len(raw) for v in raw]
        for j, v in enumerate(point):
            means[j] += p * v / complete_mass
        second += p * math.fsum(v * v for v in point) / complete_mass
    variance = second - math.fsum(v * v for v in means)
    return {
        "law": law,
        "positive_paths": leaves,
        "prefix_steps": steps,
        "complete_probability_ideal_arithmetic": complete_mass,
        "conditional_mean_ideal_arithmetic": means,
        "conditional_variance_ideal_arithmetic": variance,
    }


def independent_marginal_error(snapshot, original_scores) -> float:
    """Enumerate original token paths to verify the FIRST constrained marginals.

    We use direct emission probabilities and summation rather than the native
    segment-tree routine. This is a float64 real-weight reference only.
    """
    sampler = snapshot.compiled.sampler
    matcher = snapshot.new_matcher()
    k = snapshot.offset
    scores = torch.log_softmax(original_scores[0, k:, : sampler.vocab_size].float(), dim=-1)
    probs = scores.cpu().double().exp().numpy()
    forced = snapshot.tokens[0, k:].cpu().numpy().copy()
    budget = matcher.budget()
    if budget is not None and budget < len(forced):
        forced[budget:] = snapshot.compiled.eos_token_id
    emit = sampler.emission.cpu().double().numpy()
    src, dst = sampler.edge_src.cpu().tolist(), sampler.edge_index.cpu().tolist()
    end = matcher.end_log(len(forced)).cpu().double().numpy()
    outgoing = defaultdict(list)
    for e, s in enumerate(src):
        outgoing[s].append(e)
    marginal = np.zeros_like(probs)
    mass = 0.0
    stack = [(0, snapshot.node, 1.0, ())]
    visited = 0
    while stack:
        p, node, weight, tokens = stack.pop()
        visited += 1
        if visited > 500_000:
            raise RuntimeError("declared token enumeration guard exceeded")
        if p == len(forced):
            if math.isfinite(end[node]):
                current = weight * math.exp(end[node])
                mass += current
                for t, token in enumerate(tokens):
                    marginal[t, token] += current
            continue
        for e in outgoing[node]:
            ids = [int(forced[p])] if forced[p] >= 0 else np.flatnonzero(emit[e] > 0)
            for token in ids:
                if emit[e, token] > 0:
                    w = 1.0 if forced[p] >= 0 else probs[p, token] * emit[e, token]
                    if w:
                        stack.append((p + 1, dst[e], weight * w, (*tokens, int(token))))
    assert mass > 0
    target = snapshot.scores[0, k:, : sampler.vocab_size].cpu().double().exp().numpy()
    return float(np.max(np.abs(marginal / mass - target)))
