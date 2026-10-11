"""Joint class conditioning followed by exact block/original-ID recovery."""

from functools import reduce
from math import gcd
from types import SimpleNamespace

from .block_stats import integer_weight
from .frozen.posterior import Posterior
from .summary import ClassPosterior


def choose(weights, rng):
    factor = reduce(gcd, weights, 0)
    return Posterior.choose([w // factor for w in weights] if factor > 1 else weights, rng)


class BlockPosterior(ClassPosterior):
    def __init__(self, prepared, stats, fetch):
        self.stats, self.fetch = stats, fetch
        self.free = tuple(p for p, t in enumerate(prepared.canvas) if t is None)
        if len(self.free) != len(stats.totals):
            raise ValueError("weight rows differ from free positions")
        by_position = dict(zip(self.free, range(len(self.free)), strict=True))
        self.row_of_position = by_position
        partition = stats.partition
        sums, denominators = [], []
        free_sums = stats.class_sums()
        for p, fixed in enumerate(prepared.canvas):
            if fixed is None:
                row = free_sums[by_position[p]]
            else:
                if type(fixed) is not int or not 0 <= fixed < len(partition.class_of):
                    raise ValueError("invalid fixed original token")
                row = tuple(
                    int(cid == partition.class_of[fixed]) for cid in range(partition.class_count)
                )
            sums.append(row)
            denominators.append(sum(row))
        super().__init__(
            prepared,
            SimpleNamespace(
                class_of=partition.class_of,
                canvas=prepared.canvas,
                consumed=False,
                sums=tuple(sums),
                denominators=tuple(denominators),
            ),
        )

    def sample(self, rng):
        if self.ledger.consumed:
            raise ValueError("summary already consumed")
        if not self.total:
            raise ValueError("zero_valid_mass")
        self.ledger.consumed = True
        classes, state = [], 0
        for p, layer in enumerate(self.prepared.arcs):
            out = layer[state]
            b, gids = out[
                choose(
                    [
                        w * self.beta[p + 1][b]
                        for (b, _), w in zip(out, self.arc_weights[p][state], strict=True)
                    ],
                    rng,
                )
            ]
            gid = gids[choose([self.leaf[p, g] for g in gids], rng)]
            cids = self.prepared.table.local_to_class[gid]
            classes.append(cids[choose([self.ledger.sums[p][c] for c in cids], rng)])
            state = b
        partition = self.stats.partition
        bids = []
        for p in self.free:
            row = self.row_of_position[p]
            options = partition.class_blocks[classes[p]]
            bids.append(options[choose([self.stats.totals[row][b] for b in options], rng)])
        values = self.fetch(tuple(bids))
        if len(values) != len(self.free):
            raise RuntimeError("provider changed row count")
        tokens = list(self.prepared.canvas)
        for row, (p, bid, fetched) in enumerate(zip(self.free, bids, values, strict=True)):
            block = partition.blocks[bid]
            if len(fetched) != len(block):
                raise RuntimeError("provider changed block length")
            weights = [integer_weight(v, self.stats.minimum_exponents[row]) for v in fetched]
            if any(w < 0 for w in weights) or sum(weights) != self.stats.totals[row][bid]:
                raise RuntimeError("provider changed original block mass")
            tokens[p] = block[choose(weights, rng)]
        return tuple(tokens)


def numpy_fetch(weights, partition):
    return lambda bids: tuple(weights[row, list(partition.blocks[b])] for row, b in enumerate(bids))


def cuda_fetch(weights, mapping):
    import torch

    offsets = torch.arange(mapping.partition.block_size, device=weights.device)

    def fetch(bids):
        if not bids:
            return ()
        selected = torch.tensor(bids, dtype=torch.int64, device=weights.device)
        positions = mapping.starts[selected, None] + offsets
        tokens = mapping.ids[positions.clamp_max(len(mapping.partition.class_of) - 1)]
        output = (
            weights[torch.arange(len(bids), device=weights.device)[:, None], tokens].cpu().numpy()
        )
        return tuple(output[row, : len(mapping.partition.blocks[b])] for row, b in enumerate(bids))

    return fetch
