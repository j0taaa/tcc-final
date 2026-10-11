"""A35 proof objects, never a favorable performance/model benchmark."""

import itertools
import unittest
from fractions import Fraction as F
from functools import cache

from mwpc_exact.cfg_posterior import compile_cfg_sampler
from mwpc_exact.eos_policy import EOSMode, EOSPolicy
from mwpc_exact.mass_certificate import ProbabilityInput
from mwpc_exact.reference.byte_grammars import _SourceGrammarBuilder
from mwpc_exact.reference.ll1 import check_ll1
from mwpc_exact.reference.normalization import TerminalRef, normalize_to_cnf
from mwpc_exact.state import SelectionInput
from mwpc_exact.support import SupportPolicy, build_per_position_support
from mwpc_exact.tokenizer_bytes import CompositionalByteLevelAdapter
from mwpc_exact.types import SupportKind


def fixture(terms):
    n, m = len(terms[0]), len(terms)
    names = (
        "S",
        "T",
        "U",
        *(f"E{k}" for k in range(n + 1)),
        *(f"D{j}_{k}" for j in range(m) for k in range(n + 1)),
    )
    b = _SourceGrammarBuilder(names, start="S")
    b.rule("S", b"A", "T")
    b.rule("S", b"B", "U")
    witnesses = tuple(bytes((97 + j,)) for j in range(m))
    for j, (term, witness) in enumerate(zip(terms, witnesses, strict=True)):
        b.rule("T", witness, f"D{j}_0")
        b.rule("U", witness, "E0")
        for k, bit in enumerate(term):
            for value in (0, 1) if bit is None else (bit,):
                b.rule(f"D{j}_{k}", str(value).encode(), f"D{j}_{k + 1}")
        b.rule(f"D{j}_{n}")
    for k in range(n):
        for value in (b"0", b"1"):
            b.rule(f"E{k}", value, f"E{k + 1}")
    b.rule(f"E{n}")
    return b.build(), (b"0", b"1", b"A", b"A", b"B", b"B", *witnesses)


def enumerate_source(source):
    """Enumerate the acyclic SOURCE directly, never using project normalization."""
    terminals = {t.symbol_id: bytes((t.label,)) for t in source.terminals}

    @cache
    def expand(head):
        words = []
        for rule in source.productions:
            if rule.head_id != head:
                continue
            choices = [
                (terminals[s.symbol_id],) if isinstance(s, TerminalRef) else expand(s.symbol_id)
                for s in rule.body
            ]
            words.extend(b"".join(parts) for parts in itertools.product(*choices))
        return tuple(words)

    return expand(source.start_nonterminal_id)


class CommitmentLawCountingTests(unittest.TestCase):
    def test_alias_confidence_union_greedy_mwpc_and_posterior(self):
        cases = (
            ((1, None), (None, 1), (1, None), (None, 1), (1, None)),
            ((1, 0, None), (None, 1, 1), (0, None, 0), (1, 0, None), (None, 1, 1)),
            ((1, None),) * 5,
            ((None,),) * 5,
            ((0, None), (1, None), (0, None), (1, None), (0, None)),
        )
        for terms in cases:
            with self.subTest(terms=terms):
                n, m = len(terms[0]), len(terms)
                source, emissions = fixture(terms)
                check_ll1(source)
                words = enumerate_source(source)
                self.assertEqual(len(words), len(set(words)), "witness must disambiguate")
                assignments = tuple(itertools.product((0, 1), repeat=n))
                satisfying = set().union(
                    *(
                        set(itertools.product(*[(0, 1) if x is None else (x,) for x in t]))
                        for t in terms
                    )
                )
                rows = ((2, 3, 4, 5), tuple(range(6, 6 + m))) + ((0, 1),) * n
                paths = tuple(
                    path
                    for path in itertools.product(*rows)
                    if b"".join(emissions[t] for t in path) in set(words)
                )
                accepted = 0
                for bits in assignments:
                    live = tuple(path for path in paths if path[2:] == bits)
                    self.assertTrue(live, "B makes every argument assignment completable")
                    for ranking in itertools.permutations(rows[0]):
                        chosen = next(t for t in ranking if any(p[0] == t for p in live))
                        accepted += chosen in (2, 3)
                    for flag, witness in itertools.product(rows[0], rows[1]):
                        proposal = (flag, witness, *bits)
                        weights = (F(1, 4), F(1, m)) + (F(1, 2),) * n
                        scores = [
                            sum(
                                w for a, t, w in zip(path, proposal, weights, strict=True) if a == t
                            )
                            for path in paths
                        ]
                        best = max(scores)
                        for path, score in zip(paths, scores, strict=True):
                            if score == best:
                                self.assertEqual(path[2:], bits)
                                self.assertEqual(
                                    path[0] in (2, 3), flag in (2, 3) and bits in satisfying
                                )
                self.assertEqual(F(accepted, 24 * 2**n), F(len(satisfying), 2 ** (n + 1)))

                support = build_per_position_support(
                    canvas=(None,) * len(rows),
                    policy=SupportPolicy(kind=SupportKind.EXPLICIT, vocabulary_size=len(emissions)),
                    explicit_support=dict(enumerate(rows)),
                )
                state = SelectionInput(
                    normalize_to_cnf(source).grammar,
                    (None,) * len(rows),
                    (),
                    support,
                    CompositionalByteLevelAdapter(emissions),
                    EOSPolicy(EOSMode.ABSENT),
                )
                data = ProbabilityInput(state, tuple(tuple(F(1, len(r)) for _ in r) for r in rows))
                result = compile_cfg_sampler(source, state).evaluate(data)
                term_mass = sum(F(1, 2 ** sum(x is not None for x in t)) for t in terms)
                self.assertEqual(result.valid_mass, F(1, 2) + term_mass / (2 * m))
                self.assertEqual(sum(result.marginals[0][:2]), term_mass / (m + term_mass))


if __name__ == "__main__":
    unittest.main()
