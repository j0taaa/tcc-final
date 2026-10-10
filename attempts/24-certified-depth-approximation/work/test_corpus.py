"""Pinned original documents must not change with sampling randomness."""

import hashlib
import tempfile
import unittest
import zipfile
from pathlib import Path

from .corpus import select_independent


class CorpusIdentityTests(unittest.TestCase):
    def test_identity_is_fixed_but_source_bytes_still_must_match(self):
        class Tokenizer:
            @staticmethod
            def encode(text, add_special_tokens):
                return list(range(20))

        documents = {"y_first.json": b'{"x":1}', "y_second.json": b'{"x":2}'}
        corpus = dict(
            revision="pinned",
            identity_seed=7,
            eligible_count=2,
            cases=[
                dict(
                    key=hashlib.sha256(b"7/" + raw).hexdigest(),
                    file=name,
                    source_sha256=hashlib.sha256(raw).hexdigest(),
                )
                for name, raw in documents.items()
            ],
        )
        protocol = dict(seed=10, independent_corpus=corpus, external=dict(eligible_tokens=[16, 96]))
        with tempfile.TemporaryDirectory() as tmp:
            archive = Path(tmp) / "corpus.zip"
            with zipfile.ZipFile(archive, "w") as target:
                for name, raw in documents.items():
                    target.writestr("JSONTestSuite-pinned/test_parsing/" + name, raw)
            first = select_independent(archive, Tokenizer(), protocol)
            protocol["seed"] = 999
            self.assertEqual(first, select_independent(archive, Tokenizer(), protocol))
            corpus["cases"][0]["source_sha256"] = "0" * 64
            with self.assertRaises(ValueError):
                select_independent(archive, Tokenizer(), protocol)
