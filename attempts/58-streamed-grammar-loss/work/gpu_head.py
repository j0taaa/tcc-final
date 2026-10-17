"""Opt-in V3 FP32 correctness kernel; no filtered gradients or dense NV buffer.

CCE/recomputed linear-LSE is the direct template. This unoptimized grouped
specialization has no measured systems advantage or mixed-precision claim.
"""

import torch
import triton
import triton.language as tl


@triton.jit
def _project(
    H,
    W,
    Bias,
    IDs,
    Part,
    N: tl.constexpr,
    D: tl.constexpr,
    P: tl.constexpr,
    BN: tl.constexpr,
    BV: tl.constexpr,
    BK: tl.constexpr,
):
    row = tl.program_id(0) * BN + tl.arange(0, BN)
    panel = tl.program_id(1)
    v = tl.load(IDs + panel * BV + tl.arange(0, BV))
    k = tl.arange(0, BK)
    logits = tl.zeros((BN, BV), tl.float32)
    for base in range(tl.cdiv(D, BK)):
        d = base * BK + k
        h = tl.load(H + row[:, None] * D + d[None, :], (row[:, None] < N) & (d[None, :] < D), 0)
        w = tl.load(W + v[None, :] * D + d[:, None], (v[None, :] >= 0) & (d[:, None] < D), 0)
        logits = tl.dot(h, w, logits, input_precision="ieee")
    b = tl.load(Bias + v, v >= 0, 0)
    logits = tl.where(v[None, :] >= 0, logits + b[None, :], -float("inf"))
    maximum = tl.max(logits, 1)
    safe = tl.where(maximum > -float("inf"), maximum, 0)
    lse = safe + tl.log(tl.sum(tl.exp(logits - safe[:, None]), 1))
    tl.store(Part + row * P + panel, lse, row < N)


@triton.jit
def _merge(Part, Bounds, Z, P: tl.constexpr, C: tl.constexpr, BLOCK: tl.constexpr):
    row, cls = tl.program_id(0), tl.program_id(1)
    lo, hi = tl.load(Bounds + cls * 2), tl.load(Bounds + cls * 2 + 1)
    idx = lo + tl.arange(0, BLOCK)
    values = tl.load(Part + row * P + idx, idx < hi, -float("inf"))
    maximum = tl.max(values, 0)
    safe = tl.where(maximum > -float("inf"), maximum, 0)
    value = safe + tl.log(tl.sum(tl.exp(values - safe), 0))
    tl.store(Z + row * C + cls, value)


@triton.jit
def _targets(H, W, Bias, Targets, Out, D: tl.constexpr, BLOCK: tl.constexpr):
    row = tl.program_id(0)
    target = tl.load(Targets + row)
    d = tl.arange(0, BLOCK)
    h = tl.load(H + row * D + d, d < D, 0)
    w = tl.load(W + target * D + d, d < D, 0)
    tl.store(Out + row, tl.sum(h * w, 0) + tl.load(Bias + target))


@triton.jit
def _backward(
    H,
    W,
    Bias,
    Targets,
    IDs,
    PanelClass,
    Z,
    DZ,
    DT,
    DH,
    DW,
    DB,
    N: tl.constexpr,
    D: tl.constexpr,
    C: tl.constexpr,
    BN: tl.constexpr,
    BV: tl.constexpr,
    BK: tl.constexpr,
):
    row = tl.program_id(0) * BN + tl.arange(0, BN)
    panel = tl.program_id(1)
    v = tl.load(IDs + panel * BV + tl.arange(0, BV))
    cls = tl.load(PanelClass + panel)
    k = tl.arange(0, BK)
    logits = tl.zeros((BN, BV), tl.float32)
    for base in range(tl.cdiv(D, BK)):
        d = base * BK + k
        h = tl.load(H + row[:, None] * D + d[None, :], (row[:, None] < N) & (d[None, :] < D), 0)
        w = tl.load(W + v[None, :] * D + d[:, None], (v[None, :] >= 0) & (d[:, None] < D), 0)
        logits = tl.dot(h, w, logits, input_precision="ieee")
    b = tl.load(Bias + v, v >= 0, 0)
    logits = tl.where(v[None, :] >= 0, logits + b[None, :], -float("inf"))
    norm = tl.load(Z + row * C + cls, row < N, 0)
    safe = tl.where(norm > -float("inf"), norm, 0)
    dz = tl.load(DZ + row * C + cls, row < N, 0)
    dt = tl.load(DT + row, row < N, 0)
    target = tl.load(Targets + row, row < N, -2)
    g = dz[:, None] * tl.exp(logits - safe[:, None])
    g += tl.where(v[None, :] == target[:, None], dt[:, None], 0)
    for base in range(tl.cdiv(D, BK)):
        d = base * BK + k
        h = tl.load(H + row[:, None] * D + d[None, :], (row[:, None] < N) & (d[None, :] < D), 0)
        w = tl.load(W + v[:, None] * D + d[None, :], (v[:, None] >= 0) & (d[None, :] < D), 0)
        dh = tl.dot(g, w, input_precision="ieee")
        dw = tl.dot(tl.trans(g), h, input_precision="ieee")
        tl.atomic_add(DH + row[:, None] * D + d[None, :], dh, (row[:, None] < N) & (d[None, :] < D))
        tl.atomic_add(DW + v[:, None] * D + d[None, :], dw, (v[:, None] >= 0) & (d[None, :] < D))
    tl.atomic_add(DB + v, tl.sum(g, 0), v >= 0)


def metadata(mapping, device):
    if not mapping or sorted(set(mapping)) != list(range(max(mapping) + 1)):
        raise ValueError("nonempty contiguous class map required")
    panels, classes, bounds = [], [], []
    for cls in range(max(mapping) + 1):
        members = [v for v, c in enumerate(mapping) if c == cls]
        lo = len(panels)
        for start in range(0, len(members), 32):
            panel = members[start : start + 32]
            panels.append(panel + [-1] * (32 - len(panel)))
            classes.append(cls)
        bounds.append((lo, len(panels)))
    return {
        "ids": torch.tensor(panels, device=device, dtype=torch.int32),
        "class": torch.tensor(classes, device=device, dtype=torch.int32),
        "bounds": torch.tensor(bounds, device=device, dtype=torch.int32),
        "C": len(bounds),
        "V": len(mapping),
        "block": triton.next_power_of_2(max(hi - lo for lo, hi in bounds)),
    }


def grouped_gpu(h, w, b, targets, meta):
    n, d = h.shape
    if (
        n < 1
        or d < 1
        or h.dtype != torch.float32
        or w.dtype != h.dtype
        or b.dtype != h.dtype
        or h.device.type != "cuda"
        or w.shape != (meta["V"], d)
        or b.shape != (meta["V"],)
        or targets.shape != (n,)
        or not all(t.is_contiguous() for t in (h, w, b, targets))
        or not torch.isfinite(h).all()
        or not torch.isfinite(w).all()
        or torch.isnan(b).any()
        or torch.isposinf(b).any()
        or not torch.isfinite(b).any()
        or (targets < 0).any()
        or (targets >= len(w)).any()
    ):
        raise ValueError("nonempty valid FP32 CUDA affine head/target required")

    class GroupedGPU(torch.autograd.Function):
        @staticmethod
        def forward(ctx, hh, ww, bb, tt):
            p, c = len(meta["class"]), meta["C"]
            partial = hh.new_empty((n, p))
            z, target = hh.new_empty((n, c)), hh.new_empty((n,))
            _project[(triton.cdiv(n, 16), p)](
                hh, ww, bb, meta["ids"], partial, n, d, p, 16, 32, 32, num_warps=4
            )
            _merge[(n, c)](partial, meta["bounds"], z, p, c, meta["block"], num_warps=4)
            _targets[(n,)](hh, ww, bb, tt, target, d, triton.next_power_of_2(d), num_warps=4)
            ctx.save_for_backward(hh, ww, bb, tt, z)
            return z, target

        @staticmethod
        def backward(ctx, dz, dt):
            hh, ww, bb, tt, z = ctx.saved_tensors
            dh, dw, db = torch.zeros_like(hh), torch.zeros_like(ww), torch.zeros_like(bb)
            _backward[(triton.cdiv(n, 16), len(meta["class"]))](
                hh,
                ww,
                bb,
                tt,
                meta["ids"],
                meta["class"],
                z,
                dz.contiguous(),
                dt.contiguous(),
                dh,
                dw,
                db,
                n,
                d,
                meta["C"],
                16,
                32,
                32,
                num_warps=4,
            )
            return dh, dw, db, None

    return GroupedGPU.apply(h, w, b, targets)
