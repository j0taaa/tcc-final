"""Lossless ByteLevel support construction at a tokenizer integration boundary."""

from typing import Any

from mwpc_exact.tokenizer_bytes import byte_level_piece_to_bytes


def encode_call(
    tokenizer: Any, call: str, *, slots: int, eos: int
) -> tuple[list[int], dict[int, bytes]]:
    tokens = tokenizer.encode(call, add_special_tokens=False)
    if eos in tokens:
        raise ValueError("UNSUPPORTED: ordinary call contains a control token")
    if len(tokens) >= slots:
        raise ValueError(f"UNSUPPORTED: call needs {len(tokens) + 1} slots; configured {slots}")
    emissions = {
        token: byte_level_piece_to_bytes(tokenizer.convert_ids_to_tokens(token)) for token in tokens
    }
    if b"".join(emissions[token] for token in tokens) != call.encode("utf-8"):
        raise ValueError("UNSUPPORTED: tokenizer pieces do not reconstruct the call bytes")
    return tokens + [eos] * (slots - len(tokens)), emissions
