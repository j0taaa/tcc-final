"""Uniform distinct source indices, without rejected label queries or floats."""


class Source:
    def __init__(self, size, query, randrange):
        if not isinstance(size, int) or size < 4:
            raise ValueError("source size must be an integer >=4")
        self.size, self.query, self.randrange = size, query, randrange
        self.seen = []

    def __call__(self):
        if len(self.seen) == 4:
            raise ValueError("four-query budget exhausted")
        index = self.randrange(self.size - len(self.seen))
        if not isinstance(index, int) or not 0 <= index < self.size - len(self.seen):
            raise ValueError("randrange returned an invalid rank")
        for previous in sorted(self.seen):
            if index >= previous:
                index += 1
        self.seen.append(index)
        return self.query(index)
