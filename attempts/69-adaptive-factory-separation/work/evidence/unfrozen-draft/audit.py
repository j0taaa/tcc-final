"""Independent finite-word/leaf laws and arithmetic checks, not a benchmark."""

import hashlib
import json
import subprocess
import sys
from collections import Counter, defaultdict
from dataclasses import asdict
from fractions import Fraction as F
from math import comb
from pathlib import Path

from separation import predicate, sample

HERE = Path(__file__).resolve().parent


class Tape:
    def __init__(self, word):
        self.word, self.used = word, 0

    def getrandbits(self, width):
        assert width == 1 and self.used < len(self.word), "Unexpected auxiliary consumption"
        bit = self.word[self.used]
        self.used += 1
        return bit


def literal(word, center, level, width):
    total = 0
    checks = {4**j: j for j in range(level)}
    for length, bit in enumerate(word, 1):
        total += bit
        if length in checks:
            j = checks[length]
            if abs(F(total, length) - center) > width * F(j + 1, 2**j):
                return 0, length
    return int(abs(F(total, len(word)) - center) <= F(1, 2**level)), len(word)


def leaves(center, level, width):
    active, terminal = {0: 1}, Counter()
    checks = {4**j: j for j in range(level)}
    for length in range(1, 4**level + 1):
        expanded = defaultdict(int)
        for k, count in active.items():
            expanded[k] += count
            expanded[k + 1] += count
        active = {}
        for k, count in expanded.items():
            failed = length in checks and abs(F(k, length) - center) > width * F(
                checks[length] + 1, 2 ** checks[length]
            )
            if failed or length == 4**level:
                bit = int(not failed and abs(F(k, length) - center) <= F(1, 2**level))
                terminal[length, k, bit] += count
            else:
                active[k] = count
    assert not active
    return terminal


def main(destination):
    counts, cases = Counter(), []
    for center in (F(1, 4), F(1, 2), F(5, 8)):
        for level in (1, 2):
            for width in (F(1, 8), F(2)):
                length = 4**level
                histogram = Counter()
                digest = hashlib.sha256()
                for encoded in range(2**length):
                    word = tuple((encoded >> j) & 1 for j in range(length))
                    source = iter(word)
                    actual = predicate(lambda source=source: next(source), center, level, width)
                    expected = literal(word, center, level, width)
                    assert actual == expected
                    histogram[sum(word), *actual] += 1
                    digest.update(bytes(actual))
                    counts["enumerated_full_word_transcripts"] += 1
                stopped = leaves(center, level, width)
                for p in (F(), F(1, 4), F(1, 2), F(3, 4), F(1)):
                    enum_output = enum_work = dp_output = dp_work = dp_mass = F()
                    for (k, bit, used), count in histogram.items():
                        weight = count * p**k * (1 - p) ** (length - k)
                        enum_output += weight * bit
                        enum_work += weight * used
                    for (used, k, bit), count in stopped.items():
                        weight = count * p**k * (1 - p) ** (used - k)
                        dp_output += weight * bit
                        dp_work += weight * used
                        dp_mass += weight
                    assert dp_mass == 1 and dp_output == enum_output and dp_work == enum_work
                    cases.append(
                        dict(
                            center=str(center),
                            level=level,
                            width=str(width),
                            p=str(p),
                            output=str(dp_output),
                            mean_calls=str(dp_work),
                            word_result_sha256=digest.hexdigest(),
                        )
                    )
                    counts["independent_stopped_leaf_laws"] += 1
    transcripts = []

    def forbidden():
        raise AssertionError("Source used before a passed rare gate")

    for word in ((0, 0), (1, 0), (1, 1), (0, 1, 1, 1), (0, 1, 0, 1, 1)):
        tape = Tape(word)
        result = sample(forbidden, tape)
        assert result.auxiliary_bits == tape.used == len(word) and result.source_calls == 0
        assert result.bit == int(word == (0, 0))
        transcripts.append(asdict(result))
        counts["auxiliary_tickets"] += 1
    for n in (1, 2, 3, 30):
        level = n * n + 4
        word = (0, 1) + (0,) * (n - 1) + (1,) + (0,) * (2 * level - n)
        tape = Tape(word)
        observed = []

        def source(observed=observed):
            observed.append(0)
            return 0

        result = sample(source, tape)
        assert result.bit == 0 and result.source_calls == len(observed) == 1024
        assert result.auxiliary_bits == tape.used == len(word)
        assert (4**level) * F((2 ** (n + 1)) + 1, 2 ** (n + 2)) > 2**level
        transcripts.append(asdict(result))
        counts["forced_rare_zero_sources"] += 1
    pattern = (1, 0, 1, 0, 1, 1, 0, 1)
    seen = []

    def periodic():
        bit = pattern[len(seen) % len(pattern)]
        seen.append(bit)
        return bit

    result = sample(periodic, Tape((0, 1, 1) + (0,) * 9))
    assert result.bit == 1 and result.source_calls == len(seen) == 1024
    transcripts.append(asdict(result))
    counts["forced_accepting_predicate"] += 1
    center, level = F(5, 8), 5
    total = 4**level
    for j in range(level):
        assert max(4**j * center, 4**j * (1 - center)) <= 2 * (j + 1) * 2**j
    values = []
    for p in (center - F(4, 2**level), center, center + F(4, 2**level)):
        values.append(
            sum((F(comb(total, k)) * p**k * (1 - p) ** (total - k) for k in range(608, 673)), F())
        )
    assert values[1] >= F(37, 50) and max(values[0], values[2]) < F(1, 100)
    assert (values[0] - 2 * values[1] + values[2]) / 16 <= -F(1, 16)
    counts["exact_first_member_curvature_certificate"] += 1
    for degree in range(33):
        for p in (F(j, 8) for j in range(1, 8)):
            norm = F()
            for k in range(degree + 1):
                weight = comb(degree, k) * p**k * (1 - p) ** (degree - k)
                score = (
                    (k - degree * p) ** 2 / (p * p * (1 - p) ** 2)
                    - k / (p * p)
                    - (degree - k) / (1 - p) ** 2
                )
                norm += abs(weight * score)
            assert norm <= 2 * degree / (p * (1 - p))
            counts["bernstein_second_derivative_norms"] += 1
    for u in range(41):
        j = 2 * u + 10
        assert F(2 * (j + 1), 2**j) <= F(1, 2 ** (u + 1))
        assert (4**j) * F(1 if not u else 2**4, 2 ** (4 * u)) <= 2**24
        counts["dyadic_cost_scales"] += 1
    for n in range(1, 65):
        center = F(1, 2) + F(1, 2 ** (n + 2))
        following = F(1, 2) + F(1, 2 ** (n + 3))
        assert F(1, 2 ** (n + 5)) + F(1, 2 ** (n + 6)) < center - following
        if n >= 3:
            assert F(4, 2 ** (n * n + 4)) < F(1, 2 ** (n + 5))
        counts["disjointness_and_localisation"] += 1
    for args in ((F(), 1, F(2)), (F(1, 2), 0, F(2)), (F(1, 2), 1, F()), (0.5, 1, F(2))):
        try:
            predicate(forbidden, *args)
        except (TypeError, ValueError):
            counts["invalid_input_guards"] += 1
        else:
            raise AssertionError("Invalid predicate accepted")
    try:
        predicate(lambda: 2, F(1, 2), 1)
    except ValueError:
        counts["invalid_input_guards"] += 1
    else:
        raise AssertionError("Invalid source bit accepted")
    try:
        sample(forbidden, Tape((2,)))
    except ValueError:
        counts["invalid_input_guards"] += 1
    else:
        raise AssertionError("Invalid auxiliary bit accepted")
    names = (
        "separation.py",
        "audit.py",
        "theory-v1.md",
        "preflight-contract-v1.md",
        "primary-v1.md",
    )
    summary = dict(
        status="PASS",
        source_commit=subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
        counts=dict(counts),
        hashes={n: hashlib.sha256((HERE / n).read_bytes()).hexdigest() for n in names},
        scope="Finite proof-object audit; infinite proof, natural use, timing/NN/priority unverified",
        goal="OPEN",
    )
    target = Path(destination)
    target.mkdir(parents=True, exist_ok=False)
    (target / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    (target / "finite-laws.json").write_text(json.dumps(cases, indent=2) + "\n")
    (target / "forced-transcripts.json").write_text(json.dumps(transcripts, indent=2) + "\n")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main(sys.argv[1])
