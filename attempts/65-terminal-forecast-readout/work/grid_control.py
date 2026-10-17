"""Classical finite-grid sum/moment DP; ideal weights, not finite-RNG exactness."""

from __future__ import annotations

import json
import math
from collections import defaultdict
from dataclasses import dataclass

import numpy as np
import torch

WHITESPACE = " \t\r\n"
SPELLINGS = {"0": 0, "1": 100, "1.0": 100, "1.00": 100}
SPELLINGS.update({f"0.{j}": 10 * j for j in range(10)})
SPELLINGS.update({f"0.{j:02d}": j for j in range(100)})
PREFIXES = {s[:k] for s in SPELLINGS for k in range(len(s) + 1)}


@dataclass(frozen=True)
class ParseState:
    piece: int = 0
    fragment: str = ""
    ended: bool = False


class SemanticParser:
    def __init__(self, labels, texts, eot, pad):
        self.labels, self.texts, self.eot, self.pad = tuple(labels), texts, eot, pad
        assert self.labels and len(set(labels)) == len(labels)
        self.pieces = ["{", json.dumps("probabilities"), ":", "{"]
        for j, label in enumerate(labels):
            if j:
                self.pieces.append(",")
            self.pieces.extend([json.dumps(label), ":", j])
        self.pieces.extend(["}", "}"])
        self.cache = {}

    def feed(self, state, token):
        key = state, token
        if key not in self.cache:
            self.cache[key] = self._feed(state, token)
        return self.cache[key]

    def _feed(self, state, token):
        if state.ended:
            return (state, ()) if token == self.pad else None
        if token == self.eot:
            if state.piece == len(self.pieces) and not state.fragment:
                return ParseState(state.piece, ended=True), ()
            return None
        if token == self.pad:
            return None
        piece, fragment, events = state.piece, state.fragment, []
        for char in self.texts[token]:
            while True:
                if piece == len(self.pieces):
                    if char not in WHITESPACE:
                        return None
                    break
                expected = self.pieces[piece]
                if isinstance(expected, int):
                    if char in "0123456789.":
                        fragment += char
                        if fragment not in PREFIXES:
                            return None
                        break
                    if fragment not in SPELLINGS:
                        if not fragment and char in WHITESPACE:
                            break
                        return None
                    events.append((expected, SPELLINGS[fragment]))
                    piece, fragment = piece + 1, ""
                    continue  # the delimiter also belongs to the next piece
                if not fragment and char in WHITESPACE:
                    break
                position = len(fragment)
                if char != expected[position]:
                    return None
                fragment += char
                if fragment == expected:
                    piece, fragment = piece + 1, ""
                break
        return ParseState(piece, fragment), tuple(events)

    def prefix(self, ids):
        state, events = ParseState(), []
        for token in ids:
            item = self.feed(state, token)
            if item is None:
                raise ValueError("Accepted prefix is outside the semantic language")
            state, update = item
            events.extend(update)
        return state, events


def moments(layers, start, end_weights, parser, prefix=()):
    """Compute conditional semantic moments without enumerating completed vectors.

    A layer maps native node -> (destination, original token ID, edge weight).
    Fraction input yields Fraction results; native float inputs are ordinary
    float64 arithmetic. Common per-layer normalization prevents tiny total
    valid-word mass from underflowing the whole forward recurrence.
    """
    state, events = parser.prefix(prefix)
    k = len(parser.labels)
    initial = [1, *([0] * k), 0]
    total = 0
    for j, x in events:
        total += x
        initial[j + 1] += x
        initial[-1] += x * x
    semantic = {(start, state, total): tuple(initial)}
    plain = {start: 1}
    transitions = 0
    peak = 1
    for layer in layers:
        next_plain = defaultdict(int)
        for node, mass in plain.items():
            for target, _, weight in layer.get(node, ()):
                next_plain[target] += mass * weight
        scale = sum(next_plain.values())
        if not scale:
            raise ValueError("Zero native path mass")
        next_semantic = {}
        for (node, state, total), value in semantic.items():
            for target, token, weight in layer.get(node, ()):
                transitions += 1
                if transitions > 5_000_000:
                    raise RuntimeError("Declared semantic transition guard exceeded")
                parsed = parser.feed(state, token)
                if parsed is None:
                    continue
                new_state, events = parsed
                updated, new_sum = list(value), total
                for j, x in events:
                    new_sum += x
                    updated[j + 1] += x * value[0]
                    updated[-1] += x * x * value[0]
                key = target, new_state, new_sum
                weighted = tuple(v * weight for v in updated)
                if key in next_semantic:
                    weighted = tuple(
                        a + b for a, b in zip(next_semantic[key], weighted, strict=True)
                    )
                next_semantic[key] = weighted
                if len(next_semantic) > 500_000:
                    raise RuntimeError("Declared semantic state guard exceeded")
        plain = {node: v / scale for node, v in next_plain.items()}
        semantic = {key: tuple(v / scale for v in value) for key, value in next_semantic.items()}
        peak = max(peak, len(semantic))
    denominator = sum(mass * end_weights.get(node, 0) for node, mass in plain.items())
    if not denominator:
        raise ValueError("Zero native accepting path mass")
    by_sum = {}
    for (node, state, total), value in semantic.items():
        if not state.ended or not end_weights.get(node, 0):
            continue
        weighted = tuple(v * end_weights[node] for v in value)
        if total in by_sum:
            weighted = tuple(a + b for a, b in zip(by_sum[total], weighted, strict=True))
        by_sum[total] = weighted
    complete = sum(v[0] for v in by_sum.values())
    if not complete:
        return {"alpha": 0, "mean": None, "variance": None, "by_sum": {}, "peak_states": peak}
    mean = []
    for j in range(k):
        mean.append(sum(v[j + 1] / s if s else v[0] / k for s, v in by_sum.items()) / complete)
    second = sum(v[-1] / (s * s) if s else v[0] / k for s, v in by_sum.items()) / complete
    variance = second - sum(v * v for v in mean)
    if variance < 0:
        assert float(variance) > -1e-12
        variance *= 0
    return {
        "alpha": complete / denominator,
        "mean": tuple(mean),
        "variance": variance,
        "second_norm": second,
        "by_sum": by_sum,
        "peak_states": peak,
        "semantic_transitions": transitions,
    }


def native_moments(snapshot):
    """Classical DP control on the native real-arithmetic path operator."""
    sampler, matcher = snapshot.compiled.sampler, snapshot.new_matcher()
    offset = snapshot.offset
    logits = snapshot.scores[0, offset:, : sampler.vocab_size].float()
    lp = torch.log_softmax(logits, dim=-1).cpu().double().numpy()
    forced = snapshot.tokens[0, offset:].cpu().numpy().copy()
    budget = matcher.budget()
    if budget is not None:
        forced[budget:] = snapshot.compiled.eos_token_id
    emit = sampler.emission.cpu().double().numpy()
    src, dst = sampler.edge_src.cpu().tolist(), sampler.edge_index.cpu().tolist()
    layers = []
    for p, pin in enumerate(forced):
        layer = defaultdict(list)
        for e, (s, target) in enumerate(zip(src, dst, strict=True)):
            ids = np.flatnonzero(emit[e] > 0)
            if pin >= 0:
                if emit[e, pin] <= 0:
                    continue
                chosen, weight = int(pin), 1.0
            else:
                weight = math.fsum(np.exp(lp[p, ids]) * emit[e, ids])
                if not weight:
                    continue
                chosen = int(ids[np.argmax(lp[p, ids] + np.log(emit[e, ids]))])
            layer[s].append((target, chosen, weight))
        layers.append(layer)
    end = matcher.end_log(len(forced)).cpu().double().tolist()
    end_weights = {n: math.exp(v) for n, v in enumerate(end) if math.isfinite(v)}
    tokenizer = snapshot.tokenizer
    parser = SemanticParser(
        snapshot.labels,
        {t: tokenizer.decode(t) for t in range(sampler.vocab_size)},
        tokenizer.convert_tokens_to_ids("<eot>"),
        tokenizer.convert_tokens_to_ids("<pad>"),
    )
    return moments(layers, snapshot.node, end_weights, parser, snapshot.prefix)
