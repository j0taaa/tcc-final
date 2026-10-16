"""Independent JSON parser, full original-word enumeration and class sums."""

import itertools
import json
import random
import re
import unittest
from fractions import Fraction as F
from math import prod

from .numeric_json import STATE_COUNT, TAIL, NumericJSON


class Number(str):
    """Retain arbitrary JSON exponent text without a Decimal/float range cap."""


def independent_accepts(language, word):
    if language.eos not in word:
        return False
    boundary = word.index(language.eos)
    if any(v != language.pad for v in word[boundary + 1 :]):
        return False
    try:
        text = b"".join(language.emissions[v] for v in word[:boundary]).decode("utf8")
        if not re.match(r'\A[ \t\r\n]*\{[ \t\r\n]*"answer"[ \t\r\n]*:', text):
            return False
        value = json.loads(
            text,
            parse_int=Number,
            parse_float=Number,
            object_pairs_hook=lambda pairs: pairs,
            parse_constant=lambda name: (_ for _ in ()).throw(ValueError(name)),
        )
        return (
            type(value) is list
            and len(value) == 1
            and value[0][0] == "answer"
            and type(value[0][1]) is Number
        )
    except (ValueError, UnicodeError, IndexError, TypeError):
        return False


class NumericConsumerTests(unittest.TestCase):
    def test_json_number_syntax_independent_parser_and_specials(self):
        corpus = [
            b'{"answer":0}',
            b' \t{ "answer" : -0.125e+100000000000000000000000000 }\n',
            b'{"answer":10}',
            b'{"answer":-1E-3}',
            b'{"answer":false}',
            b'{"answer":01}',
            b'{"answer":+1}',
            b'{"answer":1.}',
            b'{"answer":.1}',
            b'{"answer":1e}',
            b'{"answer":NaN}',
            b'{"answer":Infinity}',
            b'{"answer":0,"answer":1}',
            b'{"Answer":0}',
            b'{"answer":"0"}',
            b'{"answer":[]}',
            b'\v{"answer":0}',
            b'{"\\u0061nswer":0}',
        ]
        ea, eb, eos, pad = range(len(corpus), len(corpus) + 4)
        language = NumericJSON((*corpus, b"", b"", b"<EOT>", b"<PAD>"), eos, pad)
        for i in range(len(corpus)):
            for word in ((i, eos), (ea, i, eb, eos, pad), (i,), (i, eos, eb), (i, pad, eos)):
                self.assertEqual(language.accepts(word), independent_accepts(language, word), word)
        self.assertEqual(language.step(TAIL, ea), -1)
        self.assertEqual(language.step(TAIL, pad), TAIL)

    def test_all_small_original_words_and_global_class_reduction(self):
        emissions = (
            b'{"answer":',
            b"0",
            b"1",
            b"-2.0e3",
            b"}",
            b'{"answer":0}',
            b'{"answer":0}',
            b" ",
            b"",
            b"",
            b"<EOT>",
            b"<PAD>",
        )
        language = NumericJSON(emissions, 10, 11)
        effects, members, mapping = language.classes()
        self.assertEqual(sorted(v for group in members for v in group), list(range(len(emissions))))
        self.assertEqual(mapping[5], mapping[6])
        self.assertEqual(mapping[8], mapping[9])
        for v in range(len(emissions)):
            for state in range(STATE_COUNT):
                self.assertEqual(effects[mapping[v]][state], language.step(state, v))
        rng, total_words = random.Random(5206), 0
        for length in (2, 3, 4):
            rows = tuple(tuple(F(rng.randrange(1, 9)) for _ in emissions) for _ in range(length))
            graph = language.small_reference_graph(length)
            exact = F()
            for word in itertools.product(range(len(emissions)), repeat=length):
                expected = independent_accepts(language, word)
                self.assertEqual(language.accepts(word), expected, word)
                if expected:
                    exact += prod(rows[i][v] for i, v in enumerate(word))
                total_words += 1
            self.assertEqual(graph.infer(rows)[0], exact)
            beta = [F(s == TAIL) for s in range(STATE_COUNT)]
            for row in reversed(rows):
                masses = [sum((row[v] for v in group), F()) for group in members]
                beta = [
                    sum(
                        (
                            masses[c] * beta[effects[c][state]]
                            for c in range(len(members))
                            if effects[c][state] >= 0
                        ),
                        F(),
                    )
                    for state in range(STATE_COUNT)
                ]
            self.assertEqual(beta[0], exact)
        print(
            json.dumps(
                {
                    "numeric_original_words": total_words,
                    "classes": len(members),
                    "original_ids": len(emissions),
                }
            )
        )


if __name__ == "__main__":
    unittest.main()
