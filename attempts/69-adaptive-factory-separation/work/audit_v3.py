"""Independent exact score, scale and finite-controller audit; no timing study."""

import hashlib
import json
import subprocess
import sys
from collections import Counter
from dataclasses import asdict
from fractions import Fraction as F
from math import comb, factorial
from pathlib import Path

from finite_v3 import parse_limit, sample_finite

HERE = Path(__file__).resolve().parent
PATTERN = (1, 0, 1, 0, 1, 1, 0, 1)


def falling(n, r):
    answer = 1
    for j in range(r):
        answer *= n - j
    return answer


def derivative_basis(m, k, r, p):
    return comb(m, k) * sum(
        (
            comb(r, a)
            * falling(k, a)
            * falling(m - k, r - a)
            * (-1) ** (r - a)
            * p ** (k - a)
            * (1 - p) ** (m - k - r + a)
            for a in range(r + 1)
            if a <= k and r - a <= m - k
        ),
        F(),
    )


def polynomial(coefficients, p):
    m = len(coefficients) - 1
    return sum(
        (b * comb(m, k) * p**k * (1 - p) ** (m - k) for k, b in enumerate(coefficients)), F()
    )


class NeedMore(Exception):
    pass


class Tape:
    def __init__(self, word):
        self.word, self.used = word, 0

    def getrandbits(self, width):
        assert width == 1
        if self.used == len(self.word):
            raise NeedMore
        answer = self.word[self.used]
        self.used += 1
        return answer


def literal(word, limit, mode):
    position = 0

    def take():
        nonlocal position
        if position == len(word):
            raise NeedMore
        result = word[position]
        position += 1
        return result

    ticket = 2 * take() + take()
    if ticket != 1:
        return dict(
            bit=int(ticket == 0),
            source_calls=0,
            auxiliary_bits=position,
            selected_level=None,
            stage="base",
        )
    n = 1
    while not take():
        n += 1
    if n > limit:
        return dict(
            bit=0, source_calls=0, auxiliary_bits=position, selected_level=n, stage="cap_rejected"
        )
    level = n * n + 4
    for _ in range(2 * level - n):
        if take():
            return dict(
                bit=0,
                source_calls=0,
                auxiliary_bits=position,
                selected_level=n,
                stage="rare_gate_rejected",
            )
    center = F(1, 2) + F(1, 2 ** (n + 2))

    def count(t):
        return 0 if mode == "zero" else 5 * (t // 8) + sum(PATTERN[: t % 8])

    for j in range(level):
        t = 4**j
        if abs(F(count(t), t) - center) > F(2 * (j + 1), 2**j):
            return dict(
                bit=0, source_calls=t, auxiliary_bits=position, selected_level=n, stage="predicate"
            )
    t = 4**level
    bit = int(abs(F(count(t), t) - center) <= F(1, 2**level))
    return dict(
        bit=bit, source_calls=t, auxiliary_bits=position, selected_level=n, stage="predicate"
    )


def execute(word, binary, mode="zero"):
    tape = Tape(word)
    calls = 0

    def source():
        nonlocal calls
        bit = 0 if mode == "zero" else PATTERN[calls % 8]
        calls += 1
        return bit

    answer = sample_finite(source, tape, binary)
    assert answer.source_calls == calls and answer.auxiliary_bits == tape.used
    return asdict(answer)


def main(destination):
    counts = Counter()
    records = []
    for m in range(33):
        for p in (F(j, 8) for j in range(1, 8)):
            for r in range(1, 5):
                values = [derivative_basis(m, k, r, p) for k in range(m + 1)]
                mass = sum(
                    (
                        v * v / (comb(m, k) * p**k * (1 - p) ** (m - k))
                        for k, v in enumerate(values)
                    ),
                    F(),
                )
                expected = F(factorial(r) * falling(m, r), 1) / (p * (1 - p)) ** r
                assert mass == expected
                norm = sum(map(abs, values), F())
                assert norm * norm <= mass
                if r == 4 and F(1, 4) <= p <= F(3, 4):
                    assert norm <= 160 * m * m
                counts["exact_score_norm_identities"] += 1
    for m in (0, 1, 2, 3, 4, 8, 16):
        patterns = (
            (F(),) * (m + 1),
            (F(1),) * (m + 1),
            tuple(F(k % 2) for k in range(m + 1)),
            tuple(F(k >= m // 2) for k in range(m + 1)),
            tuple(F((k * k + 1) % 7, 6) for k in range(m + 1)),
        )
        for coefficients in patterns:
            for n in (4, 5, 6):
                center = F(1, 2) + F(1, 2 ** (n + 2))
                big = 4 ** (n * n + 4)
                h = F(4, 2 ** (n * n + 4))
                values = [polynomial(coefficients, center + j * h) for j in (-2, -1, 0, 1, 2)]
                diff = (values[0] - 4 * values[1] + 6 * values[2] - 4 * values[3] + values[4]) / (
                    h * h
                )
                assert abs(diff) <= min(F(2560 * m * m, big), F(big))
                counts["exact_bounded_polynomial_differences"] += 1
    grid = sorted(set(range(129)) | {max(0, 2**j + d) for j in range(81) for d in (-1, 0, 1)})
    for m in grid:
        total = sum(
            (min(F(2560 * m * m, 4 ** (n * n + 4)), F(4 ** (n * n + 4))) for n in range(4, 65)), F()
        )
        assert total <= 128 * m
        counts["multiscale_majorant_sums"] += 1
    assert F(64, 63) * (64 + 40) < 128
    assert 40 * (2**10 + 2**16) + F(1, 4) < 2**22
    peak = 6 * (F(3, 4) - F(2, 255)) - 8 * F(1, 2**17)
    assert F(3, 4) - F(2, 255) >= F(37, 50) and F(1, 2**17) < F(1, 100)
    assert peak / 64 - F(1, 2**14) > F(1, 16)
    assert F(10, 4**8) / (1 - F(1, 4**11)) < 1
    counts["global_rational_constant_certificates"] += 5
    for j in range(3, 65):
        exponent = 2 * j * j - 2 * j - 3
        assert 2**exponent >= 6 * j * j + j + 31
        assert 6 * (j + 1) ** 2 + (j + 1) + 31 <= 4 * (6 * j * j + j + 31)
        counts["offcentre_induction_checks"] += 1
    for n in range(4, 65):
        level = n * n + 4
        h = F(4, 2**level)
        radius = F(1, 2 ** (n + 5))
        assert 2 * h < radius
        assert F(2**26, 4**level) <= F(1, 2**14)
        assert 4 * n + 42 <= 2 ** (n + 14)
        counts["localisation_interference_budget_scales"] += 1
    for limit in (0, 1, 2, 3, 30):
        binary = format(limit, "b")
        for width in (4, 8, 12):
            ones = unresolved = 0
            for encoded in range(2**width):
                word = tuple((encoded >> j) & 1 for j in range(width))
                try:
                    actual = execute(word, binary)
                except NeedMore:
                    try:
                        literal(word, limit, "zero")
                    except NeedMore:
                        pass
                    else:
                        raise AssertionError("Only implementation unresolved")
                    unresolved += 1
                else:
                    expected = literal(word, limit, "zero")
                    assert actual == expected
                    ones += actual["bit"]
                counts["finite_auxiliary_word_transcripts"] += 1
            assert F(ones, 2**width) <= F(1, 4) <= F(ones + unresolved, 2**width)
            records.append(dict(limit=limit, width=width, ones=ones, unresolved=unresolved))
    for binary in ("0", "1", "10", "11", "11110", "1" + "0" * 4096):
        limit = int(binary, 2)
        for n in (1, 2, 3, 30):
            level = n * n + 4
            word = (0, 1) + (0,) * (n - 1) + (1,) + (0,) * (2 * level - n)
            for mode in ("zero", "periodic") if n == 1 else ("zero",):
                actual = execute(word, binary, mode)
                expected = literal(word, limit, mode)
                assert actual == expected
                records.append(
                    dict(binary_length=len(binary), selected_n=n, mode=mode, result=actual)
                )
                counts["forced_finite_controllers"] += 1
    for invalid in ("", "01", "00", "10x", "-1", None, 1):
        try:
            parse_limit(invalid)
        except ValueError:
            counts["invalid_input_guards"] += 1
        else:
            raise AssertionError("Invalid binary accepted")
    for bad in (2, 0.0):
        try:
            sample_finite(lambda: 0, Tape((bad,)), "1")
        except ValueError:
            counts["invalid_input_guards"] += 1
        else:
            raise AssertionError("Invalid auxiliary bit accepted")
    word = (0, 1, 1) + (0,) * 9
    try:
        sample_finite(lambda: 2, Tape(word), "1")
    except ValueError:
        counts["invalid_input_guards"] += 1
    else:
        raise AssertionError("Invalid source bit accepted")
    names = (
        "finite_v3.py",
        "audit_v3.py",
        "separation.py",
        "quantitative-gap-v3.md",
        "protocol-v3.md",
        "primary-v3.md",
    )
    summary = dict(
        status="PASS",
        source_commit=subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
        counts=dict(counts),
        hashes={n: hashlib.sha256((HERE / n).read_bytes()).hexdigest() for n in names},
        scope="Finite proof certificates; general theorem/priority/natural use unverified",
        goal="OPEN",
    )
    target = Path(destination)
    target.mkdir(parents=True, exist_ok=False)
    (target / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    (target / "finite-transcripts.json").write_text(json.dumps(records, indent=2) + "\n")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main(sys.argv[1])
