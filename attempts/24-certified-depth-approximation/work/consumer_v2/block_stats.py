"""Exact binary64 class/block masses; independent vectorized CPU control."""

from dataclasses import dataclass

import numpy as np

MASK32 = (1 << 32) - 1
MASK52 = (1 << 52) - 1


class Partition:
    def __init__(self, class_of, class_count, block_size=512):
        self.class_of = tuple(class_of)
        if not self.class_of or type(class_count) is not int or class_count <= 0:
            raise ValueError("nonempty positive partition required")
        if any(type(c) is not int or not 0 <= c < class_count for c in self.class_of):
            raise ValueError("invalid original-ID partition")
        if type(block_size) is not int or not 1 <= block_size <= 1024:
            raise ValueError("block size must be in1..1024")
        self.class_count, self.block_size = class_count, block_size
        members = [[] for _ in range(class_count)]
        for token, cid in enumerate(self.class_of):
            members[cid].append(token)
        self.blocks, self.block_classes = [], []
        self.class_blocks = [[] for _ in range(class_count)]
        self.block_of = [None] * len(self.class_of)
        for cid, ids in enumerate(members):
            for start in range(0, len(ids), block_size):
                bid = len(self.blocks)
                block = tuple(ids[start : start + block_size])
                self.blocks.append(block)
                self.block_classes.append(cid)
                self.class_blocks[cid].append(bid)
                for token in block:
                    self.block_of[token] = bid
        self.blocks = tuple(self.blocks)
        self.permutation = tuple(t for block in self.blocks for t in block)
        self.starts = tuple(np.cumsum([0] + [len(b) for b in self.blocks[:-1]]).tolist())
        self.sizes = tuple(map(len, self.blocks))


@dataclass(frozen=True)
class BlockStats:
    partition: Partition
    minimum_exponents: tuple
    totals: tuple
    digit_words: int

    @classmethod
    def from_digits(cls, partition, exponents, digits):
        rows = tuple(
            tuple(sum(int(d) << (32 * j) for j, d in enumerate(block)) for block in row)
            for row in digits
        )
        if any(not sum(row) for row in rows):
            raise ValueError("zero original row")
        return cls(partition, tuple(map(int, exponents)), rows, digits.shape[-1])

    def class_sums(self):
        return tuple(
            tuple(sum(row[b] for b in bids) for bids in self.partition.class_blocks)
            for row in self.totals
        )


def integer_weight(value, minimum_exponent):
    """Exactly remove a row-common dyadic scale; reject an incompatible scale."""
    n, d = float(value).as_integer_ratio()
    shift = 1074 - (d.bit_length() - 1) - minimum_exponent
    if shift >= 0:
        return n << shift
    quotient, remainder = divmod(n, 1 << -shift)
    if remainder:
        raise ValueError("row scale does not divide original weight")
    return quotient


def numpy_stats(weights, partition):
    weights = np.asarray(weights)
    if weights.dtype != np.float64 or weights.ndim != 2:
        raise ValueError("binary64 matrix required")
    if weights.shape[1] != len(partition.class_of) or not weights.shape[0]:
        raise ValueError("matrix differs from partition")
    if np.any(~np.isfinite(weights)) or np.any(weights < 0):
        raise ValueError("nonnegative finite weights required")
    bits = weights.view(np.uint64)
    exponent = ((bits >> np.uint64(52)) & np.uint64(2047)).astype(np.int64)
    mantissa = (bits & np.uint64(MASK52)) | ((exponent > 0).astype(np.uint64) << np.uint64(52))
    shifts = np.maximum(exponent - 1, 0)
    positive = weights > 0
    minimum = np.where(positive, shifts, 2048).min(axis=1)
    if np.any(minimum == 2048):
        raise ValueError("zero original row")
    span = (np.where(positive, shifts, 0).max(axis=1) - minimum + 53).max()
    words = (int(span) + 31) // 32
    relative = shifts - minimum[:, None]
    digits = np.empty((len(weights), len(partition.blocks), words), dtype=np.uint64)
    block_of = np.asarray(partition.block_of)
    for j in range(words):
        delta = relative - 32 * j
        left = (mantissa << np.maximum(delta, 0).astype(np.uint64)) & np.uint64(MASK32)
        right = (mantissa >> np.maximum(-delta, 0).astype(np.uint64)) & np.uint64(MASK32)
        digit = np.where((delta >= 0) & (delta < 32), left, np.where(delta < 0, right, 0))
        for row in range(len(weights)):
            # Positive integer sums <2^42 are EXACT in binary64 (53-bit mantissa).
            # This supplies a strong vectorized control without Python V loops.
            digits[row, :, j] = np.bincount(
                block_of, weights=digit[row].astype(np.float64), minlength=len(partition.blocks)
            ).astype(np.uint64)
    return BlockStats.from_digits(partition, minimum, digits)
