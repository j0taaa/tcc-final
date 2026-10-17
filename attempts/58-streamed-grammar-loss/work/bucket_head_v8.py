"""Classical size-bucketed merge, with unchanged projection/full VJP kernels."""

from collections import Counter, defaultdict

import torch
import triton
import triton.language as tl

from .gpu_head import _project, _targets
from .tiled_head_v6 import _Tiled, prepare


@triton.jit
def _copy(
    Part,
    Bounds,
    Classes,
    Z,
    N: tl.constexpr,
    P: tl.constexpr,
    C: tl.constexpr,
    NC: tl.constexpr,
    B: tl.constexpr,
):
    row = tl.program_id(0) * B + tl.arange(0, B)
    idx = tl.program_id(1) * B + tl.arange(0, B)
    cls = tl.load(Classes + idx, idx < NC, 0)
    start = tl.load(Bounds + cls * 2)
    value = tl.load(
        Part + row[:, None] * P + start[None, :], (row[:, None] < N) & (idx[None, :] < NC), 0
    )
    tl.store(Z + row[:, None] * C + cls[None, :], value, (row[:, None] < N) & (idx[None, :] < NC))


@triton.jit
def _reduce(
    Part,
    Bounds,
    Classes,
    Z,
    N: tl.constexpr,
    P: tl.constexpr,
    C: tl.constexpr,
    BLOCK: tl.constexpr,
    BN: tl.constexpr,
):
    row = tl.program_id(0) * BN + tl.arange(0, BN)
    cls = tl.load(Classes + tl.program_id(1))
    lo, hi = tl.load(Bounds + cls * 2), tl.load(Bounds + cls * 2 + 1)
    idx = lo + tl.arange(0, BLOCK)
    values = tl.load(
        Part + row[:, None] * P + idx[None, :],
        (row[:, None] < N) & (idx[None, :] < hi),
        -float("inf"),
    )
    maximum = tl.max(values, 1)
    safe = tl.where(maximum > -float("inf"), maximum, 0)
    value = safe + tl.log(tl.sum(tl.exp(values - safe[:, None]), 1))
    tl.store(Z + row * C + cls, value, row < N)


def prepare_bucket(mapping, device, tile):
    meta = prepare(mapping, device, tile)
    counts = Counter(mapping)
    groups = defaultdict(list)
    for cls in range(len(counts)):
        panels = triton.cdiv(counts[cls], tile[1])
        groups[triton.next_power_of_2(panels)].append(cls)
    meta["buckets"] = [
        (block, torch.tensor(ids, device=device, dtype=torch.int32))
        for block, ids in sorted(groups.items())
    ]
    return meta


class _Bucket(torch.autograd.Function):
    @staticmethod
    def forward(ctx, h, w, b, t, meta):
        n, d = h.shape
        p, c, bn, bv = len(meta["class"]), meta["C"], meta["BN"], meta["BV"]
        part = h.new_empty((n, p))
        z, target = h.new_empty((n, c)), h.new_empty((n,))
        _project[(triton.cdiv(n, bn), p)](
            h, w, b, meta["ids"], part, n, d, p, bn, bv, 32, num_warps=4
        )
        for block, ids in meta["buckets"]:
            if block == 1:
                _copy[(triton.cdiv(n, 32), triton.cdiv(len(ids), 32))](
                    part, meta["bounds"], ids, z, n, p, c, len(ids), 32, num_warps=4
                )
            else:
                rows = min(16, max(1, 2048 // block))
                _reduce[(triton.cdiv(n, rows), len(ids))](
                    part, meta["bounds"], ids, z, n, p, c, block, rows, num_warps=4
                )
        _targets[(n,)](h, w, b, t, target, d, triton.next_power_of_2(d), num_warps=4)
        ctx.save_for_backward(h, w, b, t, z)
        ctx.meta = meta
        return z, target

    @staticmethod
    def backward(ctx, dz, dt):
        return _Tiled.backward(ctx, dz, dt)


def bucket_head(h, w, b, t, meta):
    return _Bucket.apply(h, w, b, t, meta)
