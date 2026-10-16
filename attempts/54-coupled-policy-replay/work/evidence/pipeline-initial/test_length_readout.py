"""Independent original-word/anchor/gate enumeration, no old neural heads."""

import itertools
import math
import unittest
from collections import defaultdict
from fractions import Fraction as F

import numpy as np

from .actor_coordinates import actor_vector, state_features
from .length_readout import NumericSuffix, readout
from .query_support import support
from .prefix_floating import PrefixFloatPlan, PrefixPlanner


class LengthReadoutTests(unittest.TestCase):
    def test_joint_length_mass_score_and_mixture_against_independent_words(self):
        language = NumericSuffix((b"1", b"}", b"", b"0", b"EOS"), 4, 4)
        differences = 0
        checks = 0
        for fixed in ({}, {0: 0}, {3: 4}):
            weights = np.tile([1 / 4, 1 / 4, 1 / 8, 1 / 8, 1 / 4], (4, 1))
            for i, v in fixed.items():
                weights[i] = 0
                weights[i, v] = 1
            planner = PrefixPlanner(PrefixFloatPlan(language), weights, fixed, -2.0)
            words = {}
            for length in range(1, 5):
                for prefix in itertools.product(range(4), repeat=length - 1):
                    word = (*prefix, 4)
                    if not language.accepts(word) or any(
                        i >= length or word[i] != v for i, v in fixed.items()
                    ):
                        continue
                    mass = math.prod(F(float(weights[i, v])) for i, v in enumerate(word))
                    if mass:
                        words[word] = mass
            z = sum(words.values())
            masses = defaultdict(F)
            scores = defaultdict(lambda: np.zeros(9))
            examples = {}
            anchor_mass = defaultdict(F)
            anchor_score = defaultdict(lambda: np.zeros(9))
            for word, p in words.items():
                active = [i for i in range(len(word)) if i not in fixed]
                if not active:
                    continue
                for anchor in active:
                    for bits in itertools.product((False, True), repeat=len(active) - 1):
                        keep = {anchor}
                        mass = p / z / len(active)
                        for i, bit in zip((i for i in active if i != anchor), bits, strict=True):
                            g = F(float(planner.gates[i, word[i]]))
                            mass *= g if bit else 1 - g
                            if bit:
                                keep.add(i)
                        action = tuple((i, word[i]) for i in sorted(keep))
                        key = (len(word), action)
                        aa = np.zeros(4)
                        rr = np.zeros(4)
                        for i in active:
                            aa[i] = 0 if i == anchor else int(i in keep) - planner.gates[i, word[i]]
                            rr[i] = int(i == anchor) - 1 / len(active)
                        bb = sum(aa[i] * math.log(weights[i, word[i]]) for i in active)
                        vector = np.r_[aa, rr, bb]
                        anchor_mass[anchor, action] += mass
                        anchor_score[anchor, action] += float(mass) * vector
                        masses[key] += mass
                        scores[key] += float(mass) * vector
                        examples[key] = (word, anchor)
            by_action = defaultdict(list)
            for (length, action), mass in masses.items():
                result = readout(planner, action, length)
                self.assertIsNotNone(result)
                vector = np.r_[result["alpha"], result["anchor"], result["beta"]]
                np.testing.assert_allclose(
                    vector, scores[length, action] / float(mass), rtol=0, atol=2e-12
                )
                self.assertAlmostEqual(math.exp(result["log_probability"]), float(mass), places=12)
                by_action[action].append((mass, vector))
                word, anchor = examples[length, action]
                hybrid = planner.controls(word, anchor, action)["length_integrated"]
                differences += np.max(np.abs(hybrid["alpha"] - result["alpha"])) > 1e-7
                checks += 1
            for action, values in by_action.items():
                features = state_features(weights, fixed, language.eos)
                conditional = support(planner, action, features)
                for item in conditional["anchors"]:
                    anchor = item["anchor"]
                    expected = anchor_score[anchor, action] / float(anchor_mass[anchor, action])
                    projected = actor_vector(
                        {"alpha": expected[:4], "anchor": expected[4:8], "beta": expected[8]},
                        features,
                    )
                    np.testing.assert_allclose(projected, item["actor"], rtol=0, atol=2e-12)
                full = planner.statistics(action)
                mass = sum(p for p, _ in values)
                mixed = sum(float(p) * v for p, v in values) / float(mass)
                np.testing.assert_allclose(
                    mixed, np.r_[full["alpha"], full["anchor"], full["beta"]], rtol=0, atol=2e-12
                )
                self.assertAlmostEqual(math.exp(full["log_probability"]), float(mass), places=12)
        self.assertGreater(checks, 20)
        self.assertGreater(differences, 0)

    def test_zero_event_and_fixed_eos_length_are_explicit(self):
        language = NumericSuffix((b"1", b"}", b"", b"0", b"EOS"), 4, 4)
        weights = np.full((4, 5), 1 / 5)
        weights[3] = 0
        weights[3, 4] = 1
        planner = PrefixPlanner(PrefixFloatPlan(language), weights, {3: 4}, -2)
        self.assertIsNone(readout(planner, ((0, 0),), 3))
        self.assertIsNone(readout(planner, ((0, 0),), 1))
        value = readout(planner, ((0, 0),), 4)
        visible = planner.statistics(((0, 0),))
        for key in value:
            np.testing.assert_allclose(value[key], visible[key], rtol=0, atol=1e-12)
