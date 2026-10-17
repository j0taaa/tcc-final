"""Frozen small native-FP audit; no competitive timing or neural execution."""

from __future__ import annotations

import argparse
import ctypes as ct
import hashlib
import itertools
import json
import math
import platform
import struct
import subprocess
import tempfile
from fractions import Fraction as F
from functools import lru_cache
from pathlib import Path


class State(ct.Structure):
    _fields_ = [(name, ct.c_float) for name in ("w", "m", "v")]


class Coeff(ct.Structure):
    _fields_ = [(name, ct.c_float) for name in ("a", "d")]


def bits(x: float) -> int:
    return struct.unpack("<I", struct.pack("<f", x))[0]


def value(b: int) -> float:
    return struct.unpack("<f", struct.pack("<I", b))[0]


def f32(x: float) -> float:
    return value(bits(x))


@lru_cache(maxsize=65536)
def frac(b: int) -> F:
    return F.from_float(value(b))


def exact(x: float) -> F:
    return frac(bits(x))


def rn(q: F) -> float:
    """Independent nearest-even rounding by exact finite-grid comparisons."""
    sign = q < 0
    q = abs(q)
    if not q:
        return 0.0
    low, high = 0, 0x7F7FFFFF
    if q > frac(high):
        raise ValueError("oracle overflow outside admitted finite contract")
    while low < high:
        middle = (low + high + 1) // 2
        if frac(middle) <= q:
            low = middle
        else:
            high = middle - 1
    if frac(low) == q:
        selected = low
    else:
        upper = low + 1
        midpoint = (frac(low) + frac(upper)) / 2
        selected = low if q < midpoint or (q == midpoint and low % 2 == 0) else upper
    return value(selected | (0x80000000 if sign else 0))


def sqrt_r(x: float) -> float:
    q = exact(x)
    assert q >= 0
    low, high = 0, 0x7F7FFFFF
    while low < high:
        middle = (low + high + 1) // 2
        if frac(middle) ** 2 <= q:
            low = middle
        else:
            high = middle - 1
    if frac(low) ** 2 == q:
        return value(low)
    midpoint = (frac(low) + frac(low + 1)) / 2
    return value(low if q < midpoint**2 or (q == midpoint**2 and low % 2 == 0) else low + 1)


def add(x: float, y: float) -> float:
    q = exact(x) + exact(y)
    if not q:
        return -0.0 if bits(x) == bits(y) == 0x80000000 else 0.0
    return rn(q)


def mul(x: float, y: float) -> float:
    q = exact(x) * exact(y)
    if not q:
        return value((bits(x) ^ bits(y)) & 0x80000000)
    return rn(q)


def div(x: float, y: float) -> float:
    q = exact(x) / exact(y)
    if not q:
        return value((bits(x) ^ bits(y)) & 0x80000000)
    return rn(q)


def oracle_step(s: State, g: float, c: Coeff, b1: float, b2: float, eps: float) -> State:
    c1, c2 = rn(1 - exact(b1)), rn(1 - exact(b2))
    m = add(mul(b1, s.m), mul(c1, g))
    v = add(mul(b2, s.v), mul(mul(c2, g), g))
    z = add(div(sqrt_r(v), c.d), eps)
    update = div(mul(c.a, m), z)
    return State(add(s.w, -update), m, v)


def state_bits(s: State) -> list[int]:
    return [bits(s.w), bits(s.m), bits(s.v)]


@lru_cache
def constants(beta: float) -> tuple[int, F]:
    if not 0 < beta < 1:
        raise ValueError("beta outside(0,1)")
    delta = 1 - exact(beta) * (1 + F(1, 1 << 24))
    assert delta > 0
    m = (delta.denominator + delta.numerator - 1) // delta.numerator
    return m, F(1, 1 << 150) / delta


def bound(x: float, beta: float, gap: int) -> tuple[float, int]:
    if gap < 0 or not math.isfinite(x) or x < 0:
        raise ValueError("invalid enclosure input")
    period, floor = constants(beta)
    exponent = min(gap // period, 512)
    q = exact(x) / (1 << exponent) + floor
    out = rn(q)
    if exact(out) < q:
        out = value(bits(out) + 1)
    return out, exponent


def native_library(path: Path):
    lib = ct.CDLL(str(path))
    lib.init_fp.restype = ct.c_int
    assert lib.init_fp() == 1, "unsupported FP environment"
    lib.make_schedule.argtypes = [ct.POINTER(Coeff), ct.c_int] + [ct.c_float] * 3
    lib.step.argtypes = [State, ct.c_float, Coeff] + [ct.c_float] * 3
    lib.step.restype = State
    lib.moments.argtypes = [State] + [ct.c_float] * 3
    lib.moments.restype = State
    lib.weight.argtypes = [State, Coeff, ct.c_float]
    lib.weight.restype = State
    lib.run_zero.argtypes = [State, ct.c_int, ct.c_int, ct.POINTER(Coeff)] + [ct.c_float] * 3
    lib.run_zero.restype = State
    lib.decay.argtypes = [State, ct.c_int, ct.c_float, ct.c_float]
    lib.decay.restype = State
    lib.update_bound.argtypes = [ct.c_float] * 3
    lib.update_bound.restype = ct.c_float
    lib.sub_round.argtypes = [ct.c_float] * 2
    lib.sub_round.restype = ct.c_float
    for name in ("add_round", "mul_round", "div_round"):
        function = getattr(lib, name)
        function.argtypes = [ct.c_float, ct.c_float]
        function.restype = ct.c_float
    lib.sqrt_round.argtypes = [ct.c_float]
    lib.sqrt_round.restype = ct.c_float
    return lib


def validate(s: State, b1: float, b2: float, eps: float, c: Coeff, maximum: float) -> None:
    if not all(math.isfinite(x) for x in (s.w, s.m, s.v, b1, b2, eps, c.a, c.d, maximum)):
        raise ValueError("nonfinite input")
    if not (0 < b1 < 1 and 0 < b2 < 1 and eps > 0 and c.d > 0 and 0 <= c.a <= maximum):
        raise ValueError("invalid scalar/configuration")
    if s.v < 0:
        raise ValueError("negative variance")


def guard(lib, s: State, maximum: float, eps: float) -> bool:
    if not math.isfinite(s.w) or not s.w:
        return False
    upper = lib.update_bound(maximum, s.m, eps)
    if not math.isfinite(upper):
        return False
    signed = -upper if math.copysign(1, s.m) < 0 else upper
    return bits(lib.sub_round(s.w, signed)) == bits(s.w)


def lazy(lib, start: State, s: int, h: int, g: float, table, config, maximum: float):
    b1, b2, eps = config
    validate(start, b1, b2, eps, table[s + h + 1], maximum)
    current = State(start.w, start.m, start.v)
    head = 0
    frozen = guard(lib, current, maximum, eps)
    while head < min(512, h) and not frozen:
        current = lib.step(current, 0, table[s + head + 1], b1, b2, eps)
        head += 1
        frozen = guard(lib, current, maximum, eps)
    remaining = h - head
    erased = False
    replayed = remaining
    if not frozen:
        current = lib.run_zero(current, s + head + 1, remaining, table, b1, b2, eps)
        read = current.w
        final = lib.step(current, g, table[s + h + 1], b1, b2, eps)
    else:
        read = current.w
        um, _ = bound(abs(current.m), b1, remaining)
        uv, _ = bound(current.v, b2, remaining)
        lower_m, upper_m = (-um, 0.0) if current.m < 0 else (0.0, um)
        left = lib.moments(State(0, lower_m, 0), g, b1, b2)
        right = lib.moments(State(0, upper_m, uv), g, b1, b2)
        erased = all(
            math.isfinite(x) and x != 0 and bits(x) == bits(y)
            for x, y in ((left.m, right.m), (left.v, right.v))
        )
        if erased:
            final = lib.weight(State(read, left.m, left.v), table[s + h + 1], eps)
            replayed = 0
        else:
            current = lib.decay(current, remaining, b1, b2)
            final = lib.step(current, g, table[s + h + 1], b1, b2, eps)
    return (
        read,
        final,
        dict(
            head=head,
            frozen=frozen,
            erased=erased,
            zero_moment_steps=head + replayed,
            zero_weight_steps=head if frozen else h,
            control_absorption_moment_steps=h,
            native_zero_steps=h,
        ),
    )


def run(out: Path, lib, source: dict, compiler: str, flags: list[str]) -> None:
    b1, b2, eps, eta = map(f32, (0.9, 0.999, 1e-8, 0.001))
    config = (b1, b2, eps)
    gaps = (0, 1, 15, 128, 512, 4096, 32768, 65536)
    size = 1024 + max(gaps) + 2
    table = (Coeff * size)()
    lib.make_schedule(table, size, eta, b1, b2)
    assert all(math.isfinite(c.a) and math.isfinite(c.d) and c.a > 0 and c.d > 0 for c in table[1:])
    maximum = max(c.a for c in table[1:])
    raw = bytes(table)
    (out / "schedule.f32").write_bytes(raw)
    counts = dict(cases=0, short_oracle=0, frozen=0, erased=0, nontrivial_erased=0)
    corpus = [value(i) for i in (0, 1, 0x007FFFFF, 0x00800000, 0x3F7FFFFF, 0x3F800000, 0x3F800001)]
    corpus += [-0.0, -value(1), -1.0, f32(0.1), f32(0.999), f32(1e20)]
    primitives = []
    for name, operation in (("add_round", add), ("mul_round", mul), ("div_round", div)):
        for x, y in itertools.product(corpus, repeat=2):
            if name == "div_round" and not y:
                continue
            actual = getattr(lib, name)(x, y)
            if not math.isfinite(actual):
                primitives.append(
                    dict(operation=name, x=bits(x), y=bits(y), status="OUTSIDE_FINITE")
                )
                continue
            expected = operation(x, y)
            assert bits(actual) == bits(expected), (name, bits(x), bits(y))
            primitives.append(
                dict(operation=name, x=bits(x), y=bits(y), result=bits(actual), status="PASS")
            )
    for x in corpus:
        if x >= 0 and bits(x) != 0x80000000:
            actual = lib.sqrt_round(x)
            assert bits(actual) == bits(sqrt_r(x))
            primitives.append(
                dict(operation="sqrt_round", x=bits(x), result=bits(actual), status="PASS")
            )
    (out / "primitives.json").write_text(json.dumps(primitives, indent=2) + "\n")
    zero_reset_counterexample = None
    with (out / "cases.jsonl").open("w") as stream:
        product = itertools.product(
            (-1, -0.01, 0.01, 1), (1, 1024), (-0.1, 0.001, 0.1), (-0.2, 0, 0.0001, 0.2), gaps
        )
        for w0, s, g0, g, h in product:
            w0, g0, g = map(f32, (w0, g0, g))
            initial = lib.step(State(w0, 0, 0), g0, table[s], *config)
            eager_read = lib.run_zero(initial, s + 1, h, table, *config)
            eager = lib.step(eager_read, g, table[s + h + 1], *config)
            read, final, work = lazy(lib, initial, s, h, g, table, config, maximum)
            assert bits(read) == bits(eager_read.w), (counts["cases"], "read")
            assert state_bits(final) == state_bits(eager), (counts["cases"], "next state")
            control = lib.run_zero(initial, s + 1, work["head"], table, *config)
            if work["frozen"]:
                control = lib.decay(control, h - work["head"], b1, b2)
            else:
                control = lib.run_zero(
                    control, s + work["head"] + 1, h - work["head"], table, *config
                )
            assert state_bits(lib.step(control, g, table[s + h + 1], *config)) == state_bits(eager)
            if h <= 15:
                oracle = oracle_step(State(w0, 0, 0), g0, table[s], *config)
                assert state_bits(oracle) == state_bits(initial)
                for t in range(s + 1, s + h + 1):
                    oracle = oracle_step(oracle, 0.0, table[t], *config)
                assert state_bits(oracle) == state_bits(eager_read)
                oracle = oracle_step(oracle, g, table[s + h + 1], *config)
                assert state_bits(oracle) == state_bits(eager)
                counts["short_oracle"] += 1
            reset = lib.step(State(eager_read.w, 0, 0), g, table[s + h + 1], *config)
            if zero_reset_counterexample is None and state_bits(reset) != state_bits(eager):
                zero_reset_counterexample = dict(
                    case=counts["cases"], true=state_bits(eager), reset=state_bits(reset)
                )
            counts["cases"] += 1
            counts["frozen"] += int(work["frozen"])
            counts["erased"] += int(work["erased"])
            counts["nontrivial_erased"] += int(
                work["erased"] and work["head"] < h and initial.m != 0 and initial.v != 0
            )
            row = dict(
                status="COMPLETE",
                case=counts["cases"] - 1,
                s=s,
                h=h,
                w0=bits(w0),
                g0=bits(g0),
                g=bits(g),
                initial=state_bits(initial),
                read=bits(read),
                final=state_bits(final),
                work=work,
            )
            stream.write(json.dumps(row, sort_keys=True) + "\n")
    assert counts["cases"] == 768 and counts["short_oracle"] == 288
    assert counts["nontrivial_erased"] > 0 and zero_reset_counterexample is not None

    xs = [value(i) for i in (1, 0x007FFFFF, 0x00800000, 0x00800001)]
    xs += [f32(x) for x in (1e-20, 1e-8, 0.001, 1, 1e20)]
    enclosures = []
    for beta, x, h in itertools.product((b1, b2), xs, gaps):
        actual = lib.decay(State(1, x, x), h, beta, beta)
        upper, exponent = bound(x, beta, h)
        assert abs(actual.m) <= upper and 0 <= actual.v <= upper
        negative = lib.decay(State(1, -x, x), h, beta, beta)
        assert -upper <= negative.m <= 0
        enclosures.append(
            dict(
                beta=bits(beta),
                x=bits(x),
                h=h,
                actual=state_bits(actual),
                negative=state_bits(negative),
                upper=bits(upper),
                exponent=exponent,
            )
        )
    fixed = []
    for beta in (b1, b2):
        s = lib.decay(State(1, value(1), value(1)), 65536, beta, beta)
        assert bits(s.m) == bits(s.v) == 1
        fixed.append(dict(beta=bits(beta), final=state_bits(s)))
    huge = []
    for h in (1 << 128, 1 << 1024):
        for beta in (b1, b2):
            upper, exponent = bound(f32(0.001), beta, h)
            assert exponent == 512 and upper > 0
            huge.append(
                dict(
                    gap_binary_length=h.bit_length(),
                    beta=bits(beta),
                    upper=bits(upper),
                    exponent=exponent,
                    eager_run=False,
                )
            )

    separate = 1.0
    for _ in range(4):
        separate = lib.sub_round(separate, 2.0**-26)
    aggregate = lib.sub_round(1, 2.0**-24)
    assert bits(separate) == bits(1.0) and bits(aggregate) != bits(separate)
    assert not guard(lib, State(0.0, 1, 1), maximum, eps)
    assert not guard(lib, State(-0.0, 1, 1), maximum, eps)
    bad_inputs = [
        (State(1, 1, -1), b1, b2, eps, Coeff(1, 1), 1),
        (State(math.nan, 1, 1), b1, b2, eps, Coeff(1, 1), 1),
        (State(1, 1, 1), 1, b2, eps, Coeff(1, 1), 1),
        (State(1, 1, 1), b1, 0, eps, Coeff(1, 1), 1),
        (State(1, 1, 1), b1, b2, 0, Coeff(1, 1), 1),
        (State(1, 1, 1), b1, b2, eps, Coeff(1, 0), 1),
        (State(1, 1, 1), b1, b2, eps, Coeff(-1, 1), 1),
        (State(1, 1, 1), b1, b2, eps, Coeff(2, 1), 1),
    ]
    for args in bad_inputs:
        try:
            validate(*args)
        except ValueError:
            continue
        raise AssertionError("invalid configuration admitted")
    details = dict(
        enclosures=enclosures,
        fixed_points=fixed,
        huge_gaps=huge,
        zero_reset_counterexample=zero_reset_counterexample,
        absorption=dict(separate=bits(separate), aggregate=bits(aggregate)),
        refusals=len(bad_inputs),
        signed_zero_guards=2,
    )
    (out / "boundaries.json").write_text(json.dumps(details, indent=2) + "\n")
    result = dict(
        status="PASS",
        kind="Constructed scalar correctness; no real workload, timing or neural execution",
        counts=counts,
        enclosure_checks=len(enclosures),
        primitive_checks=sum(row["status"] == "PASS" for row in primitives),
        primitive_outside_finite=sum(row["status"] == "OUTSIDE_FINITE" for row in primitives),
        config_bits=dict(
            beta1=bits(b1), beta2=bits(b2), eps=bits(eps), eta=bits(eta), max_step=bits(maximum)
        ),
        head_cap=512,
        source=source,
        compiler=compiler,
        flags=flags,
        platform=platform.platform(),
        python=platform.python_version(),
        schedule=dict(
            rows=size,
            bytes=len(raw),
            sha256=hashlib.sha256(raw).hexdigest(),
            kind="Native supplied scalar bits; not correctly-rounded pow theorem",
        ),
        artifacts={
            p.name: hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(out.iterdir())
            if p.is_file()
        },
    )
    (out / "summary.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[3]
    here = Path(__file__).resolve().parent
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip()
    source = dict(commit=commit, files={})
    for name in (
        "native_v1.c",
        "audit_v1.py",
        "theory-v1.md",
        "protocol-v1.md",
        "protocol-implementation-v1.md",
    ):
        path = here / name
        relative = str(path.relative_to(root))
        frozen = subprocess.check_output(["git", "show", f"{commit}:{relative}"], cwd=root)
        assert frozen == path.read_bytes(), f"source not frozen:{relative}"
        source["files"][relative] = hashlib.sha256(frozen).hexdigest()
    args.output.mkdir(parents=True, exist_ok=False)
    compiler = subprocess.check_output(["cc", "--version"], text=True).splitlines()[0]
    flags = [
        "-std=c11",
        "-O2",
        "-fPIC",
        "-shared",
        "-ffp-contract=off",
        "-fno-fast-math",
        "-fexcess-precision=standard",
    ]
    with tempfile.TemporaryDirectory(prefix="a70-native-v1-") as tmp:
        library = Path(tmp) / "native.so"
        result = subprocess.run(
            ["cc", *flags, str(here / "native_v1.c"), "-lm", "-o", str(library)],
            capture_output=True,
            text=True,
        )
        (args.output / "build.json").write_text(
            json.dumps(
                dict(
                    command=["cc", *flags, "native_v1.c", "-lm", "-o", "native.so"],
                    exit_code=result.returncode,
                    stdout=result.stdout,
                    stderr=result.stderr,
                ),
                indent=2,
            )
            + "\n"
        )
        result.check_returncode()
        run(args.output, native_library(library), source, compiler, flags)


if __name__ == "__main__":
    main()
