from __future__ import annotations

import pytest

from mwpc_exact import (
    BYTE_LEVEL_ALPHABET,
    CompositionalByteLevelAdapter,
    UnsupportedTokenError,
    byte_level_piece_to_bytes,
)


def test_byte_level_alphabet_is_a_complete_bijection() -> None:
    assert len(BYTE_LEVEL_ALPHABET) == 256
    assert len(set(BYTE_LEVEL_ALPHABET)) == 256
    assert BYTE_LEVEL_ALPHABET[10] == "Ċ"
    assert BYTE_LEVEL_ALPHABET[32] == "Ġ"
    assert BYTE_LEVEL_ALPHABET[65] == "A"
    assert BYTE_LEVEL_ALPHABET[0xA9] == "©"
    assert BYTE_LEVEL_ALPHABET[0xF0] == "ð"
    assert b"".join(byte_level_piece_to_bytes(piece) for piece in BYTE_LEVEL_ALPHABET) == bytes(
        range(256)
    )


@pytest.mark.parametrize(
    ("piece", "expected"),
    [
        ("hello", b"hello"),
        ("Ġworld", b" world"),
        ("Ċ", b"\n"),
        ("ðŁĳ", bytes.fromhex("f09f91")),
        ("©", bytes.fromhex("a9")),
    ],
)
def test_piece_mapping_matches_known_llada_bytelevel_pieces(piece: str, expected: bytes) -> None:
    assert byte_level_piece_to_bytes(piece) == expected


def test_adapter_composes_byte_fragments_before_unicode_rendering() -> None:
    adapter = CompositionalByteLevelAdapter.from_token_pieces(
        ("hello", "Ġworld", "ðŁĳ", "©", None)
    )

    assert adapter.detokenize_bytes((0, 1)) == b"hello world"
    assert adapter.token_bytes(2) == bytes.fromhex("f09f91")
    assert adapter.token_bytes(3) == bytes.fromhex("a9")
    assert adapter.detokenize_bytes((2, 3)).decode("utf-8") == "👩"
    assert adapter.vocabulary_size == 5
    assert adapter.unsupported_token_ids == (4,)


def test_adapter_rejects_control_token_and_invalid_ids() -> None:
    adapter = CompositionalByteLevelAdapter.from_token_pieces(("A", None))

    with pytest.raises(UnsupportedTokenError, match="token ID 1"):
        adapter.token_bytes(1)
    with pytest.raises(ValueError, match=r"\[0, 2\)"):
        adapter.token_bytes(2)
    with pytest.raises(TypeError, match="integer"):
        adapter.token_bytes(True)


@pytest.mark.parametrize("piece", ["", "☃"])
def test_piece_mapping_rejects_empty_or_non_bytelevel_pieces(piece: str) -> None:
    with pytest.raises(ValueError):
        byte_level_piece_to_bytes(piece)


def test_adapter_rejects_empty_emissions_at_construction() -> None:
    with pytest.raises(ValueError, match="empty"):
        CompositionalByteLevelAdapter(emissions=(b"",))
