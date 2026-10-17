"""Independent JSON/Decimal and original-tape enumeration oracles; no models."""

import itertools
import json
import unittest
from collections import defaultdict
from decimal import Decimal
from fractions import Fraction

from .semantic_index import Normalizer, SemanticIndex


def parsed(data):
    try:
        text = data.decode("ascii")
        number = json.loads(text, parse_int=Decimal, parse_float=Decimal)
        if text.strip() != text or not isinstance(number, Decimal):
            return None
        return number if 1 <= number < 100 else None
    except (UnicodeError, ValueError):
        return None


def reference_key(number):
    _, digits, exponent = number.as_tuple()
    # Do not Decimal.normalize(): its rounding depends on the ambient context.
    order = exponent + len(digits) - 1
    return "ab"[order] + "".join(map(str, digits)).rstrip("0")


def enumerated(rows, byte_of):
    law = defaultdict(Fraction)
    tapes = 0
    for tape in itertools.product(*rows):
        weight = Fraction(1)
        for row, token in zip(rows, tape, strict=True):
            weight *= row[token]
        number = parsed(b"".join(byte_of[t] for t in tape))
        tapes += 1
        if number is not None:
            law[Fraction(number)] += weight
    return {v: w for v, w in law.items() if w}, tapes


class SemanticIndexTests(unittest.TestCase):
    def test_unique_normalization_against_independent_decimal(self):
        normalizer = Normalizer(64)
        integers = ("0", "1", "2", "10", "11", "12", "20", "99")
        fractions = [""] + [
            "." + "".join(s) for length in (1, 2) for s in itertools.product("012", repeat=length)
        ]
        powers = [""] + [
            e + sign + "".join(s)
            for length in (1, 2, 3)
            for s in itertools.product("012", repeat=length)
            for e in ("e", "E")
            for sign in ("", "+", "-")
        ]
        count = accepted = 0
        for parts in itertools.product(("", "-"), integers, fractions, powers):
            data = "".join(parts).encode()
            value = parsed(data)
            keys = normalizer.normalize(data)
            expected = [] if value is None else [reference_key(value)]
            self.assertEqual(keys, expected, data)
            count += 1
            accepted += bool(expected)
        regressions = (
            b"100e-2", b"0.0001e4", b"1.020e0", b"10e1", b"1e1", b"10e0",
            b"0.1e1", b"1.2000", b"99e0", b"9.9e1", b"10e01", b"10e-01",
            b"1e+0000", b"1e-0000", b"0", b"01", b"1.", b"1.e0", b"1e",
            b"1e--1", b"1e+-1", b"1e00x", b"true", b"NaN", b" 1", b"1 ",
            b"1\xff", b"1.234567890123456789012345678901234567890000",
        )
        for data in regressions:
            value = parsed(data)
            self.assertEqual(
                normalizer.normalize(data), [] if value is None else [reference_key(value)], data
            )
        print(json.dumps({"normalization_numerals": count, "accepted": accepted,
                          "separate_regressions": len(regressions)}))

    def test_source_mass_cdf_and_exact_quantile_boundaries(self):
        byte_of = {2: b"1", 3: b"1", 5: b"2", 7: b"9", 11: b"0.0", 13: b"",
                   17: b".", 19: b"0", 23: b"5", 29: b"e1", 31: b"e-1", 37: b"e0"}
        cases = [
            [{2: Fraction(1, 2), 3: Fraction(1, 3), 7: Fraction(1, 6)}],
            [{2: Fraction(1, 2), 11: Fraction(1, 2)}, {13: Fraction(1, 3), 19: Fraction(2, 3)},
             {13: Fraction(1, 2), 29: Fraction(1, 4), 31: Fraction(1, 4)}],
            [{t: Fraction(1, 5) for t in (2, 5, 7, 11, 13)},
             {t: Fraction(1, 4) for t in (13, 17, 19, 23)},
             {t: Fraction(1, 3) for t in (2, 19, 13)},
             {t: Fraction(1, 4) for t in (13, 29, 31, 37)}],
            [{2: Fraction(1)}, {17: Fraction(1)}, {2: Fraction(1, 2), 23: Fraction(1, 2)},
             {19: Fraction(1, 2), 13: Fraction(1, 2)}],
            [{11: Fraction(1)}, {31: Fraction(1)}],
        ]
        tapes = cdfs = quantiles = coefficients = 0
        for rows in cases:
            law, count = enumerated(rows, byte_of)
            tapes += count
            index = SemanticIndex(rows, byte_of)
            total = sum(law.values(), Fraction(0))
            self.assertEqual(index.mass, total)
            for slot, row in enumerate(rows):
                for token, weight in row.items():
                    fixed = list(rows)
                    fixed[slot] = {token: weight}
                    fixed_law, _ = enumerated(fixed, byte_of)
                    self.assertEqual(SemanticIndex(fixed, byte_of).mass, sum(fixed_law.values()))
                    coefficients += 1
            if not total:
                with self.assertRaisesRegex(ValueError, "EMPTY"):
                    index.quantile(Fraction(1, 2))
                with self.assertRaisesRegex(ValueError, "EMPTY"):
                    index.cdf(10)
                continue
            atoms = sorted(law)
            thresholds = set(atoms) | {Fraction(0), Fraction(1), Fraction(10), Fraction(99),
                                      Fraction(100), Fraction(1, 3), Fraction(61, 7)}
            thresholds.update((a + b) / 2 for a, b in itertools.pairwise(atoms))
            tiny = Fraction(1, 10 ** (index.budget + 1))
            thresholds.update(a + sign * tiny for a in atoms for sign in (-1, 1))
            for threshold in thresholds:
                for inclusive in (True, False):
                    expected = sum(
                        (w for v, w in law.items()
                         if v < threshold or (inclusive and v == threshold)), Fraction(0)
                    )
                    self.assertEqual(index.cdf(threshold, inclusive), expected / total,
                                     (rows, threshold, inclusive))
                    cdfs += 1
            probabilities, cumulative = {Fraction(1, 2), Fraction(1)}, Fraction(0)
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
                self.assertEqual(index.quantile(probability), expected, (rows, probability))
                quantiles += 1
        print(json.dumps({"original_tapes": tapes, "source_cases": len(cases),
                          "original_id_coefficients": coefficients, "exact_cdfs": cdfs,
                          "exact_quantiles": quantiles}))

    def test_alias_sensitive_subjective_bayes_example(self):
        byte_of = {0: b"90", 1: b"1", 2: b"1.0", 3: b"1e0"}
        rows = [{0: Fraction(4, 10), 1: Fraction(3, 10),
                 2: Fraction(2, 10), 3: Fraction(1, 10)}]
        index = SemanticIndex(rows, byte_of)
        law, _ = enumerated(rows, byte_of)
        self.assertEqual(law, {Fraction(1): Fraction(3, 5), Fraction(90): Fraction(2, 5)})
        median = index.quantile(Fraction(1, 2))
        self.assertEqual(median, 1)
        self.assertEqual(sum(w * abs(v - median) for v, w in law.items()), Fraction(356, 10))
        self.assertEqual(sum(w * abs(v - 90) for v, w in law.items()), Fraction(534, 10))

    def test_empty_emissions_epsilon_ownership_and_refusals(self):
        byte_of = {0: b"", 1: b"", 2: b"1", 3: b"00", 4: b"e-2", 5: b"e2"}
        rows = [{0: Fraction(1, 3), 1: Fraction(2, 3)}, {2: Fraction(1)},
                {0: Fraction(1, 4), 3: Fraction(3, 4)},
                {4: Fraction(1, 2), 5: Fraction(1, 2)}, {1: Fraction(1)}]
        index = SemanticIndex(rows, byte_of)
        self.assertEqual(index.mass, Fraction(3, 8))
        self.assertEqual(index.quantile(1), 1)
        with self.assertRaisesRegex(ValueError, "byte bound"):
            SemanticIndex(rows, byte_of, budget=2)
        for probability in (-1, 0, Fraction(3, 2)):
            with self.assertRaisesRegex(ValueError, "probability"):
                index.quantile(probability)
        with self.assertRaisesRegex(ValueError, "nonnegative"):
            SemanticIndex([{2: Fraction(-1)}], byte_of)
        for rows in ([], [{}], [{2: Fraction(0)}]):
            empty = SemanticIndex(rows, byte_of)
            self.assertEqual(empty.mass, 0)
            with self.assertRaisesRegex(ValueError, "EMPTY"):
                empty.quantile(1)


if __name__ == "__main__":
    unittest.main()
