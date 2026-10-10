"""Weighted unranking of the maintained LL(1) original-token posterior forest.

Classical unranking. Reuses inside values without enumerating token strings.
This experimental adapter does not change posterior weights or core sampling.
"""

from bisect import bisect_right
from functools import lru_cache
from itertools import accumulate

from .batch import Kernel


class CfgRanks:
    def __init__(self, posterior):
        self.posterior = posterior
        self.plan = posterior._plan
        self.inside = posterior._inside
        self.weights = posterior._weights
        root = self.plan.root
        if root is None or not self.inside[root]:
            raise ValueError("zero_valid_mass: no conditional batch exists")
        self.total = self.inside[root]
        self.cdf = tuple(
            tuple(accumulate(self.plan.term_mass(t, self.weights, self.inside) for t in terms))
            for terms in self.plan.terms
        )
        self.kernel = Kernel(self.total, self.unrank)

    def unrank(self, rank):
        if type(rank) is not int or not 0 <= rank < self.total:
            raise ValueError("rank outside original integer mass")
        pending, output = [(self.plan.root, rank)], []
        while pending:
            node, local = pending.pop()
            index = bisect_right(self.cdf[node], local)
            term = self.plan.terms[node][index]
            if index:
                local -= self.cdf[node][index - 1]
            if term.choice is not None:
                position, row_index = term.choice
                if position != len(output):
                    raise RuntimeError("unranking changed physical token order")
                output.append(self.plan.state.support.rows[position][row_index])
            elif term.children:
                left, right = term.children
                left_rank, right_rank = divmod(local, self.inside[right])
                pending.extend(((right, right_rank), (left, left_rank)))
            elif local:
                raise RuntimeError("neutral leaf has non-unit weight")
        if len(output) != len(self.posterior.inputs.state.canvas):
            raise RuntimeError("unranking changed physical slot count")
        return tuple(output)

    def evidence_prefix(self, allowed, boundaries):
        """Count evidence-compatible tickets below each boundary, without draws.

        allowed maps physical positions to sets of ORIGINAL IDs. Other slots
        are unrestricted. Evidence is an auditor input, never sampler guidance.
        Counts may be non-contiguous because weighted product leaves repeat.
        """
        allowed = {p: frozenset(tokens) for p, tokens in allowed.items()}
        if any(
            type(p) is not int or not 0 <= p < len(self.posterior.inputs.state.canvas)
            for p in allowed
        ):
            raise ValueError("evidence position outside physical slots")
        filtered, term_prefix = [0] * len(self.plan.terms), [()] * len(self.plan.terms)
        for node in self.plan.order:
            values = []
            for term in self.plan.terms[node]:
                if term.choice is not None:
                    p, j = term.choice
                    token = self.plan.state.support.rows[p][j]
                    value = self.weights[p][j] if p not in allowed or token in allowed[p] else 0
                elif term.children:
                    left, right = term.children
                    value = filtered[left] * filtered[right]
                else:
                    value = 1
                values.append(value)
            term_prefix[node] = tuple(accumulate(values))
            filtered[node] = sum(values)

        @lru_cache(None)
        def compatible(node, rank):
            if not filtered[node]:
                return False
            if filtered[node] == self.inside[node]:
                return True
            index = bisect_right(self.cdf[node], rank)
            local = rank - (self.cdf[node][index - 1] if index else 0)
            term = self.plan.terms[node][index]
            if term.choice is not None:
                p, j = term.choice
                return p not in allowed or self.plan.state.support.rows[p][j] in allowed[p]
            if term.children:
                left, right = term.children
                a, b = divmod(local, self.inside[right])
                return compatible(left, a) and compatible(right, b)
            return True

        @lru_cache(None)
        def prefix(node, stop):
            if not stop or not filtered[node]:
                return 0
            if stop == self.inside[node]:
                return filtered[node]
            index = bisect_right(self.cdf[node], stop - 1)
            offset = self.cdf[node][index - 1] if index else 0
            count = term_prefix[node][index - 1] if index else 0
            term, local = self.plan.terms[node][index], stop - offset
            if term.choice is not None:
                p, j = term.choice
                token = self.plan.state.support.rows[p][j]
                return count + (local if p not in allowed or token in allowed[p] else 0)
            if term.children:
                left, right = term.children
                whole, remainder = divmod(local, self.inside[right])
                count += prefix(left, whole) * filtered[right]
                if remainder and compatible(left, whole):
                    count += prefix(right, remainder)
                return count
            return count + local

        result = []
        for stop in boundaries:
            if type(stop) is not int or not 0 <= stop <= self.total:
                raise ValueError("evidence boundary outside integer mass")
            result.append(prefix(self.plan.root, stop))
        return tuple(result)
