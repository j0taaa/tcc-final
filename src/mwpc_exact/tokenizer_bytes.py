"""Exact compositional byte emission for GPT-2-style ByteLevel vocabularies.

This module deliberately has no dependency on Transformers or Tokenizers.  A
model adapter supplies the token pieces from its pinned tokenizer artifact;
the code here only implements the fixed ByteLevel byte-to-Unicode bijection
and an immutable token-ID lookup.
"""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from dataclasses import dataclass


def _build_byte_level_alphabet() -> tuple[str, ...]:
    direct_bytes = (
        list(range(ord("!"), ord("~") + 1))
        + list(range(ord("¡"), ord("¬") + 1))
        + list(range(ord("®"), ord("ÿ") + 1))
    )
    ordered_bytes = list(direct_bytes)
    code_points = list(direct_bytes)
    extra_index = 0
    for byte_value in range(256):
        if byte_value not in direct_bytes:
            ordered_bytes.append(byte_value)
            code_points.append(256 + extra_index)
            extra_index += 1

    alphabet = [""] * 256
    for byte_value, code_point in zip(ordered_bytes, code_points, strict=True):
        alphabet[byte_value] = chr(code_point)
    return tuple(alphabet)


BYTE_LEVEL_ALPHABET = _build_byte_level_alphabet()
"""ByteLevel character indexed by its raw byte value."""

_BYTE_BY_CHARACTER = {character: value for value, character in enumerate(BYTE_LEVEL_ALPHABET)}


class UnsupportedTokenError(ValueError):
    """Raised when a token has no ordinary grammar-byte emission."""


def byte_level_piece_to_bytes(piece: str) -> bytes:
    """Invert one GPT-2-style ByteLevel vocabulary piece to raw bytes.

    Empty pieces and characters outside the 256-character ByteLevel alphabet
    are rejected instead of being silently dropped or encoded as Unicode.
    """

    if not isinstance(piece, str):
        raise TypeError("ByteLevel token piece must be a string")
    if not piece:
        raise ValueError("empty ByteLevel token pieces are unsupported")

    output = bytearray()
    for character in piece:
        byte_value = _BYTE_BY_CHARACTER.get(character)
        if byte_value is None:
            raise ValueError(
                "ByteLevel token piece contains a character outside the byte alphabet: "
                f"U+{ord(character):04X}"
            )
        output.append(byte_value)
    return bytes(output)


@dataclass(frozen=True, slots=True)
class CompositionalByteLevelAdapter:
    """Immutable token-ID to raw-byte mapping for a frozen vocabulary.

    ``None`` marks control/added token IDs that the ordinary byte grammar does
    not support. Every supported token must emit at least one byte.
    """

    emissions: tuple[bytes | None, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.emissions, tuple):
            raise TypeError("emissions must be a tuple")
        if not self.emissions:
            raise ValueError("emissions must contain at least one token ID")
        for token_id, emission in enumerate(self.emissions):
            if emission is None:
                continue
            if not isinstance(emission, bytes):
                raise TypeError(f"emission for token ID {token_id} must be bytes or None")
            if not emission:
                raise ValueError(f"empty emission for token ID {token_id} is unsupported")

    @classmethod
    def from_token_pieces(
        cls, token_pieces: Sequence[str | None]
    ) -> CompositionalByteLevelAdapter:
        """Build a mapping from ByteLevel pieces; ``None`` remains unsupported."""

        if isinstance(token_pieces, (str, bytes)) or not isinstance(token_pieces, Sequence):
            raise TypeError("token_pieces must be a sequence of strings or None")
        emissions = tuple(
            None if piece is None else byte_level_piece_to_bytes(piece) for piece in token_pieces
        )
        return cls(emissions=emissions)

    @property
    def vocabulary_size(self) -> int:
        """Return the total number of represented token IDs."""

        return len(self.emissions)

    @property
    def unsupported_token_ids(self) -> tuple[int, ...]:
        """Return every token ID excluded from ordinary grammar emission."""

        return tuple(
            token_id for token_id, emission in enumerate(self.emissions) if emission is None
        )

    def token_bytes(self, token_id: int) -> bytes:
        """Return one token's emission or reject an invalid/unsupported ID."""

        if isinstance(token_id, bool) or not isinstance(token_id, int):
            raise TypeError("token_id must be an integer")
        if token_id < 0 or token_id >= self.vocabulary_size:
            raise ValueError(f"token_id must be in [0, {self.vocabulary_size})")
        emission = self.emissions[token_id]
        if emission is None:
            raise UnsupportedTokenError(
                f"token ID {token_id} is not an ordinary grammar-emitting token"
            )
        return emission

    def detokenize_bytes(self, token_ids: Iterable[int]) -> bytes:
        """Concatenate exact raw emissions in token order."""

        if isinstance(token_ids, (str, bytes)) or not isinstance(token_ids, Iterable):
            raise TypeError("token_ids must be an iterable of integers")
        return b"".join(self.token_bytes(token_id) for token_id in token_ids)
