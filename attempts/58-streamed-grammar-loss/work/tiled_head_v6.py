"""Explicit finite-domain entry point; unchanged V3 kernels, fixed tile grid.

Caller guarantees valid immutable finite-domain inputs. This does not provide
the old guarded API's input-refusal contract. No new differentiation method.
"""

import torch
import triton

from .gpu_head import _backward, _merge, _project, _targets


def prepare(mapping, device, tile):
    bn, bv = tile
    if tile not in ((16, 32), (32, 64), (64, 64), (64, 128)):
        raise ValueError("unregistered predeclared tile")
    panels, classes, bounds = [], [], []
    for cls in range(max(mapping) + 1):
        members = [v for v, c in enumerate(mapping) if c == cls]
        lo = len(panels)
        for start in range(0, len(members), bv):
            ids = members[start : start + bv]
            panels.append(ids + [-1] * (bv - len(ids)))
            classes.append(cls)
        bounds.append((lo, len(panels)))
    return {
        "ids": torch.tensor(panels, device=device, dtype=torch.int32),
        "class": torch.tensor(classes, device=device, dtype=torch.int32),
        "bounds": torch.tensor(bounds, device=device, dtype=torch.int32),
        "C": len(bounds),
        "BN": bn,
        "BV": bv,
        "block": triton.next_power_of_2(max(hi - lo for lo, hi in bounds)),
    }


class _Tiled(torch.autograd.Function):
    @staticmethod
    def forward(ctx, h, w, b, t, meta):
        n, d = h.shape
        p, c, bn, bv = len(meta["class"]), meta["C"], meta["BN"], meta["BV"]
        part = h.new_empty((n, p))
        z, target = h.new_empty((n, c)), h.new_empty((n,))
        _project[(triton.cdiv(n, bn), p)](
            h, w, b, meta["ids"], part, n, d, p, bn, bv, 32, num_warps=4
        )
        _merge[(n, c)](part, meta["bounds"], z, p, c, meta["block"], num_warps=4)
        _targets[(n,)](h, w, b, t, target, d, triton.next_power_of_2(d), num_warps=4)
        ctx.save_for_backward(h, w, b, t, z)
        ctx.meta = meta
        return z, target

    @staticmethod
    def backward(ctx, dz, dt):
        h, w, b, t, z = ctx.saved_tensors
        meta = ctx.meta
        n, d = h.shape
        dh, dw, db = torch.zeros_like(h), torch.zeros_like(w), torch.zeros_like(b)
        _backward[(triton.cdiv(n, meta["BN"]), len(meta["class"]))](
            h,
            w,
            b,
            t,
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
            meta["BN"],
            meta["BV"],
            32,
            num_warps=4,
        )
        return dh, dw, db, None, None


def finite_domain_head(h, w, b, targets, meta):
    return _Tiled.apply(h, w, b, targets, meta)
