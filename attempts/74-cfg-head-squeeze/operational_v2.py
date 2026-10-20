"""A74 V2: exact integer-head CFG sampler and complete operational comparison."""

from __future__ import annotations

import argparse
import bisect
import fcntl
import gc
import hashlib
import importlib.util
import json
import math
import os
import random
import resource
import signal
import subprocess
import time
from decimal import ROUND_CEILING, Decimal, localcontext
from fractions import Fraction
from itertools import product
from pathlib import Path

import numpy as np
import torch
import torch.nn.functional as functional
from transformers import AutoTokenizer

from mwpc_exact.tokenizer_bytes import byte_level_piece_to_bytes

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
VOCAB = 50256
MASK = 50257
LENGTHS = (8, 32, 128)
PREFIXES = ("Return a balanced sequence of A and B:", "Complete the structured payload:")
PROXIES = ("int8", "svd8", "svd32", "svd128")
BACKENDS = ("split", "double")
METHODS = tuple(f"dense:{b}" for b in BACKENDS) + tuple(
    f"{p}:{b}" for p, b in product(PROXIES, BACKENDS)
)


def load_local_screen():
    spec = importlib.util.spec_from_file_location("a74_screen", HERE / "screen.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def exp_table():
    with localcontext() as context:
        context.prec = 80
        values = [
            int(((Decimal(k) / 256).exp() * 65536).to_integral_value(rounding=ROUND_CEILING))
            for k in range(-8192, 8193)
        ]
    result = np.array(values, dtype=np.int64)
    assert result.min() > 0 and int(result.max()) < 2**63
    assert (result[1:] >= result[:-1]).all()
    return result


def integer_norms(matrix):
    maximum = int(np.abs(matrix).max())
    assert maximum <= math.isqrt((2**63 - 1) // matrix.shape[-1])
    squares = (matrix * matrix).sum(axis=-1, dtype=np.int64)
    return np.array(
        [math.isqrt(int(s)) + int(math.isqrt(int(s)) ** 2 != int(s)) for s in squares],
        dtype=np.int64,
    )


class Bits:
    def __init__(self, seed):
        self.random = random.Random(seed)
        self.bits = 0

    def below(self, total):
        if total <= 0:
            raise ValueError("INFEASIBLE_ON_SUPPORT")
        width = (total - 1).bit_length()
        while True:
            self.bits += width
            value = self.random.getrandbits(width)
            if value < total:
                return value


class CDF:
    """Exact positive-integer CDF up to 128 bits, with explicit uint64 carries."""

    def __init__(self, weights):
        weights = np.asarray(weights, dtype=np.uint64)
        self.low = np.cumsum(weights, dtype=np.uint64)
        previous = np.concatenate((np.zeros(1, dtype=np.uint64), self.low[:-1]))
        self.high = np.cumsum(self.low < previous, dtype=np.uint64)
        self.total = (int(self.high[-1]) << 64) + int(self.low[-1])

    def ticket(self, value):
        high, low = divmod(value, 2**64)
        start = int(np.searchsorted(self.high, np.uint64(high), side="left"))
        end = int(np.searchsorted(self.high, np.uint64(high), side="right"))
        return start + int(np.searchsorted(self.low[start:end], np.uint64(low), side="right"))


class Posterior:
    def __init__(self, rows, keep_cdfs=True):
        self.rows = rows
        self.n, self.v = rows.shape
        assert self.n % 2 == 0 and self.v % 4 == 0
        assert (rows >= 0).all()
        self.cdfs, self.masses = [], []
        for row in rows:
            cdfs = [CDF(row[g::4]) for g in range(4)]
            self.masses.append([cdf.total for cdf in cdfs])
            if keep_cdfs:
                self.cdfs.append(cdfs)
        half = self.n // 2
        self.charts = []
        self.integer_bits = 0
        for mode in range(2):
            dp = [[0] * (half + 1) for _ in range(self.n + 1)]
            dp[self.n][0] = 1
            for i in range(self.n - 1, -1, -1):
                a, b = self.masses[i][2 * mode : 2 * mode + 2]
                for k in range(min(half, self.n - i) + 1):
                    dp[i][k] = b * dp[i + 1][k] + (a * dp[i + 1][k - 1] if k else 0)
                    self.integer_bits = max(self.integer_bits, dp[i][k].bit_length())
            self.charts.append(dp)
        self.z = sum(dp[0][half] for dp in self.charts)

    def sample(self, rng):
        half = self.n // 2
        mode = int(rng.below(self.z) >= self.charts[0][0][half])
        dp, left, output = self.charts[mode], half, []
        for i in range(self.n):
            a, b = self.masses[i][2 * mode : 2 * mode + 2]
            aw = a * dp[i + 1][left - 1] if left else 0
            bw = b * dp[i + 1][left]
            kind = int(rng.below(aw + bw) >= aw)
            group = 2 * mode + kind
            cdf = self.cdfs[i][group]
            output.append(group + 4 * cdf.ticket(rng.below(cdf.total)))
            left -= int(kind == 0)
        assert left == 0
        return output

    def word_probability(self, word):
        """Induced CDF/DP law used only by the independent finite oracle."""
        mode = (word[0] % 4) // 2
        dp, left = self.charts[mode], self.n // 2
        result = Fraction(dp[0][left], self.z)
        for i, token in enumerate(word):
            group = token % 4
            if group // 2 != mode:
                return Fraction(0)
            next_left = left - int(group % 2 == 0)
            if next_left < 0:
                return Fraction(0)
            suffix = dp[i + 1][next_left]
            result *= Fraction(self.masses[i][group] * suffix, dp[i][left])
            result *= Fraction(int(self.rows[i, token]), self.masses[i][group])
            left = next_left
        return result if left == 0 else Fraction(0)


def valid(word):
    return len({(v % 4) // 2 for v in word}) == 1 and sum(v % 2 == 0 for v in word) * 2 == len(word)


def oracle():
    source = random.Random(740300)
    count = 0
    for n, v in ((2, 8), (4, 8), (2, 12)):
        rows = np.array(
            [[source.randrange(1, 10) for _ in range(v)] for _ in range(n)], dtype=np.int64
        )
        posterior = Posterior(rows)
        words = [w for w in product(range(v), repeat=n) if valid(w)]
        exact = sum(math.prod(int(rows[i, t]) for i, t in enumerate(w)) for w in words)
        assert posterior.z == exact
        for word in words:
            assert posterior.word_probability(word) == Fraction(
                math.prod(int(rows[i, t]) for i, t in enumerate(word)), exact
            )
            count += 1
        if n == 4:
            fixed = rows.copy()
            fixed[0] = 0
            fixed[0, 1] = rows[0, 1]
            p = Posterior(fixed)
            assert p.z == sum(math.prod(int(fixed[i, t]) for i, t in enumerate(w)) for w in words)
            for _ in range(16):
                assert p.sample(Bits(source.randrange(2**32)))[0] == 1
    for weights in ([0, 3, 0, 5], [2**63 - 1] * 5, [2**64 - 1, 1, 2, 2**64 - 1]):
        cdf = CDF(weights)
        cumulative = list(__import__("itertools").accumulate(weights))
        tickets = {0, sum(weights) - 1}
        tickets.update(
            x for value in cumulative for x in (value - 1, value) if 0 <= x < sum(weights)
        )
        for ticket in tickets:
            assert cdf.ticket(ticket) == bisect.bisect_right(cumulative, ticket)
    norm_rows = np.array([[3, 4], [0, 0], [-7, 9]], dtype=np.int64)
    for row, norm in zip(norm_rows, integer_norms(norm_rows), strict=True):
        exact = sum(int(v) ** 2 for v in row)
        assert int(norm) ** 2 >= exact and (int(norm) - 1) ** 2 < exact if exact else norm == 0
    table = exp_table()
    for _ in range(64):
        lo = source.randrange(-(2**30), 2**30)
        ref = lo + source.randrange(100000)
        hi = ref + source.randrange(100000)
        indices = [min(8192, max(-8192, v // 2**14)) + 8192 for v in (lo, ref, hi)]
        assert table[indices[0]] <= table[indices[1]] <= table[indices[2]]
    # Full cap law with independent small target: all candidate-ticket regions.
    for lower, target, upper in (([1, 1], [1, 2], [3, 3]), ([0, 0], [2, 3], [4, 5])):
        zw, zl, zu = sum(target), sum(lower), sum(upper)
        p = Fraction(zw, zu)
        for x in range(2):
            accepted = sum(
                Fraction(1, zu)
                for ticket in range(upper[x])
                if ticket < lower[x] or (ticket >= lower[x] and ticket < target[x])
            )
            for cap in (0, 1, 4):
                final = sum((1 - p) ** j * accepted for j in range(cap)) + (
                    1 - p
                ) ** cap * Fraction(target[x], zw)
                assert final == Fraction(target[x], zw)
        assert Fraction(zu - zl, zw) == (1 - Fraction(zl, zu)) / p
    print(
        json.dumps(
            {
                "status": "PASS",
                "complete_word_laws": count,
                "carry_boundary_cases": 3,
                "lookup_sha256": hashlib.sha256(table.tobytes()).hexdigest(),
            }
        )
    )


def ns():
    return time.perf_counter_ns()


def timed(fn):
    begin = ns()
    result = fn()
    return result, (ns() - begin) / 1e9


def gpu_snapshot():
    return subprocess.check_output(
        [
            "nvidia-smi",
            "--query-gpu=name,utilization.gpu,memory.free",
            "--format=csv,noheader,nounits",
        ],
        text=True,
    ).strip()


def process_snapshot():
    return subprocess.check_output(
        [
            "nvidia-smi",
            "--query-compute-apps=pid,process_name,used_memory",
            "--format=csv,noheader,nounits",
        ],
        text=True,
    ).strip()


def split_parts(x):
    assert int(x.abs().max().item()) <= 16384
    assert int(x.max().item()) <= 16383
    x = functional.pad(x, (0, 0, 0, (-x.shape[0]) % 16))
    return (
        torch.remainder(x, 128).to(torch.int8).contiguous(),
        torch.div(x, 128, rounding_mode="floor").to(torch.int8).contiguous(),
    )


def mm_parts(hparts, wparts):
    hlo, hhi = hparts
    wlo, whi = wparts
    result = torch._int_mm(hlo, wlo.T).to(torch.int64)
    result += 128 * torch._int_mm(hhi, wlo.T).to(torch.int64)
    result += 128 * torch._int_mm(hlo, whi.T).to(torch.int64)
    result += 16384 * torch._int_mm(hhi, whi.T).to(torch.int64)
    return result


class Heads:
    def __init__(self, w, bias, lookup):
        self.w = torch.from_numpy(w.astype(np.int32)).cuda()
        self.bias = torch.from_numpy(bias).cuda()
        self.lookup = torch.from_numpy(lookup).cuda()
        self.double = self.w.double()
        self.parts = split_parts(self.w)
        self.proxies = {}
        self.storage = {}

    def weights(self, scores, shift):
        index = torch.div(scores, 2**shift, rounding_mode="floor").clamp(-8192, 8192) + 8192
        return self.lookup[index]

    def dense(self, h, backend):
        if backend == "split":
            scores = mm_parts(split_parts(h), self.parts)[: len(h)]
        else:
            scores = (h.double() @ self.double.T).to(torch.int64)
        return self.weights(scores + self.bias, 14).cpu().numpy()

    def query(self, h, word):
        ids = torch.tensor(word, dtype=torch.int64, device="cuda")
        scores = (self.w[ids].to(torch.int64) * h.to(torch.int64)).sum(-1) + self.bias[ids]
        return self.weights(scores, 14).cpu().numpy()

    def bounds(self, h, name):
        p = self.proxies[name]
        if name == "int8":
            lo, hi = split_parts(h)
            q = (
                torch._int_mm(lo, p["w8"].T).to(torch.int64)
                + 128 * torch._int_mm(hi, p["w8"].T).to(torch.int64)
            )[: len(h)]
            q = q * p["scales"] + self.bias
            shift = 14
        else:
            q = ((h.double() @ p["b"].T) @ p["a"].T).to(torch.int64) + self.bias * 256
            shift = 22
        norm2 = (h.to(torch.int64) ** 2).sum(-1).cpu().numpy()
        eta = torch.tensor(
            [math.isqrt(int(v)) + int(math.isqrt(int(v)) ** 2 != int(v)) for v in norm2],
            dtype=torch.int64,
            device="cuda",
        )
        error = eta[:, None] * p["rho"][None, :]
        lower = self.weights(q - error, shift).cpu().numpy()
        upper = self.weights(q + error, shift).cpu().numpy()
        return lower, upper


def prepare_proxies(heads, w, emit):
    setup = {}
    started = ns()
    maximum = np.abs(w).max(axis=1)
    scales = np.array(
        [1 << (max(1, (int(x) + 126) // 127) - 1).bit_length() for x in maximum], dtype=np.int64
    )
    quant = np.rint(w / scales[:, None]).astype(np.int64)
    assert np.abs(quant).max() <= 127
    rho = integer_norms(w - quant * scales[:, None])
    heads.proxies["int8"] = {
        "w8": torch.from_numpy(quant.astype(np.int8)).cuda(),
        "scales": torch.from_numpy(scales).cuda(),
        "rho": torch.from_numpy(rho).cuda(),
    }
    torch.cuda.synchronize()
    setup["int8"] = (ns() - started) / 1e9
    heads.storage["int8"] = quant.size + 16 * len(quant)
    started = ns()
    matrix = torch.from_numpy(w.astype(np.float64)) / 4096
    gram = matrix.T @ matrix
    _, eigenvectors = torch.linalg.eigh(gram)
    common_svd = (ns() - started) / 1e9
    for rank in (8, 32, 128):
        started = ns()
        basis = eigenvectors[:, -rank:]
        a = np.rint((matrix @ basis).numpy() * 1024).astype(np.int64)
        b = np.rint(basis.T.numpy() * 1024).astype(np.int64)
        assert rank * int(np.abs(a).max()) * int(np.abs(b).max()) < 2**53
        fitted = (a.astype(np.float64) @ b.astype(np.float64)).astype(np.int64)
        rho = integer_norms(w * 256 - fitted)
        # Exact FP64 integer GEMMs for EVERY admitted H10, not a probabilistic bound.
        limit = int(np.abs(a).sum(-1).max()) * int(np.abs(b).sum(-1).max()) * 16384
        assert limit < 2**53
        name = f"svd{rank}"
        heads.proxies[name] = {
            "a": torch.from_numpy(a.astype(np.float64)).cuda(),
            "b": torch.from_numpy(b.astype(np.float64)).cuda(),
            "rho": torch.from_numpy(rho).cuda(),
        }
        torch.cuda.synchronize()
        setup[name] = common_svd + (ns() - started) / 1e9
        heads.storage[name] = a.nbytes + b.nbytes + rho.nbytes
        emit(
            type="proxy",
            proxy=name,
            rank=rank,
            setup_seconds=setup[name],
            common_svd_seconds=common_svd,
            exact_integer_partial_sum_bound=limit,
            min_rho=int(rho.min()),
            max_rho=int(rho.max()),
            storage_bytes=heads.storage[name],
        )
    emit(
        type="proxy", proxy="int8", setup_seconds=setup["int8"], storage_bytes=heads.storage["int8"]
    )
    return setup


def operation(heads, h, method, rng, emissions):
    stage = {}
    started = ns()
    proxy, backend = method.split(":")
    counters = {"reference_rows": 0, "proposals": 0, "fallback": False, "dense_head_rows": 0}
    if proxy == "dense":
        rows, stage["dense_head"] = timed(lambda: heads.dense(h, backend))
        posterior, stage["inside_cdf"] = timed(lambda: Posterior(rows))
        word, stage["rng_sample"] = timed(lambda: posterior.sample(rng))
        counters["dense_head_rows"] = h.shape[0] * VOCAB
        chart_bits = posterior.integer_bits
    else:
        (lower, upper), stage["proxy_bounds_transfer"] = timed(lambda: heads.bounds(h, proxy))
        posterior, stage["inside_cdf"] = timed(lambda: Posterior(upper))
        lower_posterior, stage["lower_inside"] = timed(lambda: Posterior(lower, keep_cdfs=False))
        chart_bits = max(posterior.integer_bits, lower_posterior.integer_bits)
        word = None
        stage["rng_proposals"] = 0.0
        stage["reference_queries"] = 0.0
        for _ in range(4):
            begin = ns()
            candidate = posterior.sample(rng)
            uprod = math.prod(int(upper[i, v]) for i, v in enumerate(candidate))
            lprod = math.prod(int(lower[i, v]) for i, v in enumerate(candidate))
            ticket = rng.below(uprod)
            counters["proposals"] += 1
            stage["rng_proposals"] += (ns() - begin) / 1e9
            if ticket < lprod:
                word = candidate
                break
            begin = ns()
            reference = heads.query(h, candidate)
            counters["reference_rows"] += len(candidate)
            accepted = ticket < math.prod(int(v) for v in reference)
            stage["reference_queries"] += (ns() - begin) / 1e9
            if accepted:
                word = candidate
                break
        if word is None:
            counters["fallback"] = True
            rows, stage["fallback_head"] = timed(lambda: heads.dense(h, backend))
            dense, stage["fallback_inside"] = timed(lambda: Posterior(rows))
            word, stage["fallback_rng"] = timed(lambda: dense.sample(rng))
            counters["dense_head_rows"] = h.shape[0] * VOCAB
            chart_bits = max(chart_bits, dense.integer_bits)
    begin = ns()
    assert valid(word) and len(word) == len(h)
    raw = b"".join(emissions[v] for v in word)
    stage["output_bytes"] = (ns() - begin) / 1e9
    torch.cuda.synchronize()
    return {
        "seconds": (ns() - started) / 1e9,
        "stages": stage,
        "ids": word,
        "bytes_sha256": hashlib.sha256(raw).hexdigest(),
        "output_byte_count": len(raw),
        "rng_bits": rng.bits,
        "peak_chart_integer_bits": chart_bits,
        **counters,
    }


def run(output):
    if subprocess.run(["git", "diff", "--quiet", "HEAD"], cwd=ROOT).returncode:
        raise ValueError("freeze source and protocol before measurement")
    lock = open("/tmp/tcc-final-candidate-tests-gpu.lock", "a")
    try:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        print("LOCK_BUSY; no measurement started")
        return 75
    output.mkdir(parents=True, exist_ok=False)
    monitor = None
    with lock, (output / "rows.jsonl").open("x") as stream:

        def emit(**row):
            stream.write(json.dumps(row) + "\n")
            stream.flush()
            if row["type"] != "draw":
                print(json.dumps(row), flush=True)

        def stop(signum, _frame):
            emit(type="interruption", signal=signum, status="INCONCLUSIVE")
            raise SystemExit(128 + signum)

        signal.signal(signal.SIGTERM, stop)
        signal.signal(signal.SIGINT, stop)

        def check_concurrency():
            for line in (output / "pmon.txt").read_text().splitlines():
                columns = line.split()
                if len(columns) > 4 and columns[0].isdigit() and "C" in columns[2]:
                    if (
                        int(columns[1]) != os.getpid()
                        and columns[3].isdigit()
                        and int(columns[3]) > 0
                    ):
                        emit(
                            type="resource", status="CONCURRENT_ACTIVITY_TIMINGS_INVALID", raw=line
                        )
                        raise RuntimeError("observed foreign GPU compute; all timings inconclusive")

        try:
            producer = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
            telemetry = []
            for _ in range(3):
                snapshot = gpu_snapshot()
                telemetry.append(snapshot)
                util, free = (int(v.strip()) for v in snapshot.rsplit(",", 2)[1:])
                if util > 3 or free < 2048:
                    emit(
                        type="resource",
                        status="RESOURCE_REFUSAL_INCONCLUSIVE",
                        snapshots=telemetry,
                        processes=process_snapshot(),
                        producer=producer,
                    )
                    return 2
                time.sleep(1)
            emit(
                type="environment",
                producer=producer,
                torch=torch.__version__,
                numpy=np.__version__,
                snapshots=telemetry,
                resident_processes=process_snapshot(),
                seed=740301,
                lock="/tmp/tcc-final-candidate-tests-gpu.lock",
                numerical_contract="Q12_W_Q10_H_lookup80_v2",
            )
            monitor_stream = (output / "pmon.txt").open("x")
            monitor = subprocess.Popen(
                ["nvidia-smi", "pmon", "-s", "um", "-d", "1"],
                stdout=monitor_stream,
                stderr=subprocess.STDOUT,
                text=True,
            )
            torch.set_num_threads(4)
            torch.manual_seed(740301)
            torch.backends.cuda.matmul.allow_tf32 = False
            torch.backends.cudnn.allow_tf32 = False
            setup_started = ns()
            config = json.loads(
                (ROOT / "configs/experiments/m31_probability_scaling_cpu_v1.json").read_text()
            )
            screen = load_local_screen()
            model, adapted = screen.load_model(config)
            head = next(
                m
                for m in model.modules()
                if isinstance(m, torch.nn.Linear) and m.out_features == 50258
            )
            w = np.rint(head.weight.detach().numpy()[:VOCAB].astype(np.float64) * 4096).astype(
                np.int64
            )
            bias = np.rint(head.bias.detach().numpy()[:VOCAB].astype(np.float64) * 2**22).astype(
                np.int64
            )
            assert w.min() >= -16384 and w.max() <= 16383
            snapshot = (
                screen.CACHE
                / "models--openai-community--gpt2/snapshots"
                / config["tokenizer_revision"]
            )
            tokenizer = AutoTokenizer.from_pretrained(str(snapshot), local_files_only=True)
            emissions = [
                byte_level_piece_to_bytes(tokenizer.convert_ids_to_tokens(v)) for v in range(VOCAB)
            ]
            lookup = exp_table()
            model.to("cuda").eval()
            heads = Heads(w, bias, lookup)
            torch.cuda.synchronize()
            common_setup = (ns() - setup_started) / 1e9
            emit(
                type="model",
                model_id=config["model_id"],
                revision=config["model_revision"],
                checkpoint_hashes=config["checkpoint_sha256"],
                adapted_sha256=adapted,
                tokenizer_revision=config["tokenizer_revision"],
                lookup_sha256=hashlib.sha256(lookup.tobytes()).hexdigest(),
                w12_sha256=hashlib.sha256(w.tobytes()).hexdigest(),
                eligible_ids="0..50255",
                common_setup_seconds=common_setup,
                reference_storage_bytes=w.size * 4 + bias.nbytes,
                numerical_contract="protocol-v2.md; integer weights; not native torch softmax",
            )
            proxy_setup = prepare_proxies(heads, w, emit)
            captured = []

            class Captured(Exception):
                pass

            def hook(_module, inputs):
                captured.append(inputs[0].detach().clone())
                raise Captured

            handle = head.register_forward_pre_hook(hook)
            for case, (prefix, n) in enumerate(product(PREFIXES, LENGTHS)):
                prefix_ids = tokenizer.encode(prefix, add_special_tokens=False)
                ids = prefix_ids + [MASK] * n
                input_ids = torch.tensor([ids], device="cuda")
                capture_costs = []
                hidden = None
                for rep in range(4):
                    torch.cuda.synchronize()
                    begin = ns()
                    try:
                        with torch.inference_mode():
                            model(input_ids=input_ids, timesteps=torch.zeros(1, device="cuda"))
                    except Captured:
                        pass
                    else:
                        raise AssertionError("reference original head unexpectedly executed")
                    torch.cuda.synchronize()
                    elapsed = (ns() - begin) / 1e9
                    current = captured.pop()[0, len(prefix_ids) :]
                    if rep:
                        capture_costs.append(elapsed)
                        if hidden is None:
                            hidden = current
                backbone = float(np.median(capture_costs))
                quant_begin = ns()
                h = torch.round(hidden * 1024).to(torch.int32)
                torch.cuda.synchronize()
                quant_seconds = (ns() - quant_begin) / 1e9
                assert int(h.min().item()) >= -16384 and int(h.max().item()) <= 16383
                hcpu = h.cpu().numpy().astype(np.int64)
                emit(
                    type="state",
                    case=case,
                    prefix=prefix,
                    n=n,
                    input_ids=ids,
                    hidden_sha256=hashlib.sha256(hidden.cpu().numpy().tobytes()).hexdigest(),
                    h10_sha256=hashlib.sha256(hcpu.tobytes()).hexdigest(),
                    backbone_seconds=capture_costs,
                    backbone_median_seconds=backbone,
                    hidden_quantize_seconds=quant_seconds,
                )
                # All values, not a sampled check, must agree between dense implementations.
                dense_split = heads.dense(h, "split")
                dense_double = heads.dense(h, "double")
                assert np.array_equal(dense_split, dense_double)
                target = Posterior(dense_split)
                emit(
                    type="target_mass",
                    case=case,
                    n=n,
                    class_masses=[[str(v) for v in r] for r in target.masses],
                    Zw=str(target.z),
                )
                pairs_rng = random.Random(740303 + case)
                for _ in range(64):
                    i, v = pairs_rng.randrange(n), pairs_rng.randrange(VOCAB)
                    score = sum(int(a) * int(b) for a, b in zip(w[v], hcpu[i], strict=True)) + int(
                        bias[v]
                    )
                    expected = int(lookup[min(8192, max(-8192, score // 2**14)) + 8192])
                    assert expected == int(dense_split[i, v])
                test_word = [pairs_rng.randrange(VOCAB) for _ in range(n)]
                queried = heads.query(h, test_word)
                assert all(
                    int(queried[i]) == int(dense_split[i, v]) for i, v in enumerate(test_word)
                )
                for proxy in PROXIES:
                    lower, upper = heads.bounds(h, proxy)
                    assert (lower <= dense_split).all() and (dense_split <= upper).all()
                    lp, up = Posterior(lower, False), Posterior(upper, False)
                    zl, zu = lp.z, up.z
                    emit(
                        type="mass",
                        case=case,
                        n=n,
                        proxy=proxy,
                        Zw=str(target.z),
                        ZL=str(zl),
                        ZU=str(zu),
                        lower_class_masses=[[str(v) for v in r] for r in lp.masses],
                        upper_class_masses=[[str(v) for v in r] for r in up.masses],
                        log_acceptance=math.log(target.z) - math.log(zu),
                        log_squeeze_mass=math.log(zl) - math.log(zu),
                        enclosure="ALL_IDS_VERIFIED",
                        dense_kernel_equality="ALL_IDS_VERIFIED",
                        python_integer_pairs=64,
                        proxy_setup_seconds=proxy_setup[proxy],
                    )
                del dense_split, dense_double, target, lower, upper
                for k, method in enumerate(METHODS):
                    operation(heads, h, method, Bits(740304 + case * 100 + k), emissions)
                gc.collect()
                gc.disable()
                for rep in range(11):
                    check_concurrency()
                    order = list(METHODS)
                    shift = (rep + case) % len(order)
                    order = order[shift:] + order[:shift]
                    for method in order:
                        index = METHODS.index(method)
                        row = operation(
                            heads,
                            h,
                            method,
                            Bits(740302 + 10000 * case + 100 * rep + index),
                            emissions,
                        )
                        row.update(
                            type="draw",
                            case=case,
                            n=n,
                            rep=rep,
                            method=method,
                            common_setup_seconds=common_setup,
                            proxy_setup_seconds=0.0
                            if method.startswith("dense:")
                            else proxy_setup[method.split(":")[0]],
                            backbone_seconds=backbone,
                            hidden_quantize_seconds=quant_seconds,
                        )
                        emit(**row)
                        if torch.cuda.max_memory_allocated() > 2 * 1024**3:
                            raise MemoryError("new CUDA allocation ceiling exceeded")
                    # Preserve every row; do not replace a slow/rejected draw.
                gc.enable()
                check_concurrency()
                emit(
                    type="case_complete",
                    case=case,
                    draws=11 * len(METHODS),
                    cuda_peak_allocated_bytes=torch.cuda.max_memory_allocated(),
                    host_peak_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
                )
            handle.remove()
            emit(
                type="complete",
                states=6,
                draws=6 * 11 * len(METHODS),
                final_processes=process_snapshot(),
                proxy_storage_bytes=heads.storage,
                cuda_peak_allocated_bytes=torch.cuda.max_memory_allocated(),
                host_peak_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
            )
        except Exception as exc:
            emit(
                type="error",
                error_type=type(exc).__name__,
                message=str(exc),
                status="ERROR_NOT_SCIENTIFIC_LOSS",
            )
            raise
        finally:
            if monitor is not None:
                monitor.terminate()
                monitor.wait(timeout=5)
                monitor_stream.close()
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--oracle", action="store_true")
    parser.add_argument("--run", type=Path)
    args = parser.parse_args()
    if args.oracle:
        oracle()
    elif args.run:
        raise SystemExit(run(args.run))
    else:
        parser.error("choose --oracle or --run NEW_DIRECTORY")
