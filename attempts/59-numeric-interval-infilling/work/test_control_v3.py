"""Full finite-state language-product audit, independent of NFA construction."""

import itertools
import json
import unittest
from collections import deque
from fractions import Fraction

from .interval_one_two import NumberNFA, token_mass
from .register_control_v3 import RegisterNumber
from .test_interval import admitted


class CompleteControlTests(unittest.TestCase):
    def test_every_byte_transition_in_complete_finite_product(self):
        reports = []
        for budget in (8, 16, 32, 64):
            nfa, control = NumberNFA(budget), RegisterNumber(budget)
            initial = (control.start, frozenset({(nfa.start, Fraction(1))}))
            queue, seen, transitions = deque([initial]), {initial}, 0
            while queue:
                state, encoded = queue.popleft()
                vector = dict(encoded)
                final = nfa.closure(vector)
                paths = sum(final.get(q, 0) for q in nfa.accept)
                self.assertEqual(paths, int(control.accepts(state)))
                for byte in range(256):
                    next_state = control.next(state, byte)
                    next_vector = nfa.advance(vector, bytes([byte]))
                    pair = (next_state, frozenset(next_vector.items()))
                    transitions += 1
                    if pair not in seen:
                        seen.add(pair)
                        queue.append(pair)
            self.assertLess(len(seen), 20 * budget + 40)
            reports.append({"L": budget, "product_states": len(seen), "byte_edges": transitions})
        print(json.dumps({"all_byte_language_equivalence": reports}))

    def test_control_against_independent_exact_numerals(self):
        control = RegisterNumber(16)
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
            state = control.advance(control.start, text.encode())
            self.assertEqual(control.accepts(state), admitted(text), text)
            count += 1
        print(json.dumps({"control_independent_numerals": count}))

    def test_weighted_original_ids_fixed_holes_and_zero_mass(self):
        control, nfa = RegisterNumber(32), NumberNFA(32)
        vocabulary = {2: b"15e-", 7: b"1", 11: b"01", 17: b"1", 23: b"2", 29: b"0", 37: b""}
        scenarios = [
            [{2: Fraction(1)}, {7: Fraction(1, 6), 11: Fraction(1, 3), 17: Fraction(1, 2)}],
            [{2: Fraction(1)}, {23: Fraction(1)}],
            [{2: Fraction(1)}, {29: Fraction(1)}],
            [{2: Fraction(1)}, {37: Fraction(1)}],
            [{2: Fraction(1)}, {37: Fraction(1)}, {7: Fraction(1)}],
        ]
        coefficients = 0
        for rows in scenarios:
            reference = Fraction(0)
            for tape in itertools.product(*rows):
                value = Fraction(int(admitted(b"".join(vocabulary[t] for t in tape).decode())))
                for row, token in zip(rows, tape, strict=True):
                    value *= row[token]
                reference += value
            self.assertEqual(control.mass(rows, vocabulary), reference)
            self.assertEqual(token_mass(nfa, rows, vocabulary), reference)
            for slot, row in enumerate(rows):
                for token, weight in row.items():
                    fixed = list(rows)
                    fixed[slot] = {token: weight}
                    self.assertEqual(
                        control.mass(fixed, vocabulary), token_mass(nfa, fixed, vocabulary)
                    )
                    coefficients += 1
        print(
            json.dumps(
                {"complete_control_mass_cases": len(scenarios), "coefficients": coefficients}
            )
        )


if __name__ == "__main__":
    unittest.main()
