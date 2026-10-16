"""Classical directed CDF decision; ambiguous results retain their uniform bits."""

import torch
import triton as tr
import triton.language as tl

from .interval_frontend import _add_hi, _add_lo


@tr.jit
def interval_index(lower, upper, raw, bits: tl.constexpr, valid, N: tl.constexpr):
    lane = tl.arange(0, N)
    lo, hi = tl.where(valid, lower, 0), tl.where(valid, upper, 0)
    pl, ph = tl.associative_scan(lo, 0, _add_lo), tl.associative_scan(hi, 0, _add_hi)
    sl, sh = (
        tl.associative_scan(lo, 0, _add_lo, reverse=True),
        tl.associative_scan(hi, 0, _add_hi, reverse=True),
    )
    before_hi = tl.where(lane > 0, tl.gather(ph, tl.maximum(lane - 1, 0), 0), 0)
    after_hi = tl.where(lane + 1 < N, tl.gather(sh, tl.minimum(lane + 1, N - 1), 0), 0)
    left_den, right_den = _add_lo(before_hi, sl), _add_hi(pl, after_hi)
    left = tl.inline_asm_elementwise(
        "div.rp.f32 $0, $1, $2;",
        constraints="=f,f,f",
        args=[before_hi, left_den],
        dtype=tl.float32,
        is_pure=True,
        pack=1,
    )
    right = tl.inline_asm_elementwise(
        "div.rm.f32 $0, $1, $2;",
        constraints="=f,f,f",
        args=[pl, right_den],
        dtype=tl.float32,
        is_pure=True,
        pack=1,
    )
    count = tl.sum(valid.to(tl.int32), 0)
    left = tl.where(lane == 0, 0, tl.where(left_den > 0, left, 1))
    right = tl.where(lane + 1 == count, 1, tl.where(right_den > 0, right, 0))
    u0 = raw.to(tl.float64) * (2.0 ** (-bits))
    u1 = (raw.to(tl.float64) + 1) * (2.0 ** (-bits))
    proven = valid & (left.to(tl.float64) <= u0) & (u1 <= right.to(tl.float64))
    num = tl.sum(proven.to(tl.int32), 0)
    answer = tl.max(tl.where(proven, lane, -1), 0)
    return tl.where((num == 1) & (tl.sum(hi, 0) > 0), answer, -1)


@tr.jit
def _decide(lower, upper, source, out, length: tl.constexpr, bits: tl.constexpr, B: tl.constexpr):
    row, lane = tl.program_id(0), tl.arange(0, B)
    lo = tl.load(lower + lane, lane < length, 0)
    hi = tl.load(upper + lane, lane < length, 0)
    raw = tl.load(source + row)
    result = interval_index(lo, hi, raw, bits, lane < length, B)
    tl.store(out + row, result)


def decide(lower, upper, source, bits=32):
    if (
        lower.ndim != 1
        or upper.shape != lower.shape
        or not lower.numel()
        or lower.dtype != torch.float32
        or upper.dtype != lower.dtype
        or source.ndim != 1
        or source.dtype != torch.int64
        or lower.device.type != "cuda"
        or upper.device != lower.device
        or source.device != lower.device
        or not 1 <= bits <= 32
    ):
        raise ValueError("CUDA binary32 intervals and integer fair-bit prefixes required")
    if (
        not bool(torch.isfinite(upper).all())
        or not bool(torch.isfinite(lower).all())
        or bool((lower < 0).any())
        or bool((upper < lower).any())
        or bool((source < 0).any())
        or bool((source >= 1 << bits).any())
    ):
        raise ValueError("malformed interval/prefix; never guess a decision")
    out = torch.empty_like(source)
    _decide[(source.numel(),)](
        lower.contiguous(),
        upper.contiguous(),
        source.contiguous(),
        out,
        lower.numel(),
        bits,
        tr.next_power_of_2(lower.numel()),
    )
    return out
