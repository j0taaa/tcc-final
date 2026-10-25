"""Exact specialized recursive JSON token verifier, CPU and integer Torch CUDA."""
from __future__ import annotations

import ctypes as ct
import hashlib
import json
import re
import subprocess
import time
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
MASK, EOS, EOT = 126336, 126081, 126348
INF = 10000


def grammar_step(state, text, depth_limit):
    # 0=start, 1..4D = (depth, mode), then finished, then EOS/padding.
    end, eos = 4 * depth_limit + 1, 4 * depth_limit + 2
    if text == "<EOS>":
        return eos if state in (end, eos) else -1
    for char in text:
        if state in (end, eos):
            return -1
        if state == 0:
            if char != "[":
                return -1
            state = 1
            continue
        depth, mode = (state - 1) // 4 + 1, (state - 1) % 4
        if mode == 2:
            if char == '"':
                mode = 3
            elif not ("a" <= char <= "z" or "A" <= char <= "Z"):
                return -1
        elif char == '"' and mode in (0, 1):
            mode = 2
        elif char == "[" and mode in (0, 1):
            depth, mode = depth + 1, 0
            if depth > depth_limit:
                return -1
        elif char == "]" and mode in (0, 3):
            if depth == 1:
                state = end
                continue
            depth, mode = depth - 1, 3
        elif char == "," and mode == 3:
            mode = 1
        else:
            return -1
        state = 1 + 4 * (depth - 1) + mode
    return state


def compile_tables(tokenizer, budget=96):
    start = time.perf_counter()
    emissions = tokenizer.batch_decode(
        [[v] for v in range(len(tokenizer))],
        skip_special_tokens=False, clean_up_tokenization_spaces=False,
    )
    allowed = set('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ[]",')
    eligible = [(i, s) for i, s in enumerate(emissions) if s and set(s) <= allowed]
    max_open = max(s.count("[") for _, s in eligible)
    depth = budget * max_open
    # Letters in strings have the same effect regardless of spelling/length.
    patterns = sorted({re.sub("[a-zA-Z]+", "a", s) for _, s in eligible}) + ["<EOS>"]
    index = {s: i for i, s in enumerate(patterns)}
    groups = np.full(126464, -2, dtype=np.int32)
    for tok, s in eligible:
        groups[tok] = index[re.sub("[a-zA-Z]+", "a", s)]
    groups[EOS] = groups[EOT] = index["<EOS>"]
    states = 4 * depth + 3
    table = np.array(
        [[grammar_step(q, p, depth) for q in range(states)] for p in patterns],
        dtype=np.int32,
    )
    # Invalid-effect tokens need never enter a shortlist.
    live_classes = np.any(table >= 0, axis=1)
    admitted = np.flatnonzero((groups >= 0) & live_classes[np.maximum(groups, 0)])
    return {
        "table": table, "groups": groups, "admitted": admitted,
        "patterns": patterns, "depth": depth, "max_open_per_token": max_open,
        "seconds": time.perf_counter() - start,
        "vocab_sha256": hashlib.sha256(json.dumps(emissions).encode()).hexdigest(),
    }


def compile_library(cache):
    cache = Path(cache)
    cache.mkdir(parents=True, exist_ok=True)
    source = HERE / "verifier.cpp"
    digest = hashlib.sha256(source.read_bytes()).hexdigest()
    target = cache / f"verifier-{digest[:16]}.so"
    start = time.perf_counter()
    reused = target.exists()
    if not reused:
        subprocess.run(
            ["g++", "-O3", "-std=c++17", "-shared", "-fPIC", str(source), "-o", str(target)],
            check=True, capture_output=True,
        )
    lib = ct.CDLL(str(target))
    ptr = ct.c_void_p
    lib.init.argtypes = [ct.c_int, ct.c_int, ptr]
    lib.build.argtypes = [ct.c_int, ptr, ct.c_int, ptr, ptr]
    lib.allows.argtypes = [ct.c_int, ct.c_int, ptr, ptr]
    lib.allocation.argtypes = [ct.c_int, ptr, ptr]
    lib.distances.argtypes = [ptr]
    return lib, {"seconds": time.perf_counter() - start, "reused": reused, "sha256": digest}


def pointer(array):
    return array.ctypes.data_as(ct.c_void_p)


class Verifier:
    def __init__(self, table, lib, device="cpu", distances=None):
        self.table = np.ascontiguousarray(table, dtype=np.int32)
        self.s = table.shape[1]
        self.lib, self.device = lib, device
        lib.init(self.s, len(table), pointer(self.table))
        self.adj = [sorted(set(int(v) for v in table[:, u] if v >= 0)) for u in range(self.s)]
        self.rev = [[] for _ in range(self.s)]
        for u, edges in enumerate(self.adj):
            for v in edges:
                self.rev[v].append(u)
        if device == "cuda":
            import torch
            self.t = torch.as_tensor(table.astype(np.int64), device="cuda")
            def padded(lists):
                n = max(map(len, lists))
                out = np.full((self.s, n), self.s, dtype=np.int64)
                for i, row in enumerate(lists):
                    out[i, :len(row)] = row
                return torch.as_tensor(out, device="cuda")
            self.a, self.r = padded(self.adj), padded(self.rev)
            if distances is None:
                distances = np.empty((self.s, self.s), dtype=np.int32)
                lib.distances(pointer(distances))
            self.dist = torch.as_tensor(distances, device="cuda")

    def prepare(self, canvas, changed=-1):
        self.x = np.asarray(canvas, dtype=np.int32)
        n = len(canvas)
        if self.device == "cpu":
            if changed < 0:
                self.f = np.zeros((n + 1, self.s), dtype=np.uint8)
                self.b = np.zeros_like(self.f)
            self.lib.build(n, pointer(self.x), changed, pointer(self.f), pointer(self.b))
            return bool(self.b[0, 0])
        import torch
        if changed < 0:
            self.f = torch.zeros((n + 1, self.s + 1), dtype=torch.int32, device="cuda")
            self.b = torch.zeros_like(self.f)
            self.f[0, 0] = True
            self.b[n, self.s - 1] = True
            changed = 0
        for i in range(changed, n):
            if canvas[i] < 0:
                self.f[i + 1, :self.s] = self.f[i][self.r].any(1)
            else:
                valid = self.t[canvas[i]] >= 0
                self.f[i + 1].zero_()
                self.f[i + 1].scatter_reduce_(
                    0, torch.where(valid, self.t[canvas[i]], self.s),
                    self.f[i, :self.s] & valid, reduce="amax", include_self=True,
                )
                self.f[i + 1, self.s] = False
        for i in range(n - 1 if changed == 0 else changed, -1, -1):
            if canvas[i] < 0:
                self.b[i, :self.s] = self.b[i + 1][self.a].any(1)
            else:
                dest = self.t[canvas[i]]
                self.b[i, :self.s] = self.b[i + 1][dest.clamp_min(0)] & (dest >= 0)
        return bool(self.b[0, 0].item())

    def allows(self, pos, cls):
        if self.device == "cpu":
            return bool(self.lib.allows(pos, cls, pointer(self.f), pointer(self.b)))
        dest = self.t[cls]
        return bool((self.f[pos, :self.s] & (dest >= 0)
                     & self.b[pos + 1][dest.clamp_min(0)]).any().item())

    def allocate(self, canvas, extra, return_dp=False):
        x = np.asarray(canvas, dtype=np.int32)
        n = len(x)
        if self.device == "cpu":
            dp = np.empty((n + 1, self.s), dtype=np.int32)
            self.lib.allocation(n, pointer(x), pointer(dp))
        else:
            import torch
            d = torch.full((n + 1, self.s + 1), INF, dtype=torch.int32, device="cuda")
            for i in range(n, -1, -1):
                if i == n:
                    base = torch.full((self.s,), INF, dtype=torch.int32, device="cuda")
                    base[-1] = 0
                elif x[i] < 0:
                    base = d[i + 1][self.a].amin(1)
                else:
                    dest = self.t[x[i]]
                    base = torch.where(dest >= 0, d[i + 1][dest.clamp_min(0)], INF)
                d[i, :self.s] = (self.dist + base[None, :]).amin(1).clamp_max(INF)
            dp = d[:, :self.s].cpu().numpy()
        counts = None
        if dp[0, 0] <= extra:
            counts = self.reconstruct(x, dp)
        return (counts, dp) if return_dp else counts

    def reconstruct(self, x, dp):
        counts = [0] * (len(x) + 1)
        i, q = 0, 0
        while i < len(x) or q != self.s - 1:
            successors = self.adj[q] if i < len(x) and x[i] < 0 else (
                [int(self.table[x[i], q])] if i < len(x) else [])
            consume = [v for v in successors if v >= 0 and dp[i + 1, v] == dp[i, q]]
            if consume:
                q = consume[0]
                i += 1
                continue
            insert = [v for v in self.adj[q] if dp[i, v] + 1 == dp[i, q]]
            if not insert:
                raise AssertionError("No witness for finite distance")
            q = insert[0]
            counts[i] += 1
        return counts


def insert_masks(canvas, counts):
    out, remap = [], {}
    for i in range(len(canvas) + 1):
        out.extend([-1] * counts[i])
        if i < len(canvas):
            remap[i] = len(out)
            out.append(canvas[i])
    return out, remap
