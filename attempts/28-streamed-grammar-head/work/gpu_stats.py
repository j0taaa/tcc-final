"""Opt-in binary64 integer reductions; no float sum or RNG approximation."""

import numpy as np
import torch
import triton
import triton.language as tl

from .block_stats import MASK32, MASK52, BlockStats


@triton.jit
def _range_kernel(Q, R, V: tl.constexpr, CHUNKS: tl.constexpr, BLOCK: tl.constexpr):
    row, chunk = tl.program_id(0), tl.program_id(1)
    ix = chunk * BLOCK + tl.arange(0, BLOCK)
    bits = tl.load(Q + row * V + ix, ix < V, other=0).to(tl.uint64, bitcast=True)
    magnitude = bits & 0x7FFFFFFFFFFFFFFF
    exponent = ((bits >> 52) & 2047).to(tl.int32)
    shift = tl.maximum(exponent - 1, 0)
    positive = (magnitude != 0) & (ix < V)
    invalid = positive & (((bits >> 63) != 0) | (exponent == 2047))
    start = (row * CHUNKS + chunk) * 3
    tl.store(R + start, tl.min(tl.where(positive, shift, 2048), 0))
    tl.store(R + start + 1, tl.max(tl.where(positive, shift, 0), 0))
    tl.store(R + start + 2, tl.max(invalid.to(tl.int32), 0))


@triton.jit
def _merge_range(R, OUT, CHUNKS: tl.constexpr, BLOCK: tl.constexpr):
    row = tl.program_id(0)
    ix = tl.arange(0, BLOCK)
    lo = tl.load(R + (row * CHUNKS + ix) * 3, ix < CHUNKS, other=2048)
    hi = tl.load(R + (row * CHUNKS + ix) * 3 + 1, ix < CHUNKS, other=0)
    bad = tl.load(R + (row * CHUNKS + ix) * 3 + 2, ix < CHUNKS, other=0)
    tl.store(OUT + row * 3, tl.min(lo, 0))
    tl.store(OUT + row * 3 + 1, tl.max(hi, 0))
    tl.store(OUT + row * 3 + 2, tl.max(bad, 0))


@triton.jit
def _digits_kernel(
    Q,
    IDS,
    STARTS,
    SIZES,
    MINIMUM,
    OUT,
    V: tl.constexpr,
    M: tl.constexpr,
    WORDS: tl.constexpr,
    BLOCK: tl.constexpr,
):
    row, block, word = tl.program_id(0), tl.program_id(1), tl.program_id(2)
    ix = tl.arange(0, BLOCK)
    size, start = tl.load(SIZES + block), tl.load(STARTS + block)
    token = tl.load(IDS + start + ix, ix < size, other=0)
    bits = tl.load(Q + row * V + token, ix < size, other=0).to(tl.uint64, bitcast=True)
    exponent = ((bits >> 52) & 2047).to(tl.int32)
    mantissa = (bits & 0xFFFFFFFFFFFFF) | tl.where(exponent > 0, 1 << 52, 0).to(tl.uint64)
    delta = tl.maximum(exponent - 1, 0) - tl.load(MINIMUM + row) - 32 * word
    left = (mantissa << tl.minimum(tl.maximum(delta, 0), 31)) & 0xFFFFFFFF
    right = (mantissa >> tl.minimum(tl.maximum(-delta, 0), 63)) & 0xFFFFFFFF
    digit = tl.where(
        (delta >= 0) & (delta < 32), left, tl.where((delta < 0) & (delta > -64), right, 0)
    )
    tl.store(OUT + (row * M + block) * WORDS + word, tl.sum(digit, 0))


class DevicePartition:
    def __init__(self, partition, device):
        self.partition, self.device = partition, torch.device(device)
        self.ids = torch.tensor(partition.permutation, dtype=torch.int64, device=device)
        self.starts = torch.tensor(partition.starts, dtype=torch.int32, device=device)
        self.sizes = torch.tensor(partition.sizes, dtype=torch.int32, device=device)
        self.block_of = torch.tensor(partition.block_of, dtype=torch.int64, device=device)


def validate(q, mapping):
    if q.dtype != torch.float64 or q.ndim != 2 or not q.is_contiguous():
        raise ValueError("contiguous binary64 GPU matrix required")
    if q.device != mapping.device or q.device.type != "cuda":
        raise ValueError("matrix and partition must share CUDA device")
    if q.shape[1] != len(mapping.partition.class_of) or not q.shape[0]:
        raise ValueError("matrix differs from partition")


def triton_stats(q, mapping):
    validate(q, mapping)
    n, v = q.shape
    chunks = triton.cdiv(v, 1024)
    ranges = torch.empty((n, chunks, 3), dtype=torch.int32, device=q.device)
    _range_kernel[(n, chunks)](q, ranges, v, chunks, 1024)
    combined = torch.empty((n, 3), dtype=torch.int32, device=q.device)
    _merge_range[(n,)](ranges, combined, chunks, triton.next_power_of_2(chunks))
    host_range = combined.cpu().numpy()
    minimum, maximum = host_range[:, 0], host_range[:, 1]
    if host_range[:, 2].any():
        raise ValueError("nonnegative finite weights required")
    if (minimum == 2048).any():
        raise ValueError("zero original row")
    words = (int((maximum - minimum + 53).max()) + 31) // 32
    low = torch.tensor(minimum, dtype=torch.int32, device=q.device)
    p = mapping.partition
    digits = torch.empty((n, len(p.blocks), words), dtype=torch.int64, device=q.device)
    _digits_kernel[(n, len(p.blocks), words)](
        q,
        mapping.ids,
        mapping.starts,
        mapping.sizes,
        low,
        digits,
        v,
        len(p.blocks),
        words,
        triton.next_power_of_2(p.block_size),
    )
    return BlockStats.from_digits(p, minimum, digits.cpu().numpy())


def torch_stats(q, mapping):
    """Independent dense vectorized integer/scatter control, same exact weights."""
    validate(q, mapping)
    if bool((~torch.isfinite(q) | (q < 0)).any()):
        raise ValueError("nonnegative finite weights required")
    bits = q.view(torch.int64)
    exponent = (bits >> 52) & 2047
    mantissa = (bits & MASK52) | ((exponent > 0).to(torch.int64) << 52)
    shifts = (exponent - 1).clamp_min(0)
    positive = q > 0
    minimum = torch.where(positive, shifts, 2048).amin(dim=1)
    maximum = torch.where(positive, shifts, 0).amax(dim=1)
    bounds = torch.stack((minimum, maximum), dim=1).cpu().numpy()
    if (bounds[:, 0] == 2048).any():
        raise ValueError("zero original row")
    words = (int((bounds[:, 1] - bounds[:, 0] + 53).max()) + 31) // 32
    relative = shifts - minimum[:, None]
    p = mapping.partition
    raw = torch.zeros((len(q), len(p.blocks), words), dtype=torch.int64, device=q.device)
    for j in range(words):
        delta = relative - 32 * j
        left = (mantissa << delta.clamp(0, 31)) & MASK32
        right = (mantissa >> (-delta).clamp(0, 63)) & MASK32
        digit = torch.where(
            (delta >= 0) & (delta < 32), left, torch.where((delta < 0) & (delta > -64), right, 0)
        )
        raw[:, :, j].scatter_add_(1, mapping.block_of.expand(len(q), -1), digit)
    return BlockStats.from_digits(p, bounds[:, 0], raw.cpu().numpy().astype(np.uint64))
