"""Opt-in classical static-error GPU frontend; numerical preflight only."""

import hashlib
from fractions import Fraction as F

import torch
import triton as tr
import triton.language as tl

from .frozen_control.interval_frontend import IntervalDAG, _mul_hi, _mul_lo
from .reference import Format


@tr.jit
def _add(x, y):
    return tl.inline_asm_elementwise(
        "add.rn.f32 $0, $1, $2;", "=f,f,f", [x, y], dtype=tl.float32, is_pure=True, pack=1
    )


@tr.jit
def _mul(x, y):
    return tl.inline_asm_elementwise(
        "mul.rn.f32 $0, $1, $2;", "=f,f,f", [x, y], dtype=tl.float32, is_pure=True, pack=1
    )


@tr.jit
def _normal_or_zero(x):
    return (x == 0) | ((x >= 1.1754943508222875e-38) & (x <= 3.4028234663852886e38))


@tr.jit
def _classes(
    weights,
    members,
    pointer,
    estimate,
    lower,
    upper,
    flag,
    factors,
    V: tl.constexpr,
    C: tl.constexpr,
    B: tl.constexpr,
):
    p, c, lane = tl.program_id(0), tl.program_id(1), tl.arange(0, B)
    start, end = tl.load(pointer + c), tl.load(pointer + c + 1)
    accumulator = tl.full((B,), 0, tl.float32)
    bad = tl.full((B,), False, tl.int1)
    for offset in range(start, end, B):
        valid = offset + lane < end
        token = tl.load(members + offset + lane, valid, 0)
        original = tl.load(weights + p * V + token, valid, 0)
        value = tl.inline_asm_elementwise(
            "cvt.rn.f32.f64 $0, $1;", "=f,d", [original], dtype=tl.float32, is_pure=True, pack=1
        )
        bad = bad | ~_normal_or_zero(value) | ((original > 0) & (value == 0))
        accumulator = _add(accumulator, value)
    value = tl.reduce(accumulator, 0, _add)
    invalid = tl.sum(bad.to(tl.int32), 0) > 0
    invalid = invalid | ~_normal_or_zero(value)
    if invalid:
        tl.atomic_or(flag, 1)
    tl.store(estimate + p * C + c, value)
    tl.store(lower + p * C + c, _mul_lo(value, tl.load(factors)))
    tl.store(upper + p * C + c, _mul_hi(value, tl.load(factors + 1)))


@tr.jit
def _layer(
    class_estimate,
    outgoing,
    target,
    label_pointer,
    labels,
    next_estimate,
    raw,
    flag,
    p: tl.constexpr,
    C: tl.constexpr,
    B: tl.constexpr,
):
    state, lane = tl.program_id(0), tl.arange(0, B)
    start, end = tl.load(outgoing + state), tl.load(outgoing + state + 1)
    accumulator = tl.full((), 0, tl.float32)
    bad = tl.full((), False, tl.int1)
    for edge in range(start, end):
        a, b = tl.load(label_pointer + edge), tl.load(label_pointer + edge + 1)
        terms = tl.full((B,), 0, tl.float32)
        for offset in range(a, b, B):
            valid = offset + lane < b
            cid = tl.load(labels + offset + lane, valid, 0)
            terms = _add(terms, tl.load(class_estimate + p * C + cid, valid, 0))
        edge_weight = tl.reduce(terms, 0, _add)
        dst = tl.load(target + edge)
        suffix = tl.load(next_estimate + dst)
        value = _mul(edge_weight, suffix)
        bad = bad | ~_normal_or_zero(edge_weight) | ~_normal_or_zero(value)
        bad = bad | ((edge_weight > 0) & (suffix > 0) & (value == 0))
        accumulator = _add(accumulator, value)
    bad = bad | ~_normal_or_zero(accumulator)
    if bad:
        tl.atomic_or(flag, 1)
    tl.store(raw + state, accumulator)


@tr.jit
def _rescale(raw, scale, estimate, lower, upper, flag, factors, N: tl.constexpr, B: tl.constexpr):
    lane = tl.program_id(0) * B + tl.arange(0, B)
    valid = lane < N
    value, divisor = tl.load(raw + lane, valid, 0), tl.load(scale)
    scaled = tl.inline_asm_elementwise(
        "div.rn.f32 $0, $1, $2;", "=f,f,f", [value, divisor], dtype=tl.float32, is_pure=True, pack=1
    )
    bad = valid & (~_normal_or_zero(scaled) | ((value > 0) & (scaled == 0)))
    if tl.sum(bad.to(tl.int32), 0) > 0:
        tl.atomic_or(flag, 1)
    tl.store(estimate + lane, scaled, valid)
    tl.store(lower + lane, _mul_lo(scaled, tl.load(factors)), valid)
    tl.store(upper + lane, _mul_hi(scaled, tl.load(factors + 1)), valid)


def multipliers(budget):
    fmt = Format(24, -126, 127)
    epsilon = fmt.epsilon
    return tuple(
        float(fmt.round(value, direction))
        for value, direction in (
            (1 / (1 + epsilon) ** budget, "down"),
            (1 / (1 - epsilon) ** budget, "up"),
        )
    )


class StaticDAG(IntervalDAG):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.class_budget = 1 + tr.cdiv(max(map(len, self.classes)), 256) + 8
        self.class_factors = torch.tensor(
            multipliers(self.class_budget), dtype=torch.float32, device=self.device
        )
        following, budgets = 0, []
        for layer in reversed(self.layers):
            degree = max(map(len, layer))
            label_count = max((len(cids) for edges in layer for _, cids in edges), default=0)
            label_budget = tr.cdiv(label_count, 64) + 6
            following += self.class_budget + label_budget + 1 + degree + 1
            budgets.append(following)
        self.budgets = tuple(reversed(budgets))
        self.factors = tuple(
            torch.tensor(multipliers(k), dtype=torch.float32, device=self.device)
            for k in self.budgets
        )
        self.last_fast_status = None
        self.capture_ptx = False
        self.ptx = {}

    def _record(self, compiled):
        if self.capture_ptx:
            content = compiled.asm["ptx"]
            self.ptx[hashlib.sha256(content.encode()).hexdigest()] = content

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
        shape = (len(self.layers), len(self.classes))
        estimate, class_lo, class_hi = [
            torch.empty(shape, dtype=torch.float32, device=self.device) for _ in range(3)
        ]
        flag = torch.zeros((), dtype=torch.int32, device=self.device)
        compiled = _classes[shape](
            weights.contiguous(),
            self.members,
            self.pointer,
            estimate,
            class_lo,
            class_hi,
            flag,
            self.class_factors,
            self.vocabulary,
            len(self.classes),
            256,
        )
        self._record(compiled)
        next_estimate = torch.tensor(self.accepting, dtype=torch.float32, device=self.device)
        estimates, lowers, uppers, scales = [next_estimate], [next_estimate], [next_estimate], []
        for p in range(len(self.layers) - 1, -1, -1):
            n = len(self.layers[p])
            raw, current, lower, upper = [
                torch.empty(n, dtype=torch.float32, device=self.device) for _ in range(4)
            ]
            compiled = _layer[(n,)](
                estimate, *self.graphs[p], next_estimate, raw, flag, p, len(self.classes), 64
            )
            self._record(compiled)
            divisor = raw.max()
            divisor = torch.where(divisor > 0, divisor, torch.ones_like(divisor))
            compiled = _rescale[(tr.cdiv(n, 256),)](
                raw, divisor, current, lower, upper, flag, self.factors[p], n, 256
            )
            self._record(compiled)
            estimates.append(current)
            lowers.append(lower)
            uppers.append(upper)
            scales.append(divisor)
            next_estimate = current
        if flag.item():
            self.last_fast_status = "GUARD_FALLBACK"
            return super().query(weights)
        self.last_fast_status = "STATIC_CERTIFIED"
        scale_values = torch.stack(scales).cpu().tolist()
        factor = F(1)
        for value in scale_values:
            factor *= F(value)
        root_lo, root_hi = lowers[-1].item(), uppers[-1].item()
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
            class_estimate=estimate,
            beta_estimate=tuple(reversed(estimates)),
        )
