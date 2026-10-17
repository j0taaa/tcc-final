"""Exact finite checks of the written parity reduction, not all-budget safety."""

from fractions import Fraction as F
from itertools import permutations


def compositions(total, length):
    if length == 1:
        yield (total,)
    else:
        for value in range(total + 1):
            for tail in compositions(total - value, length - 1):
                yield (value, *tail)


def tickets_joint(counts, order=None):
    b = sum(counts)
    order = range(len(counts)) if order is None else order
    tickets = [i for i in order for _ in range(2 * counts[i])]
    joint = [[F(0) for _ in counts] for _ in counts]
    for index, i in enumerate(tickets):
        joint[i][tickets[(index + b) % (2 * b)]] += F(1, 2 * b)
    return joint


def random_order_joint(counts):
    orders = list(permutations(i for i, count in enumerate(counts) if count))
    result = [[F(0) for _ in counts] for _ in counts]
    for order in orders:
        joint = tickets_joint(counts, order)
        for i in range(len(counts)):
            for j in range(len(counts)):
                result[i][j] += joint[i][j] / len(orders)
    return result


def original_four_pool_joint(counts):
    """Enumerate original payload label transcripts, independent of towers."""
    payloads = tuple(i for i, count in enumerate(counts) for _ in range(count))
    transcripts = set(permutations(payloads))
    joint = [[F(0) for _ in counts] for _ in counts]
    shape = sorted(c for c in counts if c)
    for transcript in transcripts:
        first = transcript[0]
        if shape == [2, 2]:
            partners = [i for i in range(1, 4) if transcript[i] != first]
        elif shape == [1, 1, 2]:
            repeated = counts.index(2)
            partners = [
                i for i in range(1, 4) if (transcript[i] == repeated) != (first == repeated)
            ]
        else:
            partners = [1]
        for index in partners:
            joint[first][transcript[index]] += F(1, len(transcripts) * len(partners))
    return joint


def run():
    profiles = entries = four_profiles = 0
    for length in range(2, 7):
        for b in (3, 5, 7, 9):
            if length == 6 and b == 9:
                continue
            for counts in compositions(b, length):
                original = tickets_joint(counts)
                deletion = [[F(0) for _ in counts] for _ in counts]
                for removed, multiplicity in enumerate(counts):
                    if not multiplicity:
                        continue
                    remaining = tuple(c - (i == removed) for i, c in enumerate(counts))
                    joint = tickets_joint(remaining)
                    for i in range(length):
                        for j in range(length):
                            deletion[i][j] += F(multiplicity, b) * joint[i][j]
                assert original == deletion, (counts, original, deletion)
                assert [sum(row) for row in original] == [F(c, b) for c in counts]
                profiles += 1
                entries += length * length
    for length in range(2, 6):
        for counts in compositions(4, length):
            assert random_order_joint(counts) == original_four_pool_joint(counts), counts
            four_profiles += 1
    counts = (2, 2, 1, 1)
    f = (1, 1, -2, -2)
    joint = random_order_joint(counts)
    mean = sum(F(c, 6) * value for c, value in zip(counts, f, strict=True))
    variance = sum(F(c, 6) * (value - mean) ** 2 for c, value in zip(counts, f, strict=True))
    product = sum(joint[i][j] * f[i] * f[j] for i in range(4) for j in range(4))
    assert mean == 0 and variance == 2 and product == 0
    assert product - mean**2 > -variance / 5
    print(
        dict(
            status="PASS_FINITE_PARITY_AND_CONTROL_ONLY",
            fixed_order_profiles=profiles,
            exact_matrix_entries=entries,
            four_pool_control_profiles=four_profiles,
            conditional_shortcut_counterexample=True,
            universal_safety_proved=False,
            new_neural_calls=0,
        )
    )


if __name__ == "__main__":
    run()
