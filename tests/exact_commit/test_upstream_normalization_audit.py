from __future__ import annotations

from itertools import product

import pytest

from mwpc_exact.reference.grammar import from_repository_cnf

rustformlang_cfg = pytest.importorskip(
    "rustformlang.cfg", reason="pinned EPIC Rust binding is not built"
)


@pytest.mark.integration
@pytest.mark.parametrize(
    ("name", "text", "vocabulary"),
    [
        (
            "epsilon",
            "S -> A B | epsilon\nA -> a | epsilon\nB -> b",
            ("a", "b"),
        ),
        (
            "unit",
            "S -> A\nA -> B | a\nB -> S | b",
            ("a", "b"),
        ),
        ("recursive", "S -> S A | a\nA -> b", ("a", "b")),
        (
            "ambiguous",
            "S -> A B | C D\nA -> a\nB -> b\nC -> a\nD -> b",
            ("a", "b"),
        ),
    ],
)
def test_pinned_upstream_normalizer_preserves_fixture_language_but_not_strict_cnf(
    name: str, text: str, vocabulary: tuple[str, ...]
) -> None:
    cfg_type = rustformlang_cfg.CFG
    source = cfg_type.from_text(text, "S")
    normalized = source.to_normal_form()

    for length in range(5):
        for word in product(vocabulary, repeat=length):
            assert source.accepts(list(word)) == normalized.accepts(list(word)), (
                name,
                word,
            )

    if name in {"epsilon", "unit"}:
        expected = "only the CNF start symbol" if name == "epsilon" else "unit production"
        with pytest.raises(ValueError, match=expected):
            from_repository_cnf(normalized)
