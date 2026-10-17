"""Competent sparse-edge moment DP and native original-ID word/path MAP."""

from __future__ import annotations

import math
from collections import defaultdict

import numpy as np
import torch
from grid_control import SemanticParser, moments


class LazyTexts:
    def __init__(self, tokenizer):
        self.tokenizer, self.cache = tokenizer, {}

    def __getitem__(self, token):
        if token not in self.cache:
            self.cache[token] = self.tokenizer.decode(token)
        return self.cache[token]


class SparseEdges:
    def __init__(self, compiled, tokenizer):
        sampler = compiled.sampler
        array = sampler.emission.cpu().numpy()
        assert np.isin(array, (0, 1)).all(), "Native grammar uses binary token support"
        self.ids = [np.flatnonzero(row) for row in array]
        self.src = sampler.edge_src.cpu().tolist()
        self.dst = sampler.edge_index.cpu().tolist()
        self.vocab = sampler.vocab_size
        # Determinism is necessary to call state-path MAP an original-ID word MAP.
        seen = defaultdict(set)
        for source, ids in zip(self.src, self.ids, strict=True):
            current = set(ids.tolist())
            assert not seen[source].intersection(current), (
                "Overlapping native outgoing token support"
            )
            seen[source].update(current)
        self.texts = LazyTexts(tokenizer)

    def prepare(self, snapshot):
        matcher = snapshot.new_matcher()
        forced = snapshot.tokens[0, snapshot.offset :].cpu().numpy().copy()
        budget = matcher.budget()
        if budget is not None:
            forced[budget:] = snapshot.compiled.eos_token_id
        free_positions = np.flatnonzero(forced < 0).tolist()
        free_index = {p: j for j, p in enumerate(free_positions)}
        scores = snapshot.scores[0, snapshot.offset :]
        # Forced positions have indicator weights; avoid irrelevant dense reductions.
        lp = torch.log_softmax(scores[free_positions, : self.vocab].float(), dim=-1)
        lp = lp.cpu().double().numpy()
        end_logs = matcher.end_log(len(forced)).cpu().double().tolist()
        end = {node: math.exp(v) for node, v in enumerate(end_logs) if math.isfinite(v)}
        raw = []
        for p, pin in enumerate(forced):
            edges = []
            for e, ids in enumerate(self.ids):
                if pin >= 0:
                    if pin not in ids:
                        continue
                    token, log_weight = int(pin), 0.0
                else:
                    values = lp[free_index[p], ids]
                    if not len(values):
                        continue
                    position = int(np.argmax(values))
                    top = float(values[position])
                    if not math.isfinite(top):
                        continue
                    token = int(ids[position])
                    log_weight = top + math.log(math.fsum(np.exp(values - top)))
                edges.append((self.src[e], self.dst[e], token, log_weight))
            raw.append(edges)
        # Classical forward/backward Boolean trimming before numerical products.
        reach = [{snapshot.node}]
        for edges in raw:
            reach.append({v for u, v, _, _ in edges if u in reach[-1]})
        coreach = [set() for _ in range(len(raw) + 1)]
        coreach[-1] = set(end)
        for p in reversed(range(len(raw))):
            coreach[p] = {u for u, v, _, _ in raw[p] if v in coreach[p + 1]}
        layers, log_layers = [], []
        for p, edges in enumerate(raw):
            viable = [(u, v, t, w) for u, v, t, w in edges if u in reach[p] and v in coreach[p + 1]]
            if not viable:
                raise ValueError("No native coaccessible path")
            shift = max(w for _, _, _, w in viable)
            layer, log_layer = defaultdict(list), defaultdict(list)
            for u, v, token, log_weight in viable:
                weight = math.exp(log_weight - shift)
                if weight:
                    layer[u].append((v, token, weight))
                    log_layer[u].append((v, token, log_weight - shift))
            layers.append(layer)
            log_layers.append(log_layer)
        return layers, log_layers, end

    def evaluate(self, snapshot):
        layers, log_layers, end = self.prepare(snapshot)
        parser = SemanticParser(
            snapshot.labels,
            self.texts,
            snapshot.tokenizer.convert_tokens_to_ids("<eot>"),
            snapshot.tokenizer.convert_tokens_to_ids("<pad>"),
        )
        result = moments(layers, snapshot.node, end, parser, snapshot.prefix)
        best = {snapshot.node: (0.0, tuple(snapshot.tokens[0, : snapshot.offset].tolist()))}
        for layer in log_layers:
            following = {}
            for node, (score, word) in best.items():
                for target, token, log_weight in layer.get(node, ()):
                    candidate = score + log_weight, (*word, token)
                    if target not in following or candidate > following[target]:
                        following[target] = candidate
            best = following
        _, word = max(
            (score + math.log(end[node]), word)
            for node, (score, word) in best.items()
            if node in end
        )
        result["map_ids"] = word
        result["map_raw"] = snapshot.observe(word)
        result["original_id_word_map_determinism_checked"] = True
        result["semantic_vector_map_claimed"] = False
        return result
