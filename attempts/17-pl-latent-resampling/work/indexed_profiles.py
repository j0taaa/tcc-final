"""Classical compact representation of the same rounded-profile control."""

from bisect import bisect_left
from fractions import Fraction as Q

from resampling import RoundedProfiles, deadline


class IndexedProfiles(RoundedProfiles):
    def __init__(self, *args, **kwargs):
        self.leaf_indices = {}
        self.merge_offsets = {}
        self.difference_threshold = None
        super().__init__(*args, **kwargs)

    def round(self, value):
        if not value:
            return 0
        if value not in self.leaf_indices:
            while self.grid[-1] < value:
                deadline(self.end)
                self.grid.append(self.grid[-1] * self.gamma)
            self.leaf_indices[value] = bisect_left(self.grid, value) + 1
        return self.leaf_indices[value]

    def combine(self, left, right):
        if not left or not right:
            return left or right
        if self.difference_threshold is None:
            power, threshold = Q(1), 0
            while power * (self.gamma - 1) < 1:
                deadline(self.end)
                power *= self.gamma
                threshold += 1
            self.difference_threshold = threshold
        difference = abs(left - right)
        if difference >= self.difference_threshold:
            offset = difference + 1
        else:
            if difference not in self.merge_offsets:
                value = 1 + self.gamma**-difference
                low, high = 0, 1
                while self.gamma**high < value:
                    deadline(self.end)
                    high *= 2
                while low + 1 < high:
                    deadline(self.end)
                    middle = (low + high) // 2
                    if self.gamma**middle < value:
                        low = middle
                    else:
                        high = middle
                self.merge_offsets[difference] = difference + high
            offset = self.merge_offsets[difference]
        return min(left, right) + offset
