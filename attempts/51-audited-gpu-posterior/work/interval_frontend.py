"""Opt-in shared classical interval inside pass; original binary64 weights."""

from fractions import Fraction as F

import torch
import triton as tr
import triton.language as tl


@tr.jit
def _add_lo(x, y):
    return tl.inline_asm_elementwise(
        "add.rm.f32 $0, $1, $2;",
        constraints="=f,f,f",
        args=[x, y],
        dtype=tl.float32,
        is_pure=True,
        pack=1,
    )


@tr.jit
def _add_hi(x, y):
    return tl.inline_asm_elementwise(
        "add.rp.f32 $0, $1, $2;",
        constraints="=f,f,f",
        args=[x, y],
        dtype=tl.float32,
        is_pure=True,
        pack=1,
    )


@tr.jit
def _mul_lo(x, y):
    return tl.inline_asm_elementwise(
        "mul.rm.f32 $0, $1, $2;",
        constraints="=f,f,f",
        args=[x, y],
        dtype=tl.float32,
        is_pure=True,
        pack=1,
    )


@tr.jit
def _mul_hi(x, y):
    return tl.inline_asm_elementwise(
        "mul.rp.f32 $0, $1, $2;",
        constraints="=f,f,f",
        args=[x, y],
        dtype=tl.float32,
        is_pure=True,
        pack=1,
    )


@tr.jit
def _class_sums(
    weights, members, pointer, lower, upper, V: tl.constexpr, C: tl.constexpr, B: tl.constexpr
):
    p, c = tl.program_id(0), tl.program_id(1)
    start, end = tl.load(pointer + c), tl.load(pointer + c + 1)
    lanes = tl.arange(0, B)
    lo, hi = tl.full((B,), 0, tl.float32), tl.full((B,), 0, tl.float32)
    for offset in range(start, end, B):
        valid = offset + lanes < end
        ids = tl.load(members + offset + lanes, valid, 0)
        x = tl.load(weights + p * V + ids, valid, 0)
        a = tl.inline_asm_elementwise(
            "cvt.rm.f32.f64 $0, $1;",
            constraints="=f,d",
            args=[x],
            dtype=tl.float32,
            is_pure=True,
            pack=1,
        )
        b = tl.inline_asm_elementwise(
            "cvt.rp.f32.f64 $0, $1;",
            constraints="=f,d",
            args=[x],
            dtype=tl.float32,
            is_pure=True,
            pack=1,
        )
        lo, hi = _add_lo(lo, a), _add_hi(hi, b)
    tl.store(lower + p * C + c, tl.reduce(lo, 0, _add_lo))
    tl.store(upper + p * C + c, tl.reduce(hi, 0, _add_hi))


@tr.jit
def _layer(
    class_lo,
    class_hi,
    outgoing,
    target,
    label_pointer,
    labels,
    next_lo,
    next_hi,
    lower,
    upper,
    p: tl.constexpr,
    C: tl.constexpr,
    B: tl.constexpr,
):
    state = tl.program_id(0)
    start, end = tl.load(outgoing + state), tl.load(outgoing + state + 1)
    lo, hi = tl.full((), 0, tl.float32), tl.full((), 0, tl.float32)
    lanes = tl.arange(0, B)
    for e in range(start, end):
        a, b = tl.load(label_pointer + e), tl.load(label_pointer + e + 1)
        el, eh = tl.full((B,), 0, tl.float32), tl.full((B,), 0, tl.float32)
        for offset in range(a, b, B):
            valid = offset + lanes < b
            cid = tl.load(labels + offset + lanes, valid, 0)
            el = _add_lo(el, tl.load(class_lo + p * C + cid, valid, 0))
            eh = _add_hi(eh, tl.load(class_hi + p * C + cid, valid, 0))
        el, eh = tl.reduce(el, 0, _add_lo), tl.reduce(eh, 0, _add_hi)
        dst = tl.load(target + e)
        lo = _add_lo(lo, _mul_lo(el, tl.load(next_lo + dst)))
        hi = _add_hi(hi, _mul_hi(eh, tl.load(next_hi + dst)))
    tl.store(lower + state, lo)
    tl.store(upper + state, hi)


@tr.jit
def _scale(raw_lo, raw_hi, scale, lower, upper, N: tl.constexpr, B: tl.constexpr):
    i = tl.program_id(0) * B + tl.arange(0, B)
    s = tl.load(scale)
    lo, hi = tl.load(raw_lo + i, i < N, 0), tl.load(raw_hi + i, i < N, 0)
    a = tl.inline_asm_elementwise(
        "div.rm.f32 $0, $1, $2;",
        constraints="=f,f,f",
        args=[lo, s],
        dtype=tl.float32,
        is_pure=True,
        pack=1,
    )
    b = tl.inline_asm_elementwise(
        "div.rp.f32 $0, $1, $2;",
        constraints="=f,f,f",
        args=[hi, s],
        dtype=tl.float32,
        is_pure=True,
        pack=1,
    )
    tl.store(lower + i, a, i < N)
    tl.store(upper + i, b, i < N)


class IntervalDAG:
    """Original IDs -> disjoint global classes -> disjoint deterministic arcs.

    Each layer is a sequence of nodes; a node has (target, class_ids) edges.
    Graph correctness relative to a grammar is a separate compiler obligation.
    """

    def __init__(self, classes, layers, accepting, *, device="cuda"):
        self.classes = tuple(tuple(c) for c in classes)
        self.layers = tuple(tuple(tuple(edges) for edges in layer) for layer in layers)
        self.accepting = tuple(bool(a) for a in accepting)
        self.device = torch.device(device)
        if self.device.type == "cuda" and self.device.index is None:
            self.device = torch.device("cuda", torch.cuda.current_device())
        flat = [t for c in self.classes for t in c]
        if (
            self.device.type != "cuda"
            or not self.classes
            or any(not c for c in self.classes)
            or sorted(flat) != list(range(len(flat)))
            or not self.layers
            or len(self.layers[0]) != 1
            or not self.accepting
        ):
            raise ValueError("complete original-ID partition, CUDA and one layered root required")
        self.vocabulary = len(flat)
        self.members = torch.tensor(flat, dtype=torch.long, device=device)
        ptr = [0]
        for c in self.classes:
            ptr.append(ptr[-1] + len(c))
        self.pointer = torch.tensor(ptr, dtype=torch.long, device=device)
        self.graphs = []
        for p, layer in enumerate(self.layers):
            if not layer:
                raise ValueError("empty node layer")
            bound = len(self.layers[p + 1]) if p + 1 < len(self.layers) else len(self.accepting)
            out, targets, label_ptr, labels = [0], [], [0], []
            for edges in layer:
                seen = set()
                for target, cids in edges:
                    if not 0 <= target < bound or not cids:
                        raise ValueError("bad edge target/empty classes")
                    for cid in cids:
                        if not 0 <= cid < len(self.classes) or cid in seen:
                            raise ValueError("class has no unique original-word state trace")
                        seen.add(cid)
                    targets.append(target)
                    labels.extend(cids)
                    label_ptr.append(len(labels))
                out.append(len(targets))
            self.graphs.append(
                tuple(
                    torch.tensor(a, dtype=torch.long, device=device)
                    for a in (out, targets, label_ptr, labels)
                )
            )

    @torch.no_grad()
    def query(self, weights):
        if (
            weights.dtype != torch.float64
            or weights.device != self.device
            or weights.shape != (len(self.layers), self.vocabulary)
        ):
            raise ValueError("original binary64 CUDA head shape/device required")
        if (
            not bool(torch.isfinite(weights).all())
            or bool((weights < 0).any())
            or bool((weights > 1).any())
        ):
            raise ValueError("finite original probability weights in[0,1] required")
        weights = weights.contiguous()
        shape = (len(self.layers), len(self.classes))
        class_lo, class_hi = [
            torch.empty(shape, dtype=torch.float32, device=self.device) for _ in range(2)
        ]
        _class_sums[shape](
            weights,
            self.members,
            self.pointer,
            class_lo,
            class_hi,
            self.vocabulary,
            len(self.classes),
            256,
        )
        next_lo = torch.tensor(self.accepting, dtype=torch.float32, device=self.device)
        next_hi = next_lo.clone()
        lowers, uppers, scales = [next_lo], [next_hi], []
        for p in range(len(self.layers) - 1, -1, -1):
            n = len(self.layers[p])
            raw_lo, raw_hi, lower, upper = [
                torch.empty(n, dtype=torch.float32, device=self.device) for _ in range(4)
            ]
            _layer[(n,)](
                class_lo,
                class_hi,
                *self.graphs[p],
                next_lo,
                next_hi,
                raw_lo,
                raw_hi,
                p,
                len(self.classes),
                64,
            )
            scale = raw_hi.max()
            scale = torch.where(scale > 0, scale, torch.ones_like(scale))
            _scale[(tr.cdiv(n, 256),)](raw_lo, raw_hi, scale, lower, upper, n, 256)
            scales.append(scale)
            lowers.append(lower)
            uppers.append(upper)
            next_lo, next_hi = lower, upper
        # All synchronization/materialization must be CHARGED in any later cost study.
        scale_values = torch.stack(scales).cpu().tolist()
        root_lo, root_hi = next_lo.item(), next_hi.item()
        if any(
            not 0 < s < float("inf") for s in scale_values
        ) or not 0 <= root_lo <= root_hi < float("inf"):
            raise ValueError("nonfinite/invalid directed enclosure; REFUSE, never clamp")
        factor = F(1)
        for value in scale_values:
            factor *= F(value)
        return dict(
            lower=F(root_lo) * factor,
            upper=F(root_hi) * factor,
            scaled_lower=root_lo,
            scaled_upper=root_hi,
            scales=tuple(scale_values),
            class_lower=class_lo,
            class_upper=class_hi,
            beta_lower=tuple(reversed(lowers)),
            beta_upper=tuple(reversed(uppers)),
        )
