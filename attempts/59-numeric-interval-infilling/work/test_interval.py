"""Independent JSON/Decimal/Fraction checks, not a real-model benchmark."""

import itertools
import json
import unittest
from decimal import Decimal
from fractions import Fraction

from .interval_one_two import NumberNFA, token_mass


def admitted(text):
    try:
        number = json.loads(text, parse_float=Decimal, parse_int=Decimal)
    except (ValueError, ArithmeticError):
        return False
    return isinstance(number, Decimal) and 1 <= Fraction(number) < 2


class NumericIntervalTests(unittest.TestCase):
    def test_independent_numeral_values_and_unambiguous_paths(self):
        machine = NumberNFA(16)
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
        count = 0
        for integer, fraction, power, minus in itertools.product(
            integers, fractions, powers, ("", "-")
        ):
            text = minus + integer + fraction + power
            self.assertLessEqual(len(text), 16)
            self.assertEqual(machine.paths(text.encode()), int(admitted(text)), text)
            count += 1
        for text in ("", "01", ".1", "1.", "1e", "1e+", "1e00+0", "1e--0", "1 0", "+1"):
            self.assertEqual(machine.paths(text.encode()), 0, text)
        print(json.dumps({"independent_numerals": count, "malformed": 10}))

    def test_budget_completeness_and_long_sound_inputs(self):
        machine = NumberNFA(80)
        words = [
            "0." + "0" * 31 + "1e32",
            "1" + "0" * 30 + "e-30",
            "1." + "9" * 200,
            "1e-" + "0" * 200,
            "1e" + "0" * 100 + "1",
            "1.99999999999999999999999999999999999",
            "2e-000",
            "0.19e1",
            "10e1",
            "10e+1",
            "10e-1",
            "0.1e1",
            "0.1e-1",
            "0.1e+1",
        ]
        for text in words:
            self.assertEqual(machine.paths(text.encode()), int(admitted(text)), text)
        with self.assertRaises(ValueError):
            NumberNFA(0)

    def test_linear_graph_and_nondeterministic_fooling_set(self):
        sizes = []
        for budget in (16, 32, 64, 128, 256):
            machine = NumberNFA(budget)
            states, edges = machine.size()
            self.assertLessEqual(states, 12 * budget + 20)
            self.assertLessEqual(edges, 70 * budget + 40)
            sizes.append([budget, states, edges])
        machine = NumberNFA(80)
        for first, second in itertools.product(range(1, 31), repeat=2):
            text = "1" + "0" * first + "e-" + str(second)
            self.assertEqual(machine.paths(text.encode()), int(first == second))
        print(json.dumps({"graph_sizes": sizes, "fooling_pairs": 900}))

    def test_original_id_joint_mass_marginals_aliases_fixed_and_zero(self):
        machine = NumberNFA(32)
        vocabulary = {
            13: b"15e-",
            21: b"1",
            33: b"01",
            48: b"001",
            52: b"2",
            65: b"0",
            79: b"1",
            82: b"+1",
            97: b"",
            101: b"e",
            113: b"-",
            127: b"15",
        }
        scenarios = [
            [
                {13: Fraction(1)},
                {v: Fraction(j, 28) for j, v in enumerate((21, 33, 48, 52, 65, 79, 82), 1)},
            ],
            [
                {127: Fraction(1)},
                {101: Fraction(1)},
                {113: Fraction(1)},
                {21: Fraction(2, 3), 52: Fraction(1, 3)},
            ],
            [{13: Fraction(1)}, {97: Fraction(1)}],
        ]
        checked = 0
        for rows in scenarios:
            reference = Fraction(0)
            contributions = [{v: Fraction(0) for v in row} for row in rows]
            for tape in itertools.product(*rows):
                text = b"".join(vocabulary[v] for v in tape).decode()
                weight = Fraction(int(admitted(text)))
                for row, token in zip(rows, tape, strict=True):
                    weight *= row[token]
                reference += weight
                for slot, token in enumerate(tape):
                    contributions[slot][token] += weight
            self.assertEqual(token_mass(machine, rows, vocabulary), reference)
            for slot, row in enumerate(rows):
                for token, probability in row.items():
                    fixed = list(rows)
                    fixed[slot] = {token: probability}
                    self.assertEqual(
                        token_mass(machine, fixed, vocabulary), contributions[slot][token]
                    )
                    checked += 1
            if reference:
                for row in contributions:
                    self.assertEqual(sum(v / reference for v in row.values()), 1)
        print(
            json.dumps({"token_mass_cases": len(scenarios), "original_id_marginal_checks": checked})
        )


if __name__ == "__main__":
    unittest.main()
