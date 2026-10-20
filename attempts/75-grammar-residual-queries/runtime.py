"""Bounded CPU oracle consumer with counted random bits and explicit refusals.

Finite intervals can refuse; the ideal Q_B law belongs to the written factory.
Optional timings acquire the shared GPU/timing lock before reading any clock.
"""

from __future__ import annotations

import argparse
import fcntl
import json
import random
import resource
import subprocess
import time
from fractions import Fraction as F
from pathlib import Path

import oracle

PURPOSES = ("reference", "mask", "poisson", "accept", "token", "pair")


class Inconclusive(RuntimeError):
    pass


class Bits(random.Random):
    def __init__(self, seed):
        super().__init__(seed)
        self.bits = 0

    def getrandbits(self, k):
        self.bits += k
        return super().getrandbits(k)


def subset(n, k, rng):
    values = list(range(n))
    for i in range(k):
        j = rng.randrange(i, n)
        values[i], values[j] = values[j], values[i]
    return sum(1 << i for i in values[:k])


def bernoulli_interval(p, rng):
    value, bits = 0, 0
    for _ in range(257):
        if F(value + 1, 1 << bits) <= F(p.lo, oracle.SCALE):
            return True
        if F(value, 1 << bits) >= F(p.hi, oracle.SCALE):
            return False
        if bits == 256:
            break
        value = 2 * value + rng.getrandbits(1)
        bits += 1
    raise Inconclusive("256-bit interval Bernoulli decision unresolved")


def poisson(rate, rng):
    probability = oracle.exp(oracle.Interval.of(-rate))
    cumulative = probability
    value, bits, j = 0, 0, 0
    while j < 1024:
        if F(value + 1, 1 << bits) <= F(cumulative.lo, oracle.SCALE):
            return j
        if F(value, 1 << bits) >= F(cumulative.hi, oracle.SCALE):
            j += 1
            probability = probability * rate / j
            cumulative += probability
        elif bits < 256:
            value = 2 * value + rng.getrandbits(1)
            bits += 1
        else:
            raise Inconclusive("256-bit Poisson inversion unresolved")
    raise Inconclusive("Poisson inversion exceeded 1024 terms")


def rational_coin(p, rng):
    return rng.randrange(p.denominator) < p.numerator


def reference_ones(n, mask, value):
    remaining = n - mask.bit_count()
    k = n // 2 - value.bit_count()
    return tuple(
        F(int(bool(value & (1 << i)))) if mask & (1 << i) else F(k, remaining) for i in range(n)
    )


def draw(n, alpha, query, control, rngs):
    proposals = 0
    if control == "reference":
        return subset(n, n // 2, rngs["reference"]), 1
    if control == "sequential_closure":
        mask, value = 0, 0
        for i in range(n):
            r = reference_ones(n, mask, value)[i]
            p = r if r in (0, 1) else query(mask, value)[i]
            if rational_coin(p, rngs["token"]):
                value |= 1 << i
            mask |= 1 << i
        return value, 0
    if control == "pair_heat_bath_n_updates":
        value = subset(n, n // 2, rngs["reference"])
        for _ in range(n):
            pair = subset(n, 2, rngs["pair"])
            i = (pair & -pair).bit_length() - 1
            j = (pair ^ (1 << i)).bit_length() - 1
            if bool(value & (1 << i)) == bool(value & (1 << j)):
                continue
            mask = ((1 << n) - 1) ^ pair
            p = query(mask, value & mask)[i]
            if rational_coin(p, rngs["token"]):
                value = (value | (1 << i)) & ~(1 << j)
            else:
                value = (value | (1 << j)) & ~(1 << i)
        return value, 1
    if control != "residual_no_short_circuit":
        raise ValueError(control)
    for _ in range(10000):
        proposals += 1
        value = subset(n, n // 2, rngs["reference"])
        j = poisson(2 * alpha, rngs["poisson"])
        accept = oracle.Interval.of(1)
        for _ in range(j):
            size = rngs["mask"].randrange(n)
            mask = subset(n, size, rngs["mask"])
            pins = value & mask
            p = query(mask, pins)
            r = reference_ones(n, mask, pins)
            w = oracle.increment(n, value, mask, p, r)
            assert w is not None
            accept *= (w.clip(alpha) + alpha) / (2 * alpha)
        # Intentionally no early rejection: all j queries above are charged.
        if bernoulli_interval(accept, rngs["accept"]):
            return value, proposals
    raise Inconclusive("10000 proposal cap reached")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--timing", action="store_true")
    args = parser.parse_args()
    lock = None
    gpu = None
    if args.timing:
        lock = open(oracle.PROTOCOL["timing"]["lock"], "a+")
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            print("TIMING_DEFERRED_LOCK_BUSY: no clocks read, no GPU use", flush=True)
            return
        gpu = subprocess.run(
            ["nvidia-smi", "--query-gpu=name,memory.used,utilization.gpu", "--format=csv,noheader"],
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip()
        processes = subprocess.run(
            [
                "nvidia-smi",
                "--query-compute-apps=pid,process_name,used_memory",
                "--format=csv,noheader",
            ],
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip()
        if processes:
            print("TIMING_DEFERRED_GPU_PROCESS_PRESENT: " + processes, flush=True)
            return
    with args.output.open("x") as output:
        output.write(
            json.dumps(
                {
                    "kind": "runtime_contract",
                    "timed": args.timing,
                    "nvidia_smi": gpu,
                    "samples": 64,
                    "seed_formula": "750019 + 10000*case_index + 100*control_index + purpose_index",
                    "finite_cap": "256 decision bits; refusal is retained, no replacement",
                    "model_forwards": 0,
                }
            )
            + "\n"
        )
        output.flush()
        for ci, (n, alpha, name) in enumerate(oracle.cases()):
            if name == "hard_core":
                continue
            for ai, control in enumerate(oracle.PROTOCOL["runtime"]["controls"]):
                wall0 = time.perf_counter() if args.timing else None
                cpu0 = time.process_time() if args.timing else None
                # Cold truth-oracle construction is charged separately and in total.
                case = None if control == "reference" else oracle.make_case(n, alpha, name)
                prep_wall = time.perf_counter() - wall0 if args.timing else None
                prep_cpu = time.process_time() - cpu0 if args.timing else None
                oracle.log.cache_clear()
                rngs = {
                    purpose: Bits(750019 + 10000 * ci + 100 * ai + pi)
                    for pi, purpose in enumerate(PURPOSES)
                }
                outputs, failures, proposals = [], [], 0
                for sample in range(64):
                    try:
                        value, proposed = draw(
                            n, alpha, None if case is None else case.oracle.query, control, rngs
                        )
                        assert value.bit_count() == n // 2
                        outputs.append(value)
                        proposals += proposed
                    except Inconclusive as error:
                        failures.append(
                            {
                                "sample_index": sample,
                                "status": "RESOURCE_INCONCLUSIVE",
                                "reason": str(error),
                            }
                        )
                row = {
                    "kind": "runtime",
                    "n": n,
                    "alpha": str(alpha),
                    "target": name,
                    "control": control,
                    "successful_outputs": len(outputs),
                    "failures": failures,
                    "oracle_queries": 0 if case is None else case.oracle.queries,
                    "reference_proposals": proposals,
                    "output_slots": len(outputs) * n,
                    "rng_bits": {k: r.bits for k, r in rngs.items()},
                    "max_oracle_integer_bits": 0 if case is None else case.oracle.max_bits,
                    "oracle_cylinders": 0 if case is None else len(case.oracle.table),
                    "log_cache": oracle.log.cache_info()._asdict(),
                    "peak_process_RSS_KiB_cumulative": resource.getrusage(
                        resource.RUSAGE_SELF
                    ).ru_maxrss,
                    "outputs": outputs,
                    "status": "PASS" if not failures else "RESOURCE_INCONCLUSIVE",
                }
                if args.timing:
                    row.update(
                        {
                            "wall_total_s": time.perf_counter() - wall0,
                            "cpu_total_s": time.process_time() - cpu0,
                            "wall_preparation_s": prep_wall,
                            "cpu_preparation_s": prep_cpu,
                        }
                    )
                output.write(json.dumps(row, sort_keys=True) + "\n")
                output.flush()
                print(
                    json.dumps(
                        {
                            k: row[k]
                            for k in ("n", "alpha", "target", "control", "status", "oracle_queries")
                        }
                    ),
                    flush=True,
                )
    if lock is not None:
        fcntl.flock(lock, fcntl.LOCK_UN)


if __name__ == "__main__":
    main()
