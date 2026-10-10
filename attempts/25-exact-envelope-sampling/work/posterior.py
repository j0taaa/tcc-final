"""Exact integer posterior for overlapping lexical groups, original marginals."""

from math import isfinite


class Weights:
    def __init__(self, rows, canvas, vocabulary_size):
        self.rows, self.denominators = [], []
        self.canvas = tuple(canvas)
        self.vocabulary_size = vocabulary_size
        if len(rows) != len(canvas):
            raise ValueError("probability rows differ from physical slots")
        for row, fixed in zip(rows, canvas, strict=True):
            if fixed is not None:
                if type(fixed) is not int or not 0 <= fixed < vocabulary_size:
                    raise ValueError("invalid original fixed token")
                self.rows.append({fixed: 1})
                self.denominators.append(1)
                continue
            if len(row) != vocabulary_size or any(not isfinite(x) or x < 0 for x in row):
                raise ValueError("invalid full-vocabulary probability row")
            ratios = [float(x).as_integer_ratio() for x in row]
            bits = max((d.bit_length() - 1 for n, d in ratios if n), default=0)
            integers = tuple(n << (bits - (d.bit_length() - 1)) if n else 0 for n, d in ratios)
            denominator = sum(integers)
            if not denominator:
                raise ValueError("zero model row")
            self.rows.append(integers)
            self.denominators.append(denominator)

    def at(self, p, t):
        row = self.rows[p]
        return row.get(t, 0) if isinstance(row, dict) else row[t]


def class_weights(table, weights):
    rows = []
    for row in weights.rows:
        sums = [0] * len(table.classes)
        if isinstance(row, dict):
            for t, w in row.items():
                sums[table.class_of[t]] += w
        else:
            for t, w in enumerate(row):
                sums[table.class_of[t]] += w
        rows.append(sums)
    return rows


class Posterior:
    @staticmethod
    def choose(masses, rng):
        total = sum(masses)
        if total <= 0:
            raise ValueError("zero conditional choice")
        positive = [i for i, m in enumerate(masses) if m]
        if len(positive) == 1:
            return positive[0]
        point = rng.randrange(total)
        for i, m in enumerate(masses):
            if point < m:
                return i
            point -= m
        raise RuntimeError("integer choice lost probability")


def lift_marginals(prepared, weights, leaf, coefficient, total, *, fixed_conservation=None):
    table = prepared.table
    numerators = []
    for p, fixed in enumerate(weights.canvas):
        if fixed is not None:
            conservation = (
                fixed_conservation[p]
                if fixed_conservation is not None
                else sum(leaf[key] * value for key, value in coefficient.items() if key[0] == p)
            )
            if conservation != total:
                raise RuntimeError("outside lost fixed original conservation")
            numerators.append({fixed: total})
            continue
        if prepared.kind == "local":
            factors = [
                sum(
                    coefficient.get((p, gid), 0)
                    for q in table.by_state
                    if (gid := table.class_to_local[q][cid]) >= 0
                )
                for cid in range(len(table.classes))
            ]
        elif prepared.kind == "global":
            factors = [coefficient.get((p, cid), 0) for cid in range(len(table.classes))]
        elif prepared.kind == "position":
            factors = [
                coefficient.get((p, prepared.position_of[p][cid]), 0)
                for cid in range(len(table.classes))
            ]
        else:
            factors = None
        row = tuple(
            weights.at(p, t)
            * (coefficient.get((p, t), 0) if factors is None else factors[table.class_of[t]])
            for t in range(weights.vocabulary_size)
        )
        if sum(row) != total or (fixed is not None and row[fixed] != total):
            raise RuntimeError("outside lost original-token marginal conservation")
        numerators.append(row)
    # Consumers receive exact numerator vectors and common denominator.
    return tuple(numerators), total
