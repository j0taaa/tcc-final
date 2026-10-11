"""Exact uniform-ticket representation of the known count-noising law."""

from math import comb, lcm

import numpy as np


class CountSource:
    def __init__(self, n):
        if not isinstance(n, int) or n < 1:
            raise ValueError("a positive integer token count is required")
        self.n = n
        self.counts = [comb(n, k) for k in range(1, n + 1)]
        self.block = lcm(*self.counts)
        self.size = n * self.block

    def decode(self, address):
        if not isinstance(address, int) or not 0 <= address < self.size:
            raise ValueError("source address out of range")
        k, remainder = divmod(address, self.block)
        k += 1
        rank = remainder // (self.block // self.counts[k - 1])
        mask = np.zeros(self.n, dtype=bool)
        for position in range(self.n):
            if k == 0:
                break
            first = comb(self.n - position - 1, k - 1)
            if rank < first:
                mask[position] = True
                k -= 1
            else:
                rank -= first
        assert rank == k == 0
        return mask
