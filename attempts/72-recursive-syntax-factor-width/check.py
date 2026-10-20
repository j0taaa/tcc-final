"""Finite attacks on the separator proof; no model or timing claim.

Integer tensor contractions and direct word recognition are independent
of any maintained parser or factor-inference implementation.
"""

from __future__ import annotations

import argparse
import json
import random
from collections import Counter
from fractions import Fraction
from itertools import product
from math import prod


def partitions(length: int, with_separator: bool = False):
    """Restricted growth strings; block 0 can name a distinguished separator."""

    def extend(labels: tuple[int, ...], maximum: int):
        if len(labels) == length:
            yield labels
            return
        for label in range(maximum + 2):
            yield from extend((*labels, label), max(maximum, label))

    yield from extend((), 0 if with_separator else -1)


def mirrors(half: int, marker: int) -> list[tuple[int, int]]:
    position = 2 * marker
    return [(i, position - 1 - i) for i in range(marker)] + [
        (position + 1 + i, 2 * half - i) for i in range(half - marker)
    ]


def check_uniform_palindromes(rng: random.Random) -> tuple[int, int, int]:
    covers = cuts = words = 0
    for half in range(1, 21):
        observed = [pair for marker in range(half + 1) for pair in mirrors(half, marker)]
        expected = {
            tuple(sorted((a, b))) for a in range(0, 2 * half + 1, 2) for b in range(1, 2 * half, 2)
        }
        assert len(observed) == len(set(observed)) == len(expected)
        assert set(observed) == expected
        covers += 1

    def check_cut(labels: tuple[int, ...]) -> bool:
        half = (len(labels) - 1) // 2
        odd_counts = Counter(labels[i] for i in range(1, len(labels), 2) if labels[i] != 0)
        if any(2 * count > half for count in odd_counts.values()):
            return False
        removed = labels.count(0)
        counts = [
            sum(
                labels[a] != 0 and labels[b] != 0 and labels[a] != labels[b]
                for a, b in mirrors(half, marker)
            )
            for marker in range(half + 1)
        ]
        assert 2 * sum(counts) >= (half + 1) * (half - 2 * removed)
        if 6 * removed < half:
            assert 5 * sum(6 * count >= half for count in counts) >= half + 1
        return True

    for length in (3, 5, 7, 9):
        for labels in partitions(length, with_separator=True):
            cuts += check_cut(labels)
        half = (length - 1) // 2
        constructed = set()
        for marker in range(half + 1):
            for bits in product("01", repeat=half):
                chars = ["#"] * length
                for (a, b), bit in zip(mirrors(half, marker), bits, strict=True):
                    chars[a] = chars[b] = bit
                constructed.add("".join(chars))
        recognized = set()
        for chars in product("01#", repeat=length):
            word = "".join(chars)
            if word.count("#") != 1:
                continue
            left, right = word.split("#")
            if len(left) % 2 == len(right) % 2 == 0 and left == left[::-1] and right == right[::-1]:
                recognized.add(word)
        assert constructed == recognized
        assert len(constructed) == (half + 1) * 2**half
        words += len(constructed)

    for half in (8, 16, 32, 64):
        for _ in range(100):
            labels = tuple(rng.randrange(1, 6) for _ in range(2 * half + 1))
            removed = rng.sample(range(len(labels)), rng.randrange((half + 5) // 6))
            removed_set = set(removed)
            labels = tuple(0 if i in removed_set else label for i, label in enumerate(labels))
            cuts += check_cut(labels)
    return covers, cuts, words


def check_block_affinity(rng: random.Random) -> int:
    """Integer tensor norms check the many-component lemma, including cycles."""
    checked = 0
    for pairs in range(1, 5):
        for labels in partitions(2 * pairs):
            if any(labels[2 * edge] == labels[2 * edge + 1] for edge in range(pairs)):
                continue
            blocks = [
                tuple(i for i, label in enumerate(labels) if label == block)
                for block in range(max(labels) + 1)
            ]
            for _ in range(3):
                tensors = [[rng.randrange(4) for _ in range(2 ** len(block))] for block in blocks]
                for tensor in tensors:
                    tensor[0] += 1
                contraction = 0
                for bits in product(range(2), repeat=pairs):
                    factors = []
                    for block, tensor in zip(blocks, tensors, strict=True):
                        index = 0
                        for endpoint in block:
                            index = 2 * index + bits[endpoint // 2]
                        factors.append(tensor[index])
                    contraction += prod(factors)
                norm_squared = prod(sum(value**2 for value in tensor) for tensor in tensors)
                assert contraction**2 <= norm_squared
                checked += 1
    return checked


def check_typed_blocks(rng: random.Random) -> int:
    """Compare a strong context-mixture control against direct word recognition."""
    checked = 0
    alphabet = "()[]#"
    closing = {"(": ")", "[": "]"}
    for length in (1, 3, 5, 7):
        valid = []
        for chars in product(alphabet, repeat=length):
            word = "".join(chars)
            if word.count("#") != 1:
                continue
            blocks = word.split("#")
            if all(
                len(block) % 2 == 0
                and all(c in closing for c in block[: len(block) // 2])
                and block[len(block) // 2 :]
                == "".join(closing[c] for c in reversed(block[: len(block) // 2]))
                for block in blocks
            ):
                valid.append(tuple(alphabet.index(c) for c in word))
        half = (length - 1) // 2
        assert len(valid) == (half + 1) * 2**half
        for case in range(20):
            weights = [[rng.randrange(case % 2, 8) for _ in alphabet] for _ in range(length)]
            enumerated = sum(
                prod(weights[i][symbol] for i, symbol in enumerate(word)) for word in valid
            )
            mixture = sum(
                weights[2 * marker][4]
                * prod(
                    weights[a][0] * weights[b][1] + weights[a][2] * weights[b][3]
                    for a, b in mirrors(half, marker)
                )
                for marker in range(half + 1)
            )
            assert enumerated == mixture
            checked += 1
    return checked


def check_library() -> int:
    """Optional consumer check; independent constructed words give all marginals."""
    from fractions import Fraction

    from mwpc_exact.cfg_posterior import compile_cfg_sampler
    from mwpc_exact.eos_policy import EOSMode, EOSPolicy
    from mwpc_exact.mass_certificate import ProbabilityInput
    from mwpc_exact.reference.byte_grammars import _SourceGrammarBuilder
    from mwpc_exact.reference.ll1 import check_ll1
    from mwpc_exact.reference.normalization import normalize_to_cnf
    from mwpc_exact.state import SelectionInput
    from mwpc_exact.support import SupportPolicy, build_per_position_support
    from mwpc_exact.tokenizer_bytes import CompositionalByteLevelAdapter
    from mwpc_exact.types import SupportKind

    builder = _SourceGrammarBuilder(("S", "P"), start="S")
    builder.rule("S", "P", b"#", "P")
    builder.rule("P", b"(", "P", b")")
    builder.rule("P", b"[", "P", b"]")
    builder.rule("P")
    source = builder.build()
    check_ll1(source)
    for half in (1, 2, 3, 4):
        length = 2 * half + 1
        canvas = (None,) * length
        support = build_per_position_support(
            canvas=canvas,
            policy=SupportPolicy(kind=SupportKind.EXPLICIT, vocabulary_size=5),
            explicit_support={i: tuple(range(5)) for i in range(length)},
        )
        state = SelectionInput(
            normalize_to_cnf(source).grammar,
            canvas,
            (),
            support,
            CompositionalByteLevelAdapter((b"(", b")", b"[", b"]", b"#")),
            EOSPolicy(EOSMode.ABSENT),
        )
        inputs = ProbabilityInput(state, ((Fraction(1, 5),) * 5,) * length)
        result = compile_cfg_sampler(source, state).evaluate(inputs)
        count = (half + 1) * 2**half
        assert result.valid_mass == Fraction(count, 5**length)
        counts = [[0] * 5 for _ in range(length)]
        for marker in range(half + 1):
            for bits in product(range(2), repeat=half):
                word = [4] * length
                for (a, b), bit in zip(mirrors(half, marker), bits, strict=True):
                    word[a], word[b] = 2 * bit, 2 * bit + 1
                for i, token in enumerate(word):
                    counts[i][token] += 1
        expected = tuple(tuple(Fraction(value, count) for value in row) for row in counts)
        assert result.marginals == expected
    return 4


def typed_words(half: int) -> list[tuple[str, ...]]:
    """Build nested blocks directly, without the matching-index formula."""
    closing = {"(": ")", "[": "]"}
    return [
        (
            *left,
            *(closing[c] for c in reversed(left)),
            "#",
            *right,
            *(closing[c] for c in reversed(right)),
        )
        for marker in range(half + 1)
        for left in product("([", repeat=marker)
        for right in product("([", repeat=half - marker)
    ]


def check_multiway_tree_separators(rng: random.Random) -> int:
    """Check the greedy construction by independently traversing components."""
    checked = 0

    def verify(parents: tuple[int, ...], weights: tuple[int, ...]) -> None:
        nonlocal checked
        total = sum(weights)
        adjacency = [set() for _ in parents]
        for node, parent in enumerate(parents[1:], 1):
            adjacency[node].add(parent)
            adjacency[parent].add(node)
        for parts in (2, 3, 4, 8):
            residual = list(weights)
            selected = set()
            for node in reversed(range(len(parents))):
                if parts * residual[node] > total:
                    selected.add(node)
                elif parents[node] >= 0:
                    residual[parents[node]] += residual[node]
            assert len(selected) < parts
            unseen = set(range(len(parents))) - selected
            while unseen:
                stack = [unseen.pop()]
                component = set(stack)
                while stack:
                    for neighbor in adjacency[stack.pop()] & unseen:
                        unseen.remove(neighbor)
                        component.add(neighbor)
                        stack.append(neighbor)
                assert parts * sum(weights[node] for node in component) <= total
            checked += 1

    for size in range(1, 5):
        for tail in product(*(range(node) for node in range(1, size))):
            for weights in product(range(3), repeat=size):
                verify((-1, *tail), weights)
    for size in (8, 16, 32, 64):
        for _ in range(100):
            parents = (-1, *(rng.randrange(node) for node in range(1, size)))
            verify(parents, tuple(rng.randrange(6) for _ in range(size)))
    return checked


def check_multiway_cuts() -> int:
    checked = 0
    for length in (3, 5, 7, 9):
        half = (length - 1) // 2
        for labels in partitions(length, with_separator=True):
            odd = Counter(labels[i] for i in range(1, length, 2) if labels[i] != 0)
            eligible = [
                parts for parts in (2, 3, 4, 8) if parts * max(odd.values(), default=0) <= half
            ]
            if not eligible:
                continue
            removed = labels.count(0)
            cuts = [
                sum(
                    labels[a] != 0 and labels[b] != 0 and labels[a] != labels[b]
                    for a, b in mirrors(half, marker)
                )
                for marker in range(half + 1)
            ]
            good = sum(2 * cut >= half for cut in cuts)
            for parts in eligible:
                assert parts * sum(cuts) >= (half + 1) * (half * (parts - 1) - parts * removed)
                assert parts * half * good >= (half + 1) * (
                    parts * half - 2 * half - 2 * parts * removed
                )
                checked += 1
    return checked


def check_fixed_positions() -> int:
    checked = 0
    for half in range(3):
        words = typed_words(half)
        for pins in product((None, *"()[]#"), repeat=2 * half + 1):
            fixed = sum(pin is not None for pin in pins)
            agree = sum(
                all(pin is None or pin == char for pin, char in zip(pins, word, strict=True))
                for word in words
            )
            assert agree * 2 ** (fixed // 2) <= len(words)
            checked += 1
    return checked


def check_approximation_mixtures(rng: random.Random) -> int:
    """Enumerate the type projection and component products; square overlap."""
    checked = 0
    alphabet = "01#"
    for half in (1, 2, 3):
        length = 2 * half + 1
        target = [
            tuple("#" if c == "#" else str(int(c in "[]")) for c in word)
            for word in typed_words(half)
        ]
        for case in range(60):
            labels = tuple(rng.randrange(4) for _ in range(length))
            separator = [i for i, label in enumerate(labels) if label == 0]
            blocks = [
                tuple(i for i, label in enumerate(labels) if label == block)
                for block in sorted(set(labels) - {0})
            ]
            rank = 1 + case % 4
            mixing = [rng.randrange(1, 6) for _ in range(rank)]
            components = []
            for component in range(rank):
                anchor = target[rng.randrange(len(target))]
                tables = []
                for block in blocks:
                    entries = list(product(alphabet, repeat=len(block)))
                    values = [rng.randrange(5) for _ in entries]
                    if case % 2:
                        values = [
                            int(entry == tuple(anchor[i] for i in block)) for entry in entries
                        ]
                    values[0] += int(not any(values))
                    tables.append(
                        dict(
                            zip(
                                entries,
                                (Fraction(value, sum(values)) for value in values),
                                strict=True,
                            )
                        )
                    )
                components.append((Fraction(mixing[component], sum(mixing)), anchor, tables))
            overlap = Fraction(0)
            for word in target:
                candidate = Fraction(0)
                for weight, anchor, tables in components:
                    if any(word[i] != anchor[i] for i in separator):
                        continue
                    candidate += weight * prod(
                        table[tuple(word[i] for i in block)]
                        for block, table in zip(blocks, tables, strict=True)
                    )
                overlap += min(Fraction(1, len(target)), candidate)
            distance = 1 - overlap
            cuts = [
                sum(
                    labels[a] != 0 and labels[b] != 0 and labels[a] != labels[b]
                    for a, b in mirrors(half, marker)
                )
                for marker in range(half + 1)
            ]
            for threshold in range(1, half + 1):
                alpha = Fraction(sum(cut >= threshold for cut in cuts), half + 1)
                difference = max(Fraction(0), alpha - distance)
                assert difference**2 * 2**threshold <= alpha * rank
                checked += 1
    return checked


def check_operational_counterexamples() -> int:
    checked = 0
    for half in range(1, 7):
        words = typed_words(half)
        count = len(words)
        marginals = [Counter(word[i] for word in words) for i in range(2 * half + 1)]
        overlap = sum(
            min(
                Fraction(1, count),
                prod(Fraction(row[c], count) for row, c in zip(marginals, word, strict=True)),
            )
            for word in words
        )
        assert 0 < overlap < 1
        point_overlap = sum(min(Fraction(1, count), int(word == words[0])) for word in words)
        assert 1 - point_overlap == 1 - Fraction(1, count)
        for marker_weight in (1, 2, 7, 100):
            weights = [marker_weight if word[0] == "#" else 1 for word in words]
            total = sum(weights)
            context_overlap = sum(
                min(Fraction(weight, total), Fraction(1, 2**half))
                for word, weight in zip(words, weights, strict=True)
                if word[0] == "#"
            )
            assert 1 - context_overlap == Fraction(half, marker_weight + half)
            checked += 1
    return checked


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--library", action="store_true", help="also check the installed LL(1) API")
    args = parser.parse_args()
    rng = random.Random(72001)
    covers, cuts, words = check_uniform_palindromes(rng)
    affinities = check_block_affinity(rng)
    weighted = check_typed_blocks(rng)
    result = {
        "palindrome_matching_covers_checked": covers,
        "balanced_component_partitions_checked": cuts,
        "uniform_palindrome_words_checked": words,
        "many_component_affinities_checked": affinities,
        "typed_block_weighted_partitions_checked": weighted,
        "arithmetic": "integer; affinity bounds compared after squaring",
        "neural_model_evaluations": 0,
        "scope": "finite proof-object checks, not novelty or runtime evidence",
    }
    if args.library:
        result["library_posteriors_checked"] = check_library()
    audit_rng = random.Random(72002)
    result.update(
        {
            "multiway_weighted_tree_separators_checked": check_multiway_tree_separators(audit_rng),
            "multiway_component_partitions_checked": check_multiway_cuts(),
            "fixed_position_events_checked": check_fixed_positions(),
            "rational_mixture_approximation_bounds_checked": check_approximation_mixtures(
                audit_rng
            ),
            "operational_counterexamples_checked": check_operational_counterexamples(),
        }
    )
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
