"""Mandatory classical GPU interval control, with exact retained-prefix fallback."""

import torch
import triton as tr
import triton.language as tl

from .exact_control import ExactDAG
from .gpu_cdf import interval_index
from .interval_frontend import IntervalDAG, _add_hi, _add_lo, _mul_hi, _mul_lo


def split_blocks(classes, layers, size=1024):
    if type(size) is not int or size < 1:
        raise ValueError("positive deterministic block size required")
    blocks, replacement = [], []
    for members in classes:
        ids = []
        for start in range(0, len(members), size):
            ids.append(len(blocks))
            blocks.append(tuple(members[start : start + size]))
        replacement.append(tuple(ids))
    expanded = tuple(
        tuple(
            tuple((dst, tuple(b for c in cids for b in replacement[c])) for dst, cids in edges)
            for edges in layer
        )
        for layer in layers
    )
    return tuple(blocks), expanded


@tr.jit
def _edge_mass(
    class_lo,
    class_hi,
    positions,
    pointer,
    labels,
    edge_lo,
    edge_hi,
    C: tl.constexpr,
    B: tl.constexpr,
):
    e, lane = tl.program_id(0), tl.arange(0, B)
    p = tl.load(positions + e)
    start, end = tl.load(pointer + e), tl.load(pointer + e + 1)
    valid = start + lane < end
    c = tl.load(labels + start + lane, valid, 0)
    lo = tl.load(class_lo + p * C + c, valid, 0)
    hi = tl.load(class_hi + p * C + c, valid, 0)
    tl.store(edge_lo + e, tl.reduce(lo, 0, _add_lo))
    tl.store(edge_hi + e, tl.reduce(hi, 0, _add_hi))


@tr.jit
def _walk(
    weights,
    class_lo,
    class_hi,
    edge_lo,
    edge_hi,
    beta_lo,
    beta_hi,
    outgoing,
    target,
    edge_pointer,
    edge_labels,
    token_pointer,
    tokens,
    source,
    words,
    complete,
    V: tl.constexpr,
    C: tl.constexpr,
    length: tl.constexpr,
    bits: tl.constexpr,
    B: tl.constexpr,
):
    trial, lane = tl.program_id(0), tl.arange(0, B)
    state, active = tl.full((), 0, tl.int64), tl.full((), True, tl.int1)
    for p in range(length):
        if active:
            start, end = tl.load(outgoing + state), tl.load(outgoing + state + 1)
            valid = start + lane < end
            dst = tl.load(target + start + lane, valid, 0)
            lo = _mul_lo(
                tl.load(edge_lo + start + lane, valid, 0), tl.load(beta_lo + dst, valid, 0)
            )
            hi = _mul_hi(
                tl.load(edge_hi + start + lane, valid, 0), tl.load(beta_hi + dst, valid, 0)
            )
            raw = tl.load(source + trial * length * 3 + p * 3)
            chosen = interval_index(lo, hi, raw, bits, valid, B)
            active = chosen >= 0
            if active:
                e = start + chosen
                start, end = tl.load(edge_pointer + e), tl.load(edge_pointer + e + 1)
                valid = start + lane < end
                cids = tl.load(edge_labels + start + lane, valid, 0)
                lo = tl.load(class_lo + p * C + cids, valid, 0)
                hi = tl.load(class_hi + p * C + cids, valid, 0)
                raw = tl.load(source + trial * length * 3 + p * 3 + 1)
                chosen = interval_index(lo, hi, raw, bits, valid, B)
                active = chosen >= 0
                if active:
                    cid = tl.load(edge_labels + start + chosen)
                    start, end = tl.load(token_pointer + cid), tl.load(token_pointer + cid + 1)
                    valid = start + lane < end
                    token_ids = tl.load(tokens + start + lane, valid, 0)
                    weight = tl.load(weights + p * V + token_ids, valid, 0)
                    lo = tl.inline_asm_elementwise(
                        "cvt.rm.f32.f64 $0, $1;",
                        constraints="=f,d",
                        args=[weight],
                        dtype=tl.float32,
                        is_pure=True,
                        pack=1,
                    )
                    hi = tl.inline_asm_elementwise(
                        "cvt.rp.f32.f64 $0, $1;",
                        constraints="=f,d",
                        args=[weight],
                        dtype=tl.float32,
                        is_pure=True,
                        pack=1,
                    )
                    raw = tl.load(source + trial * length * 3 + p * 3 + 2)
                    chosen = interval_index(lo, hi, raw, bits, valid, B)
                    active = chosen >= 0
                    if active:
                        selected_token = tl.load(tokens + start + chosen)
                        tl.store(words + trial * length + p, selected_token)
                        state = tl.load(target + e)
    tl.store(complete + trial, active)


class IntervalSampler:
    def __init__(self, classes, layers, accepting, *, block_size=1024, device="cuda"):
        classes, layers = split_blocks(classes, layers, block_size)
        self.engine = IntervalDAG(classes, layers, accepting, device=device)
        dev = self.engine.device
        node_offsets = [0]
        for layer in layers:
            node_offsets.append(node_offsets[-1] + len(layer))
        outgoing, targets, edge_pointer, edge_labels, positions = [0], [], [0], [], []
        arity = max(map(len, classes))
        for p, layer in enumerate(layers):
            for edges in layer:
                arity = max(arity, len(edges))
                for target, cids in edges:
                    arity = max(arity, len(cids))
                    targets.append(node_offsets[p + 1] + target)
                    edge_labels.extend(cids)
                    edge_pointer.append(len(edge_labels))
                    positions.append(p)
                outgoing.append(len(targets))
        if arity > 1024:
            raise ValueError("GPU control arity guard; full original support not pruned")
        self.width = tr.next_power_of_2(arity)
        self.graph = tuple(
            torch.tensor(a, dtype=torch.long, device=dev)
            for a in (outgoing, targets, edge_pointer, edge_labels)
        )
        self.positions = torch.tensor(positions, dtype=torch.long, device=dev)

    @torch.no_grad()
    def sample(self, weights, source, rngs, *, bits=32):
        n, count = len(self.engine.layers), source.shape[0]
        if (
            source.dtype != torch.int64
            or source.shape != (count, n, 3)
            or source.device != self.engine.device
            or len(rngs) != count
            or not 1 <= bits <= 32
            or bool((source < 0).any())
            or bool((source >= 1 << bits).any())
        ):
            raise ValueError("one independent retained prefix per trial/slot/phase required")
        result = self.engine.query(weights)
        edge_lo, edge_hi = [
            torch.empty(len(self.positions), dtype=torch.float32, device=self.engine.device)
            for _ in range(2)
        ]
        _edge_mass[(len(self.positions),)](
            result["class_lower"],
            result["class_upper"],
            self.positions,
            self.graph[2],
            self.graph[3],
            edge_lo,
            edge_hi,
            len(self.engine.classes),
            self.width,
        )
        beta_lo, beta_hi = torch.cat(result["beta_lower"]), torch.cat(result["beta_upper"])
        words = torch.full((count, n), -1, dtype=torch.long, device=self.engine.device)
        complete = torch.zeros(count, dtype=torch.bool, device=self.engine.device)
        if result["lower"] > 0:
            _walk[(count,)](
                weights.contiguous(),
                result["class_lower"],
                result["class_upper"],
                edge_lo,
                edge_hi,
                beta_lo,
                beta_hi,
                *self.graph,
                self.engine.pointer,
                self.engine.members,
                source.contiguous(),
                words,
                complete,
                self.engine.vocabulary,
                len(self.engine.classes),
                n,
                bits,
                self.width,
            )
        flags = complete.cpu().tolist()
        need = [i for i, ok in enumerate(flags) if not ok]
        exact = None
        if need:
            exact = ExactDAG(
                self.engine.classes,
                self.engine.layers,
                self.engine.accepting,
                weights.cpu().tolist(),
            )
            raw = source[need].cpu().tolist()
            replacements = [exact.sample(s, bits, rngs[i]) for i, s in zip(need, raw, strict=True)]
            words[need] = torch.tensor(replacements, dtype=torch.long, device=self.engine.device)
        return dict(
            tokens=words,
            fallback_count=len(need),
            gpu_certified=count - len(need),
            mass_lower=result["lower"],
            mass_upper=result["upper"],
            exact_fallback=exact,
        )
