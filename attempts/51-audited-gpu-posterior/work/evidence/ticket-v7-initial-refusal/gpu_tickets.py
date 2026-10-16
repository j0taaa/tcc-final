"""Upward count construction and actual finite integer-CDF GPU proposals (opt-in)."""

import triton as tr
import triton.language as tl


@tr.jit
def _counts(numerator, denominator, valid):
    den = tl.where(denominator > 0, denominator, 1.0).to(tl.float64)
    ratio = tl.inline_asm_elementwise(
        "div.rp.f64 $0, $1, $2;",
        constraints="=d,d,d",
        args=[numerator.to(tl.float64), den],
        dtype=tl.float64,
        is_pure=True,
        pack=1,
    )
    scaled = tl.inline_asm_elementwise(
        "mul.rp.f64 $0, $1, $2;",
        constraints="=d,d,d",
        args=[ratio, tl.full((), 2.0**40, tl.float64)],
        dtype=tl.float64,
        is_pure=True,
        pack=1,
    )
    good = (scaled >= 0) & (scaled <= 2.0**41) & ((denominator > 0) | (numerator == 0))
    safe = tl.where(good, scaled, 1.0)
    integer = tl.inline_asm_elementwise(
        "cvt.rpi.s64.f64 $0, $1;",
        constraints="=l,d",
        args=[safe],
        dtype=tl.int64,
        is_pure=True,
        pack=1,
    )
    integer = tl.where(valid, tl.maximum(integer, 1), 0)
    total = tl.sum(integer, 0)
    bad = (tl.sum((valid & ~good).to(tl.int32), 0) > 0) | (total > 2**41)
    return tl.cumsum(integer, 0), total, bad


@tr.jit
def token_counts(
    weights,
    members,
    pointer,
    mass,
    cdf,
    totals,
    bad,
    V: tl.constexpr,
    C: tl.constexpr,
    B: tl.constexpr,
):
    p, c, lane = tl.program_id(0), tl.program_id(1), tl.arange(0, B)
    start, end = tl.load(pointer + c), tl.load(pointer + c + 1)
    valid = start + lane < end
    token = tl.load(members + start + lane, valid, 0)
    original = tl.load(weights + p * V + token, valid, 0)
    upper = tl.inline_asm_elementwise(
        "cvt.rp.f32.f64 $0, $1;",
        constraints="=f,d",
        args=[original],
        dtype=tl.float32,
        is_pure=True,
        pack=1,
    )
    parent = tl.load(mass + p * C + c)
    prefixes, total, invalid = _counts(upper.to(tl.float64), parent.to(tl.float64), valid)
    tl.store(cdf + p * V + start + lane, prefixes, valid)
    tl.store(totals + p * C + c, total)
    tl.store(bad + p * C + c, invalid)


@tr.jit
def block_counts(
    mass, positions, pointer, labels, edge_mass, cdf, totals, bad, C: tl.constexpr, B: tl.constexpr
):
    e, lane = tl.program_id(0), tl.arange(0, B)
    p = tl.load(positions + e)
    start, end = tl.load(pointer + e), tl.load(pointer + e + 1)
    valid = start + lane < end
    c = tl.load(labels + start + lane, valid, 0)
    value = tl.load(mass + p * C + c, valid, 0)
    parent = tl.load(edge_mass + e)
    prefixes, total, invalid = _counts(value.to(tl.float64), parent.to(tl.float64), valid)
    tl.store(cdf + start + lane, prefixes, valid)
    tl.store(totals + e, total)
    tl.store(bad + e, invalid)


@tr.jit
def edge_counts(
    edge_mass, outgoing, targets, positions, h, scales, cdf, totals, bad, B: tl.constexpr
):
    s, lane = tl.program_id(0), tl.arange(0, B)
    p = tl.load(positions + s)
    start, end = tl.load(outgoing + s), tl.load(outgoing + s + 1)
    valid = start + lane < end
    dst = tl.load(targets + start + lane, valid, 0)
    mass = tl.load(edge_mass + start + lane, valid, 0)
    child = tl.load(h + dst, valid, 0)
    # Two binary32 operands: product is exact in binary64 (48 significant bits).
    numerator = mass.to(tl.float64) * child.to(tl.float64)
    parent = tl.load(h + s).to(tl.float64) * tl.load(scales + p).to(tl.float64)
    prefixes, total, invalid = _counts(numerator, parent, valid)
    tl.store(cdf + start + lane, prefixes, valid)
    tl.store(totals + s, total)
    tl.store(bad + s, invalid)


@tr.jit
def maximum_totals(
    node_offsets, edge_offsets, edge_a, block_a, token_a, out, C: tl.constexpr, B: tl.constexpr
):
    p, lane = tl.program_id(0), tl.arange(0, B)
    start, end = tl.load(node_offsets + p), tl.load(node_offsets + p + 1)
    emax = tl.full((B,), 0, tl.int64)
    for j in range(start, end, B):
        emax = tl.maximum(emax, tl.load(edge_a + j + lane, j + lane < end, 0))
    start, end = tl.load(edge_offsets + p), tl.load(edge_offsets + p + 1)
    bmax = tl.full((B,), 0, tl.int64)
    for j in range(start, end, B):
        bmax = tl.maximum(bmax, tl.load(block_a + j + lane, j + lane < end, 0))
    tmax = tl.full((B,), 0, tl.int64)
    for j in range(0, C, B):
        tmax = tl.maximum(tmax, tl.load(token_a + p * C + j + lane, j + lane < C, 0))
    tl.store(out + p * 3, tl.max(emax, 0))
    tl.store(out + p * 3 + 1, tl.max(bmax, 0))
    tl.store(out + p * 3 + 2, tl.max(tmax, 0))


@tr.jit
def _choose(cdf, start, end, raw):
    total = tl.load(cdf + end - 1)
    ticket = tl.inline_asm_elementwise(
        "mul.hi.u64 $0, $1, $2;",
        constraints="=l,l,l",
        args=[raw, total.to(tl.uint64)],
        dtype=tl.uint64,
        is_pure=True,
        pack=1,
    ).to(tl.int64)
    lo, hi = start, end
    while lo < hi:
        middle = (lo + hi) // 2
        before = tl.load(cdf + middle) <= ticket
        lo, hi = tl.where(before, middle + 1, lo), tl.where(before, hi, middle)
    left = tl.load(cdf + lo - 1, lo > start, 0)
    right = tl.load(cdf + lo)
    return lo, total, left, right


@tr.jit
def _random64(source, offset):
    low = tl.load(source + offset).to(tl.uint64)
    high = tl.load(source + offset + 1).to(tl.uint64)
    return low | (high << 32)


@tr.jit
def proposal_walk(
    weights,
    outgoing,
    targets,
    block_pointer,
    blocks,
    token_pointer,
    tokens,
    edge_cdf,
    block_cdf,
    token_cdf,
    source,
    words,
    selected_weights,
    packet,
    final_mask,
    valid_terminal,
    V: tl.constexpr,
    length: tl.constexpr,
):
    trial = tl.program_id(0)
    state = tl.full((), 0, tl.int64)
    for p in range(length):
        start, end = tl.load(outgoing + state), tl.load(outgoing + state + 1)
        r = _random64(source, (trial * length * 3 + p * 3) * 2)
        e, a, left, right = _choose(edge_cdf, start, end, r)
        offset = (trial * length * 3 + p * 3) * 3
        tl.store(packet + offset, a)
        tl.store(packet + offset + 1, left)
        tl.store(packet + offset + 2, right)
        start, end = tl.load(block_pointer + e), tl.load(block_pointer + e + 1)
        r = _random64(source, (trial * length * 3 + p * 3 + 1) * 2)
        b, a, left, right = _choose(block_cdf, start, end, r)
        tl.store(packet + offset + 3, a)
        tl.store(packet + offset + 4, left)
        tl.store(packet + offset + 5, right)
        cid = tl.load(blocks + b)
        start, end = tl.load(token_pointer + cid), tl.load(token_pointer + cid + 1)
        r = _random64(source, (trial * length * 3 + p * 3 + 2) * 2)
        j, a, left, right = _choose(token_cdf + p * V, start, end, r)
        tl.store(packet + offset + 6, a)
        tl.store(packet + offset + 7, left)
        tl.store(packet + offset + 8, right)
        token = tl.load(tokens + j)
        tl.store(words + trial * length + p, token)
        tl.store(selected_weights + trial * length + p, tl.load(weights + p * V + token))
        state = tl.load(targets + e)

    tl.store(valid_terminal + trial, tl.load(final_mask + state))
