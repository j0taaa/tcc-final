"""Experimental exact scalar-corrected GPU proposal; strong interval control retained."""

from fractions import Fraction as F
from math import prod

import torch

from .gpu_tickets import block_counts, edge_counts, maximum_totals, proposal_walk, token_counts
from .interval_sampler import IntervalSampler, _edge_mass
from .scalar_acceptance import acceptance


class TicketSampler:
    def __init__(self, classes, layers, accepting, *, device="cuda", block_size=1024):
        self.control = IntervalSampler(
            classes, layers, accepting, block_size=block_size, device=device
        )
        self.engine = self.control.engine
        dev = self.engine.device
        node_offsets, edge_offsets, node_positions = [0], [0], []
        for p, layer in enumerate(self.engine.layers):
            node_offsets.append(node_offsets[-1] + len(layer))
            edge_offsets.append(edge_offsets[-1] + sum(len(e) for e in layer))
            node_positions.extend([p] * len(layer))
        self.node_offsets = torch.tensor(node_offsets, dtype=torch.long, device=dev)
        self.edge_offsets = torch.tensor(edge_offsets, dtype=torch.long, device=dev)
        self.node_positions = torch.tensor(node_positions, dtype=torch.long, device=dev)
        self.final_mask = torch.tensor(
            [False] * node_offsets[-1] + list(self.engine.accepting), dtype=torch.bool, device=dev
        )

    @torch.no_grad()
    def prepare(self, weights, *, minimum_acceptance=F(99, 100)):
        result = self.engine.query(weights)
        if result["lower"] <= 0:
            raise ValueError("inconclusive positive lower mass; REFUSE without pruning")
        n, c = len(self.engine.layers), len(self.engine.classes)
        dev, v = self.engine.device, self.engine.vocabulary
        edge_lo, edge_hi = [
            torch.empty(len(self.control.positions), dtype=torch.float32, device=dev)
            for _ in range(2)
        ]
        _edge_mass[(len(self.control.positions),)](
            result["class_lower"],
            result["class_upper"],
            self.control.positions,
            self.control.graph[2],
            self.control.graph[3],
            edge_lo,
            edge_hi,
            c,
            self.control.width,
        )
        h = torch.cat(result["beta_upper"])
        scales = torch.tensor(tuple(reversed(result["scales"])), dtype=torch.float32, device=dev)
        token_cdf = torch.empty((n, v), dtype=torch.long, device=dev)
        block_cdf = torch.empty_like(self.control.graph[3])
        edge_cdf = torch.empty_like(self.control.graph[1])
        token_a = torch.empty((n, c), dtype=torch.long, device=dev)
        block_a = torch.empty(len(self.control.positions), dtype=torch.long, device=dev)
        edge_a = torch.empty(len(self.node_positions), dtype=torch.long, device=dev)
        token_bad, block_bad, edge_bad = [
            torch.empty_like(x, dtype=torch.bool) for x in (token_a, block_a, edge_a)
        ]
        token_counts[(n, c)](
            weights.contiguous(),
            self.engine.members,
            self.engine.pointer,
            result["class_upper"],
            token_cdf,
            token_a,
            token_bad,
            v,
            c,
            self.control.width,
        )
        block_counts[(len(self.control.positions),)](
            result["class_upper"],
            self.control.positions,
            self.control.graph[2],
            self.control.graph[3],
            edge_hi,
            block_cdf,
            block_a,
            block_bad,
            c,
            self.control.width,
        )
        edge_counts[(len(self.node_positions),)](
            edge_hi,
            self.control.graph[0],
            self.control.graph[1],
            self.node_positions,
            h,
            scales,
            edge_cdf,
            edge_a,
            edge_bad,
            self.control.width,
        )
        if any(bool(x.any()) for x in (token_bad, block_bad, edge_bad)):
            raise ValueError("count budget/numeric guard; REFUSE without altering support")
        maxima = torch.empty((n, 3), dtype=torch.long, device=dev)
        maximum_totals[(n,)](
            self.node_offsets, self.edge_offsets, edge_a, block_a, token_a, maxima, c, 256
        )
        values = maxima.cpu().tolist()
        factor = prod((F(int(a), 1 << 40) for row in values for a in row), start=F(1))
        # The saved upper already includes root potential and exact common scales.
        envelope = result["upper"] * factor * F(1 << 23, (1 << 23) - 1) ** (3 * n)
        if envelope < result["lower"]:
            raise RuntimeError("count envelope below certified lower mass; never clamp")
        rate = result["lower"] / envelope
        if rate < minimum_acceptance:
            raise ValueError("certified acceptance gate refused")
        return dict(
            weights=weights.contiguous(),
            frontend=result,
            potentials=h,
            scales=scales,
            edge_mass_upper=edge_hi,
            token_cdf=token_cdf,
            block_cdf=block_cdf,
            edge_cdf=edge_cdf,
            token_totals=token_a,
            block_totals=block_a,
            edge_totals=edge_a,
            maxima=values,
            envelope=envelope,
            acceptance_lower=rate,
            admission_minimum=minimum_acceptance,
        )

    @torch.no_grad()
    def propose(self, prepared, source):
        n = len(self.engine.layers)
        if (
            source.ndim != 4
            or source.shape[1:] != (n, 3, 2)
            or source.dtype != torch.int64
            or source.device != self.engine.device
        ):
            raise ValueError("CUDA uniform32 pairs per trial/position/phase required")
        if bool((source < 0).any()) or bool((source >= 1 << 32).any()):
            raise ValueError("source outside uniform32 range")
        count, dev = source.shape[0], self.engine.device
        words = torch.empty((count, n), dtype=torch.long, device=dev)
        values = torch.empty((count, n), dtype=torch.float64, device=dev)
        packet = torch.empty((count, n, 3, 3), dtype=torch.long, device=dev)
        valid = torch.empty(count, dtype=torch.bool, device=dev)
        proposal_walk[(count,)](
            prepared["weights"],
            *self.control.graph,
            self.engine.pointer,
            self.engine.members,
            prepared["edge_cdf"],
            prepared["block_cdf"],
            prepared["token_cdf"],
            source.contiguous(),
            words,
            values,
            packet,
            self.final_mask,
            valid,
            self.engine.vocabulary,
            n,
        )
        return dict(tokens=words, weights=values, packet=packet, valid=valid)

    @torch.no_grad()
    def sample_prepared(self, prepared, count, rng, *, generator=None, max_trials=8):
        if type(count) is not int or count < 1 or type(max_trials) is not int or max_trials < 1:
            raise ValueError("positive output count and fixed trial cap required")
        n, dev = len(self.engine.layers), self.engine.device
        outputs, statuses, trials = [None] * count, ["FAIL"] * count, [0] * count
        pending = list(range(count))
        proposals = 0
        for trial in range(1, max_trials + 1):
            if not pending:
                break
            source = torch.randint(
                0,
                1 << 32,
                (len(pending), n, 3, 2),
                dtype=torch.long,
                device=dev,
                generator=generator,
            )
            result = self.propose(prepared, source)
            packets = result["packet"].cpu().reshape(len(pending), -1, 3).tolist()
            weights, words, valid = (
                result["weights"].cpu().tolist(),
                result["tokens"].cpu().tolist(),
                result["valid"].cpu().tolist(),
            )
            remaining = []
            for i, index in enumerate(pending):
                a = acceptance(weights[i], packets[i], prepared["envelope"], valid=valid[i])
                proposals += 1
                trials[index] = trial
                if rng.randrange(a.denominator) < a.numerator:
                    outputs[index] = words[i]
                    statuses[index] = "COMPLETE"
                else:
                    remaining.append(index)
            pending = remaining
        tokens = torch.tensor(
            [word if word is not None else [-1] * n for word in outputs],
            dtype=torch.long,
            device=dev,
        )
        return dict(
            tokens=tokens,
            statuses=statuses,
            trials=trials,
            proposals=proposals,
            fail_bound=(1 - prepared["admission_minimum"]) ** max_trials,
        )
