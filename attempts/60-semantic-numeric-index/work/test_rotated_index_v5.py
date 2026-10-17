"""Independent lexical JSON/coefficient arithmetic and original-tape oracles."""

import itertools
import json
import unittest
from collections import defaultdict
from fractions import Fraction
from functools import cmp_to_key

from .rotated_index_v5 import RotatedIndex


def reference(data):
    try:
        text = data.decode("ascii")
        parsed = json.loads(
            text, parse_int=lambda s: ("number", s), parse_float=lambda s: ("number", s)
        )
        if text.strip() != text or not isinstance(parsed, tuple) or parsed[0] != "number":
            return None
        mantissa, _, exponent = parsed[1].lower().partition("e")
        negative = mantissa.startswith("-")
        mantissa = mantissa.removeprefix("-")
        integer, _, fractional = mantissa.partition(".")
        coefficient = int(integer + fractional)
        if not coefficient:
            return "0", 0
        if negative:
            return None
        power = int(exponent or "0") - len(fractional)
        while coefficient % 10 == 0:
            coefficient //= 10
            power += 1
        digits = str(coefficient)
        return digits, power + len(digits) - 1
    except (UnicodeError, ValueError):
        return None


def compare(a, b):
    if a[0] == "0" or b[0] == "0":
        return (a[0] != "0") - (b[0] != "0")
    if a[1] != b[1]:
        return (a[1] > b[1]) - (a[1] < b[1])
    # Rational SIGNIFICANDS only: never build10^(the enormous decimal order).
    left = Fraction(int(a[0]), 10 ** (len(a[0]) - 1))
    right = Fraction(int(b[0]), 10 ** (len(b[0]) - 1))
    return (left > right) - (left < right)


def enumerate_source(rows, byte_of):
    result, count = defaultdict(Fraction), 0
    for tape in itertools.product(*rows):
        weight = Fraction(1)
        for token, row in zip(tape, rows, strict=True):
            weight *= row[token]
        number = reference(b"".join(byte_of[t] for t in tape))
        if number is not None:
            result[number] += weight
        count += 1
    return {v: w for v, w in result.items() if w}, count


class RotatedIndexTests(unittest.TestCase):
    def check_statistics(self, index, law):
        total = sum(law.values(), Fraction(0))
        self.assertEqual(index.mass, total)
        if not total:
            with self.assertRaisesRegex(ValueError, "EMPTY"):
                index.quantile(1)
            return 0, 0
        atoms = sorted(law, key=cmp_to_key(compare))
        probabilities, cumulative = {Fraction(1), Fraction(1, 2)}, Fraction(0)
        for atom in atoms:
            probabilities.add((cumulative + law[atom] / 2) / total)
            cumulative += law[atom]
            probabilities.add(cumulative / total)
        for probability in probabilities:
            cumulative = Fraction(0)
            for atom in atoms:
                cumulative += law[atom]
                if cumulative >= probability * total:
                    expected = atom
                    break
            self.assertEqual(index.quantile(probability), expected)
        thresholds = set(atoms) | {("0", 0), ("1", 0), ("1", 1), ("99", 1)}
        thresholds.update((s + "1", k) for s, k in atoms if s != "0")
        for threshold in thresholds:
            for inclusive in (True, False):
                expected = sum(
                    (
                        w
                        for v, w in law.items()
                        if compare(v, threshold) < 0 or (inclusive and compare(v, threshold) == 0)
                    ),
                    Fraction(0),
                )
                self.assertEqual(index.cdf(threshold, inclusive), expected / total, threshold)
        return len(probabilities), 2 * len(thresholds)

    def test_all_magnitudes_aliases_and_zero_without_real_expansion(self):
        huge = 10**20
        words = [
            "0",
            "-0",
            "0.000e99999",
            "1",
            "1.0",
            "1e0",
            "9.9e1",
            "100e-2",
            "0.0001e4",
            "100e+2",
            "0.01e2",
            "1e-1",
            "1e+01",
            "10e1",
            "1000e-10",
            "1e-0",
            "1e+000",
            "1.02",
            "1.02000e0000",
            "012",
            "1.",
            "1e",
            "1e--1",
            "true",
            "NaN",
            "-1",
            " 1",
            "1 ",
            "1e" + str(huge),
            "10e" + str(huge - 1),
            "0.01e" + str(huge + 2),
            "1e-" + str(huge),
            "10e-" + str(huge + 1),
            "0.01e-" + str(huge - 2),
            "-0e" + str(huge),
        ]
        byte_of = {i: word.encode() for i, word in enumerate(words)}
        rows = [{i: Fraction(i + 1, 7) for i in byte_of}]
        law, tapes = enumerate_source(rows, byte_of)
        index = RotatedIndex(rows, byte_of)
        quantiles, cdfs = self.check_statistics(index, law)
        self.assertIn(("1", huge), law)
        self.assertIn(("1", -huge), law)
        # Three huge-exponent spellings collapse to each of these SAME values.
        for order, ids in ((huge, (28, 29, 30)), (-huge, (31, 32, 33))):
            self.assertEqual(law["1", order], sum(rows[0][i] for i in ids))
        print(
            json.dumps(
                {
                    "unrestricted_word_tapes": tapes,
                    "semantic_atoms": len(law),
                    "compact_quantiles": quantiles,
                    "compact_cdfs": cdfs,
                    "extreme_order": str(huge),
                }
            )
        )

    def test_original_ids_mid_token_marker_cuts_and_empty_tokens(self):
        byte_of = {
            0: b"",
            1: b"1",
            2: b"1",
            3: b"0",
            4: b".",
            5: b"00",
            6: b"e",
            7: b"e-1",
            8: b"E+00",
            9: b"-0",
            10: b"1e",
            11: b"01",
            12: b"2",
        }
        cases = [
            [
                {10: Fraction(1)},
                {0: Fraction(1, 4), 1: Fraction(1, 4), 2: Fraction(1, 4), 11: Fraction(1, 4)},
                {0: Fraction(1, 3), 3: Fraction(2, 3)},
            ],
            [
                {1: Fraction(1, 4), 0: Fraction(1, 4), 9: Fraction(1, 4), 3: Fraction(1, 4)},
                {0: Fraction(1, 4), 4: Fraction(1, 4), 6: Fraction(1, 4), 7: Fraction(1, 4)},
                {0: Fraction(1, 4), 1: Fraction(1, 4), 5: Fraction(1, 4), 12: Fraction(1, 4)},
            ],
            [
                {0: Fraction(2, 3), 2: Fraction(1, 3)},
                {8: Fraction(1)},
                {0: Fraction(1, 5), 1: Fraction(4, 5)},
            ],
        ]
        quantiles = cdfs = tapes = coefficients = 0
        for i, rows in enumerate(cases):
            law, count = enumerate_source(rows, byte_of)
            tapes += count
            q, c = self.check_statistics(RotatedIndex(rows, byte_of), law)
            quantiles += q
            cdfs += c
            if i == 0:
                for slot in (1, 2):
                    for token, weight in rows[slot].items():
                        fixed = list(rows)
                        fixed[slot] = {token: weight}
                        fixed_law, _ = enumerate_source(fixed, byte_of)
                        self.assertEqual(
                            RotatedIndex(fixed, byte_of).mass, sum(fixed_law.values(), Fraction(0))
                        )
                        coefficients += 1
        print(
            json.dumps(
                {
                    "row_source_tapes": tapes,
                    "sources": len(cases),
                    "original_id_coefficients": coefficients,
                    "compact_quantiles": quantiles,
                    "compact_cdfs": cdfs,
                }
            )
        )

    def test_compact_source_of_independent_mantissa_and_exponent_blocks(self):
        byte_of = {0: b"1.", 1: b"1", 2: b"2", 3: b"e1"}
        reports = []
        for length in (1, 2, 3):
            digit = {1: Fraction(1, 2), 2: Fraction(1, 2)}
            rows = [{0: Fraction(1)}] + [digit] * length + [{3: Fraction(1)}] + [digit] * length
            law, tapes = enumerate_source(rows, byte_of)
            index = RotatedIndex(rows, byte_of)
            self.assertEqual(index.mass, 1)
            atoms = sorted(law, key=cmp_to_key(compare))
            for rank in (1, len(atoms) // 2, len(atoms)):
                self.assertEqual(index.quantile(Fraction(rank, len(atoms))), atoms[rank - 1])
                self.assertEqual(index.cdf(atoms[rank - 1]), Fraction(rank, len(atoms)))
            reports.append(
                {
                    "block_digits": length,
                    "original_tapes": tapes,
                    "source_states": len(index.source.edges),
                    "index_states": len(index.edges),
                    "index_edges": sum(map(len, index.edges)),
                }
            )
        print(json.dumps({"capacity_oracle_not_timing": reports}))

    def test_zero_only_law_refusals_and_threshold_endpoints(self):
        byte_of = {0: b"", 1: b"", 2: b"-0e", 3: b"0001"}
        rows = [{0: Fraction(2), 1: Fraction(3)}, {2: Fraction(7)}, {3: Fraction(11)}]
        index = RotatedIndex(rows, byte_of)
        self.assertEqual(index.mass, 385)
        self.assertEqual(index.quantile(Fraction(1, 3)), ("0", 0))
        self.assertEqual(index.cdf(("0", 0)), 1)
        self.assertEqual(index.cdf(("0", 0), False), 0)
        self.assertEqual(index.cdf(("1", -(10**100))), 1)
        self.assertEqual(index.cdf(("1", 10**100)), 1)
        for rows in ([], [{}], [{2: Fraction(0)}]):
            empty = RotatedIndex(rows, byte_of)
            self.assertEqual(empty.mass, 0)
            with self.assertRaisesRegex(ValueError, "EMPTY"):
                empty.quantile(1)
            with self.assertRaisesRegex(ValueError, "EMPTY"):
                empty.cdf(("0", 0))
        with self.assertRaisesRegex(ValueError, "byte bound"):
            RotatedIndex([{3: Fraction(1)}], byte_of, budget=1)
        with self.assertRaisesRegex(ValueError, "nonnegative"):
            RotatedIndex([{3: Fraction(-1)}], byte_of)
        for probability in (0, -1, Fraction(3, 2)):
            with self.assertRaisesRegex(ValueError, "probability"):
                index.quantile(probability)
        with self.assertRaisesRegex(ValueError, "canonical"):
            index.cdf(("10", 0))


if __name__ == "__main__":
    unittest.main()
