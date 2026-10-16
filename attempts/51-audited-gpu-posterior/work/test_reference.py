"""Independent finite source/word enumeration, not Monte Carlo law estimates."""

import itertools
import json
import unittest
from collections import Counter
from fractions import Fraction as F
from random import Random

from .reference import Category, Edge, Reference


def compositions(total, length):
    for cuts in itertools.combinations(range(1, total), length - 1):
        endpoints = (0, *cuts, total)
        yield tuple(b - a for a, b in itertools.pairwise(endpoints))


def fixture(words, canvas, eot, pad, *, salt=0):
    """Construct a tiny independent strict-JSON language by full word enumeration.

    Prefix trie merged only at the final accept node. This deliberately uses
    neither the research JSON compiler nor its token classes.
    """
    domains = [(t,) if t is not None else range(len(words)) for t in canvas]
    law = {}
    rows = tuple(
        tuple(
            F(int(t == fixed)) if fixed is not None else F((t + p + salt) % 7, 8)
            for t in range(len(words))
        )
        for p, fixed in enumerate(canvas)
    )
    for word in itertools.product(*domains):
        if eot not in word:
            continue
        stop = word.index(eot)
        if any(t != pad for t in word[stop + 1 :]) or any(
            t in (eot, pad) or words[t] is None for t in word[:stop]
        ):
            continue
        try:
            text = b"".join(words[t] for t in word[:stop]).decode("utf8")
            json.loads(text, parse_constant=lambda _: (_ for _ in ()).throw(ValueError()))
        except (ValueError, UnicodeDecodeError):
            continue
        weight = F(1)
        for p, t in enumerate(word):
            weight *= rows[p][t]
        law[word] = weight
    if not law:
        raise ValueError("empty fixture language")
    prefixes = [sorted({w[:p] for w in law}) for p in range(len(canvas))]
    layers, tables = [], []
    for p, before in enumerate(prefixes):
        layer, layer_tables = [], []
        for s, prefix in enumerate(before):
            labels = sorted({w[p] for w in law if w[:p] == prefix})
            # Group final aliases in ONE edge to exercise disintegration.
            if p == len(canvas) - 1:
                edges = (Edge(0, tuple(labels)),)
            else:
                edges = tuple(Edge(prefixes[p + 1].index((*prefix, t)), (t,)) for t in labels)
            layer.append(edges)
            edge_cat = Category(tuple(1 + (j + s + salt) % 4 for j in range(len(edges))), 8)
            cats = tuple(
                Category(tuple(1 + (j + p + salt) % 5 for j in range(len(e.tokens))), 8)
                for e in edges
            )
            layer_tables.append((edge_cat, cats))
        layers.append(tuple(layer))
        tables.append(tuple(layer_tables))
    return Reference(tuple(layers), rows, tuple(tables)), law


class ExecutedProposalTests(unittest.TestCase):
    def test_all_small_finite_preimages_and_inverse_bounds(self):
        checked = 0
        for bits in range(2, 9):
            for total in range(1, min(12, 1 << bits)):
                for size in range(1, min(4, total) + 1):
                    for counts in compositions(total, size):
                        table = Category(counts, bits)
                        observed = Counter(table.select(r) for r in range(1 << bits))
                        self.assertEqual(sum(observed.values()), 1 << bits)
                        for i in range(size):
                            probability = F(observed[i], 1 << bits)
                            self.assertEqual(table.probability(i), probability)
                            self.assertGreater(probability, 0)
                            self.assertGreaterEqual(table.inverse_upper(i), 1 / probability)
                            checked += 1
        self.assertGreater(checked, 1000)

    def test_small_json_full_accepted_laws_and_budget_fail(self):
        cases = [
            ([b"0", b"0", b"[]", b"[[]]", None, None, b" "], (None,) * 3, 4, 5),
            ([b"[", b"]", b"0", b"[]", None, b" "], (0, None, None, None), 4, 4),
            ([b'"', b"\xc3", b"\xa9", b"a", None, None], (0, None, None, None, None), 4, 5),
            ([b"1", b"e", b"0", b" ", None, None], (None, None, None, 4), 4, 5),
        ]
        observed = set()
        for words, canvas, eot, pad in cases:
            for salt in range(1, 4):
                sampler, target = fixture(words, canvas, eot, pad, salt=salt)
                total = sum(target.values(), F())
                self.assertGreater(total, 0)
                self.assertEqual(sampler.mass, total)
                proposal = {word: sampler.trace(word)[1] for word in target}
                self.assertEqual(sum(proposal.values(), F()), 1)
                true_max = max(target[w] / proposal[w] for w in target)
                self.assertEqual(sampler.envelope, true_max)
                self.assertGreaterEqual(sampler.cheap_envelope, true_max)
                for envelope in (sampler.envelope, sampler.cheap_envelope):
                    accepted = {
                        w: proposal[w] * target[w] / (envelope * proposal[w]) for w in target
                    }
                    rate = sum(accepted.values(), F())
                    self.assertEqual(rate, total / envelope)
                    for k in (0, 1, 2, 5):
                        fail = (1 - rate) ** k
                        multiplier = sum(((1 - rate) ** j for j in range(k)), F())
                        finite = {w: multiplier * accepted[w] for w in target}
                        self.assertEqual(sum(finite.values(), F()) + fail, 1)
                        if k:
                            for word in target:
                                self.assertEqual(finite[word] / (1 - fail), target[word] / total)
                for seed in range(16):
                    result = sampler.sample(Random(seed), 20)
                    observed.add(result["status"])
                    if result["status"] == "COMPLETE":
                        self.assertGreater(target[result["word"]], 0)
                        self.assertTrue(
                            all(t is None or result["word"][p] == t for p, t in enumerate(canvas))
                        )
                self.assertEqual(sampler.sample(Random(0), 0)["status"], "FAIL")
        self.assertIn("COMPLETE", observed)

    def test_singletons_and_finite_law_are_not_ideal_count_ratios(self):
        cat = Category((1, 2), 3)
        self.assertNotEqual(cat.probability(0), F(1, 3))
        self.assertEqual(cat.probability(0), F(3, 8))
        self.assertEqual(cat.probability(1), F(5, 8))
        one = Category((7,), 3)
        self.assertEqual(one.probability(0), 1)
        self.assertEqual(one.inverse_upper(0), 1)
        self.assertEqual(one.draw(object()), 0)

    def test_invalid_counts_and_nondeterministic_graph_refused(self):
        for counts, bits in (((), 4), ((0, 1), 4), ((-1, 2), 4), ((8,), 3), ((1.0,), 4)):
            with self.assertRaises(ValueError):
                Category(counts, bits)
        c = Category((1,), 4)
        duplicate = (((Edge(0, (0,)), Edge(0, (0,))),),)
        with self.assertRaisesRegex(ValueError, "unique"):
            Reference(duplicate, ((F(1),),), (((Category((1, 1), 4), (c, c)),),))
        with self.assertRaisesRegex(ValueError, "zero-mass"):
            Reference((((Edge(0, (0,)),),),), ((F(0),),), (((c, (c,)),),))

    def test_merged_suffixes_aliases_and_reweighting(self):
        layers = (
            ((Edge(0, (0, 1)), Edge(1, (2,))),),
            ((Edge(0, (0, 1)),), (Edge(0, (0, 1)),)),
        )
        c = Category((1,), 6)
        a, b = Category((1, 2), 6), Category((3, 1), 6)
        tables = (((a, (b, c)),), ((c, (a,)), (c, (b,))))
        for rows in (
            ((F(1), F(2), F(4)), (F(3), F(7), F(0))),
            ((F(0), F(9), F(2)), (F(8), F(1), F(0))),
        ):
            sampler = Reference(layers, rows, tables)
            words = list(itertools.product(range(3), range(2)))
            ratios, weight_sum, q_sum = [], F(), F()
            for word in words:
                weight, q, _ = sampler.trace(word)
                self.assertEqual(weight, rows[0][word[0]] * rows[1][word[1]])
                ratios.append(weight / q)
                weight_sum += weight
                q_sum += q
            self.assertEqual(q_sum, 1)
            self.assertEqual(sampler.mass, weight_sum)
            self.assertEqual(sampler.envelope, max(ratios))
            self.assertGreaterEqual(sampler.cheap_envelope, max(ratios))


if __name__ == "__main__":
    unittest.main()
