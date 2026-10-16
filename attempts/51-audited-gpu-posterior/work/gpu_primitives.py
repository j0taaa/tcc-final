"""Opt-in CUDA correctly-directed basic operations; no Torch math ULP premise."""

import torch
import triton as tr
import triton.language as tl


@tr.jit
def _cast(source, down, up, count: tl.constexpr, B: tl.constexpr):
    i = tl.program_id(0) * B + tl.arange(0, B)
    x = tl.load(source + i, i < count, 0)
    lo = tl.inline_asm_elementwise(
        "cvt.rm.f32.f64 $0, $1;",
        constraints="=f,d",
        args=[x],
        dtype=tl.float32,
        is_pure=True,
        pack=1,
    )
    hi = tl.inline_asm_elementwise(
        "cvt.rp.f32.f64 $0, $1;",
        constraints="=f,d",
        args=[x],
        dtype=tl.float32,
        is_pure=True,
        pack=1,
    )
    tl.store(down + i, lo, i < count)
    tl.store(up + i, hi, i < count)


@tr.jit
def _binary(
    a, b, down, up, count: tl.constexpr, op: tl.constexpr, fp64: tl.constexpr, B: tl.constexpr
):
    i = tl.program_id(0) * B + tl.arange(0, B)
    x, y = tl.load(a + i, i < count, 0), tl.load(b + i, i < count, 1)
    if fp64:
        lo = tl.inline_asm_elementwise(
            op + ".rm.f64 $0, $1, $2;",
            constraints="=d,d,d",
            args=[x, y],
            dtype=tl.float64,
            is_pure=True,
            pack=1,
        )
        hi = tl.inline_asm_elementwise(
            op + ".rp.f64 $0, $1, $2;",
            constraints="=d,d,d",
            args=[x, y],
            dtype=tl.float64,
            is_pure=True,
            pack=1,
        )
    else:
        lo = tl.inline_asm_elementwise(
            op + ".rm.f32 $0, $1, $2;",
            constraints="=f,f,f",
            args=[x, y],
            dtype=tl.float32,
            is_pure=True,
            pack=1,
        )
        hi = tl.inline_asm_elementwise(
            op + ".rp.f32 $0, $1, $2;",
            constraints="=f,f,f",
            args=[x, y],
            dtype=tl.float32,
            is_pure=True,
            pack=1,
        )
    tl.store(down + i, lo, i < count)
    tl.store(up + i, hi, i < count)


@tr.jit
def _mulhi(a, b, out, count: tl.constexpr, B: tl.constexpr):
    i = tl.program_id(0) * B + tl.arange(0, B)
    x, y = tl.load(a + i, i < count, 0), tl.load(b + i, i < count, 0)
    z = tl.inline_asm_elementwise(
        "mul.hi.u64 $0, $1, $2;",
        constraints="=l,l,l",
        args=[x, y],
        dtype=tl.uint64,
        is_pure=True,
        pack=1,
    )
    tl.store(out + i, z, i < count)


def directed_cast(values):
    if values.dtype != torch.float64 or values.device.type != "cuda" or values.ndim != 1:
        raise ValueError("one contiguous binary64 CUDA vector required")
    values = values.contiguous()
    lower, upper = [torch.empty_like(values, dtype=torch.float32) for _ in range(2)]
    _cast[(tr.cdiv(values.numel(), 256),)](values, lower, upper, values.numel(), 256)
    return lower, upper


def directed_binary(a, b, op):
    if (
        op not in ("add", "mul", "div")
        or a.dtype not in (torch.float32, torch.float64)
        or a.dtype != b.dtype
        or a.device.type != "cuda"
        or a.device != b.device
        or a.shape != b.shape
        or a.ndim != 1
    ):
        raise ValueError("matching binary32/64 CUDA vectors and supported operation required")
    a, b = a.contiguous(), b.contiguous()
    lower, upper = torch.empty_like(a), torch.empty_like(a)
    _binary[(tr.cdiv(a.numel(), 256),)](
        a, b, lower, upper, a.numel(), op, a.dtype == torch.float64, 256
    )
    return lower, upper


def multiply_high(a, b):
    if (
        a.dtype != torch.uint64
        or b.dtype != a.dtype
        or a.device != b.device
        or a.device.type != "cuda"
        or a.shape != b.shape
        or a.ndim != 1
    ):
        raise ValueError("matching uint64 CUDA vectors required")
    out = torch.empty_like(a)
    _mulhi[(tr.cdiv(a.numel(), 256),)](a.contiguous(), b.contiguous(), out, a.numel(), 256)
    return out
