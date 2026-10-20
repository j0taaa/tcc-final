"""Exact finite utility checks for B1; no model or performance measurement."""

import json
import runpy
from fractions import Fraction as F
from itertools import product
from pathlib import Path


def main():
    frozen = runpy.run_path(str(Path(__file__).with_name("oracles.py")))
    transport = frozen["sparse_transport"]
    compositions = frozen["compositions"]
    checked = 0
    for size, denominator in [(2, 5), (3, 4), (4, 3)]:
        laws = [tuple(F(w, denominator) for w in x) for x in compositions(denominator, size)]
        for p, q in product(laws, repeat=2):
            joint = transport(p, q, set(range(size)))
            for c in range(size):
                coverage = sum(
                    joint[i][j] for i, j in product(range(size), repeat=2) if c in (i, j)
                )
                iid = 1 - (1 - p[c]) * (1 - q[c])
                assert coverage == min(F(1), p[c] + q[c])
                assert coverage - iid == min(p[c] * q[c], (1 - p[c]) * (1 - q[c]))
                assert coverage >= iid
                checked += 1

    p = (F(3, 5), F(3, 10), F(1, 10))
    joint = transport(p, p, {0, 1, 2})
    iid = [1 - (1 - pc) ** 2 for pc in p]
    b1 = [2 * p[c] - joint[c][c] for c in range(3)]
    wor = [p[c] + sum(p[i] * p[c] / (1 - p[i]) for i in range(3) if i != c) for c in range(3)]
    means = [sum(p[c] * law[c] for c in range(3)) for law in (iid, b1, wor)]
    assert means == [F(169, 250), F(4, 5), F(573, 700)]
    assert means[1] < means[2] < F(9, 10)

    # Direct expectation of item quality minus actual forbidden-collision costs.
    laws = [p, (F(2, 5), F(3, 10), F(3, 10)), (F(1, 2), F(1, 4), F(1, 4))]
    plans = [transport(laws[i], laws[i + 1], {0, 1, 2}) for i in range(2)]
    lambdas = (F(2), F(3))
    independent_utility, coupled_utility = F(0), F(0)
    for word in product(range(3), repeat=3):
        score = sum((i + 1) * (v * v - 2) for i, v in enumerate(word))
        score -= sum(lambdas[i] * (word[i] == word[i + 1]) for i in range(2))
        base = laws[0][word[0]] * laws[1][word[1]] * laws[2][word[2]]
        coupled = plans[0][word[0]][word[1]] * plans[1][word[1]][word[2]] / laws[1][word[1]]
        independent_utility += base * score
        coupled_utility += coupled * score
    predicted = sum(
        lambdas[i]
        * (
            sum(laws[i][c] * laws[i + 1][c] for c in range(3))
            - sum(plans[i][c][c] for c in range(3))
        )
        for i in range(2)
    )
    assert coupled_utility - independent_utility == predicted > 0

    uniform = (F(1, 4),) * 4
    pair = transport(uniform, uniform, set(range(4)))
    acceptable = {0, 1}
    hit = sum(pair[i][j] for i, j in product(range(4), repeat=2) if {i, j} & acceptable)
    assert hit == F(1, 2) < F(3, 4)
    four_hit = F(0)
    for word in product(range(4), repeat=4):
        mass = uniform[word[0]]
        for i in range(3):
            mass *= pair[word[i]][word[i + 1]] / uniform[word[i]]
        if 0 in word:
            four_hit += mass
    assert four_hit == F(1, 2) < 1 - F(3, 4) ** 4 == F(175, 256)
    fair = (F(1, 2),) * 2
    anti = transport(fair, fair, {0, 1})
    assert sum(anti[c][c] for c in range(2)) == 0 < F(1, 2)
    print(
        json.dumps(
            {
                "per_label_coverage_checks": checked,
                "constructed_mean_recall": {
                    "iid": str(means[0]),
                    "b1": str(means[1]),
                    "wor": str(means[2]),
                    "deterministic_top2": "9/10",
                },
                "constructed_additive_utility_gain": str(predicted),
                "counterexamples": [
                    "two_acceptable_labels",
                    "four_alternatives_on_a_path",
                    "legitimate_repetition",
                ],
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
