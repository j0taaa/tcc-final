"""Independent exact A88 oracle. Freeze this source before running --audit.

Fixed cases: binary stationary 9/10 fork; contextual R=1/5 or 4/5;
temperature-two q != p; both position ties; zero-k with changing heads;
forced-all; zero support; state-dependent ternary heads with k=1 and k=2;
coherent joint ((1/2,1/200,1/200),(0,49/200,49/200)).
Enumerate ALL native proposals/complete paths independently of auxiliary paths.
Check exact means, simplex, every clean-coordinate principal covariance minor,
the common-auxiliary stopping-time coupling and expected forward counts.
No model, float probabilities, PRNG, native timing or priority claim.
"""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from collections.abc import Callable, Iterator
from dataclasses import dataclass
from fractions import Fraction as F
from itertools import combinations, product

Vector = tuple[F, ...]
Canvas = tuple[int, ...]


def law(*weights: int | F) -> Vector:
    """Clean-token weights followed by an explicit zero-probability MASK ID."""
    total = sum(weights, F(0))
    return (*(F(w) / total for w in weights), F(0))


@dataclass(frozen=True)
class Head:
    q: Vector
    p: Vector

    def validate(self) -> None:
        if len(self.q) != len(self.p) or len(self.q) < 3:
            raise ValueError("matching full vocabularies with at least two clean IDs required")
        if any(not isinstance(x, F) or x < 0 for row in (self.q, self.p) for x in row):
            raise ValueError("nonnegative exact rational heads required")
        if sum(self.q) != 1 or sum(self.p) != 1 or self.q[-1] != 0:
            raise ValueError("normalized heads and zero proposal MASK support required")


@dataclass(frozen=True)
class Case:
    name: str
    initial: Canvas
    observed: int
    schedule: tuple[int, ...]
    heads: Callable[[Canvas, int], tuple[Head, ...]]
    revisable: bool = False

    def validate(self) -> int:
        rows = self.heads(self.initial, 0)
        mask = len(rows[0].q) - 1
        if self.revisable or not 0 <= self.observed < len(self.initial):
            raise ValueError("monotone observed-position contract required")
        if len(rows) != len(self.initial) or self.initial[self.observed] != mask:
            raise ValueError("observed position must initially be MASK")
        if any(not isinstance(k, int) or k < 0 for k in self.schedule):
            raise ValueError("nonnegative public transfer counts required")
        if sum(self.schedule) != self.initial.count(mask):
            raise ValueError("finite clean schedule must fill the canvas")
        for row in rows:
            row.validate()
        return mask


def proposals(rows: tuple[Head, ...], positions: list[int]) -> Iterator[tuple[F, dict[int, int]]]:
    supports = [[v for v, q in enumerate(rows[i].q) if q] for i in positions]
    for values in product(*supports):
        prob = F(1)
        for i, v in zip(positions, values, strict=True):
            prob *= rows[i].q[v]
        yield prob, dict(zip(positions, values, strict=True))


def rank(rows: tuple[Head, ...], i: int, v: int) -> tuple[F, int]:
    return rows[i].p[v], -i  # Higher score wins; the smaller position wins ties.


def write(state: Canvas, values: dict[int, int], selected: list[int]) -> Canvas:
    return tuple(values[i] if i in selected else old for i, old in enumerate(state))


def readout(rows: tuple[Head, ...], f: int, free_values: dict[int, int], k: int) -> Vector:
    """Selection-aware conditional law, used only after a native f hit."""
    if k > len(free_values):
        return rows[f].q
    cutoff = sorted((rank(rows, i, v) for i, v in free_values.items()), reverse=True)[k - 1]
    values = tuple(q if rank(rows, f, v) > cutoff else F(0) for v, q in enumerate(rows[f].q))
    total = sum(values)
    assert total > 0
    return tuple(x / total for x in values)


def native(case: Case, mask: int) -> list[tuple[F, Vector, Vector, int]]:
    """Enumerate complete generation, including proposals discarded after k=0."""
    result = []

    def visit(state: Canvas, t: int, prob: F, first: Vector | None, cost: int) -> None:
        if t == len(case.schedule):
            assert mask not in state and first is not None
            onehot = tuple(F(v == state[case.observed]) for v in range(mask + 1))
            result.append((prob, onehot, first, cost))
            return
        rows = case.heads(state, t)
        for row in rows:
            row.validate()
        positions = [i for i, v in enumerate(state) if v == mask]
        k = case.schedule[t]
        assert k <= len(positions)
        for branch, values in proposals(rows, positions):
            selected = sorted(positions, key=lambda i: rank(rows, i, values[i]), reverse=True)[:k]
            next_first, next_cost = first, cost
            if first is None and case.observed in selected:
                free = {i: v for i, v in values.items() if i != case.observed}
                next_first, next_cost = readout(rows, case.observed, free, k), t + 1
            visit(write(state, values, selected), t + 1, prob * branch, next_first, next_cost)

    visit(case.initial, 0, F(1), None, 0)
    assert sum(p for p, _, _, _ in result) == 1
    return result


def auxiliary(
    case: Case, mask: int
) -> list[tuple[F, Vector, int, tuple[tuple[F, Vector, int], ...]]]:
    """Separate recursion: no native selected proposal or transition is reused."""
    result = []
    zero = (F(0),) * (mask + 1)

    def visit(state: Canvas, t: int, prob: F, y: Vector, w: F, hits: tuple) -> None:
        assert t < len(case.schedule) and state[case.observed] == mask
        rows = case.heads(state, t)
        for row in rows:
            row.validate()
        free = [i for i, v in enumerate(state) if v == mask and i != case.observed]
        k = case.schedule[t]
        if k == 0:
            visit(state, t + 1, prob, y, w, hits)
        elif k > len(free):
            final = tuple(a + w * b for a, b in zip(y, rows[case.observed].q, strict=True))
            result.append((prob, final, t + 1, (*hits, (w, rows[case.observed].q, t + 1))))
        else:
            for branch, values in proposals(rows, free):
                selected = sorted(free, key=lambda i: rank(rows, i, values[i]), reverse=True)[:k]
                cutoff = rank(rows, selected[-1], values[selected[-1]])
                a = tuple(
                    q if rank(rows, case.observed, v) > cutoff else F(0)
                    for v, q in enumerate(rows[case.observed].q)
                )
                mass = sum(a)
                next_y = tuple(x + w * z for x, z in zip(y, a, strict=True))
                next_w = w * (1 - mass)
                next_hits = hits + (
                    ((w * mass, tuple(x / mass for x in a), t + 1),) if mass else ()
                )
                if next_w == 0:
                    result.append((prob * branch, next_y, t + 1, next_hits))
                else:
                    visit(
                        write(state, values, selected),
                        t + 1,
                        prob * branch,
                        next_y,
                        next_w,
                        next_hits,
                    )

    visit(case.initial, 0, F(1), zero, F(1), ())
    assert sum(p for p, _, _, _ in result) == 1
    return result


def mean_cov(distribution: list[tuple[F, Vector]], dim: int) -> tuple[Vector, list[list[F]]]:
    mean = tuple(sum((p * v[i] for p, v in distribution), F(0)) for i in range(dim))
    cov = [
        [
            sum((p * (v[i] - mean[i]) * (v[j] - mean[j]) for p, v in distribution), F(0))
            for j in range(dim)
        ]
        for i in range(dim)
    ]
    return mean, cov


def determinant(matrix: list[list[F]]) -> F:
    if not matrix:
        return F(1)
    return sum(
        (
            (-1) ** j * x * determinant([row[:j] + row[j + 1 :] for row in matrix[1:]])
            for j, x in enumerate(matrix[0])
        ),
        F(0),
    )


def psd_difference(left: list[list[F]], right: list[list[F]]) -> None:
    dim = len(left)
    for size in range(1, dim + 1):
        for subset in combinations(range(dim), size):
            assert determinant([[left[i][j] - right[i][j] for j in subset] for i in subset]) >= 0


def cases() -> list[Case]:
    binary = law(1, 1)
    fork = law(9, 1)

    def two(
        name: str, target: Callable[[Canvas, int], Head], free: Head, schedule=(1, 1), f=0
    ) -> Case:
        return Case(
            name,
            (2, 2),
            f,
            schedule,
            lambda s, t: (target(s, t), free) if f == 0 else (free, target(s, t)),
        )

    constant = Head(fork, fork)
    free_binary = Head(binary, binary)
    result = [two("stationary-99-01", lambda s, t: constant, free_binary)]
    result += [
        two(
            "contextual-epsilon",
            lambda s, t: (
                Head(law(1, 4) if s[1] == 0 else law(4, 1), law(1, 4) if s[1] == 0 else law(4, 1))
                if s[1] != 2
                else constant
            ),
            free_binary,
        )
    ]
    result += [two("temperature-two", lambda s, t: Head(law(2, 1), law(4, 1)), free_binary)]
    result += [two(f"tie-f-{f}", lambda s, t: free_binary, free_binary, f=f) for f in (0, 1)]
    result += [
        two(
            "zero-k-changing-time",
            lambda s, t: Head(law(t + 1, 4), law(t + 1, 4)),
            free_binary,
            (0, 1, 1),
        )
    ]
    result += [two("forced-all", lambda s, t: constant, free_binary, (2,))]
    result += [two("zero-probabilities", lambda s, t: free_binary, Head(law(1, 0), law(1, 0)))]

    def ternary(state: Canvas, t: int) -> tuple[Head, ...]:
        rows = []
        for i in range(3):
            weights = tuple(
                1
                + (i + 1) * (v + 1)
                + t
                + sum((j + 1) * (x + v + 1) for j, x in enumerate(state) if x != 3)
                for v in range(3)
            )
            q = law(*weights)
            rows.append(Head(q, q))
        return tuple(rows)

    result += [
        Case(f"ternary-stateful-{schedule}", (3, 3, 3), 1, schedule, ternary)
        for schedule in ((1, 1, 1), (2, 1))
    ]
    joint = ((F(1, 2), F(1, 200), F(1, 200)), (F(0), F(49, 200), F(49, 200)), (F(0), F(0), F(0)))

    def coherent(state: Canvas, t: int) -> tuple[Head, ...]:
        allowed = [
            (a, b)
            for a, b in product(range(3), repeat=2)
            if (state[0] == 3 or a == state[0]) and (state[1] == 3 or b == state[1])
        ]
        normalizer = sum((joint[a][b] for a, b in allowed), F(0))
        assert normalizer > 0
        rows = []
        for i in range(2):
            q = (
                *(
                    sum((joint[a][b] for a, b in allowed if (a, b)[i] == v), F(0)) / normalizer
                    for v in range(3)
                ),
                F(0),
            )
            rows.append(Head(q, q))
        return tuple(rows)

    result.append(Case("coherent-cost-counterexample", (3, 3), 0, (1, 1), coherent))
    return result


def audit() -> dict[str, object]:
    report = []
    for case in cases():
        mask = case.validate()
        baseline, aux = native(case, mask), auxiliary(case, mask)
        counts = [(p, one) for p, one, _, _ in baseline]
        stopped = [(p, rb) for p, _, rb, _ in baseline]
        candidate = [(p, y) for p, y, _, _ in aux]
        mu, count_cov = mean_cov(counts, mask)
        rb_mu, rb_cov = mean_cov(stopped, mask)
        y_mu, y_cov = mean_cov(candidate, mask)
        assert mu == rb_mu == y_mu
        native_hits: dict[tuple[Vector, int], F] = defaultdict(F)
        coupled_hits: dict[tuple[Vector, int], F] = defaultdict(F)
        conditional_gap = [[F(0) for _ in range(mask)] for _ in range(mask)]
        for p, _, rb, cost in baseline:
            native_hits[rb, cost] += p
        for p, y, _, hits in aux:
            assert all(v >= 0 for v in y) and sum(y) == 1 and y[-1] == 0
            assert sum(w for w, _, _ in hits) == 1
            assert tuple(sum((w * h[i] for w, h, _ in hits), F(0)) for i in range(mask + 1)) == y
            _, local_cov = mean_cov([(w, h) for w, h, _ in hits], mask)
            for i, j in product(range(mask), repeat=2):
                conditional_gap[i][j] += p * local_cov[i][j]
            for w, h, cost in hits:
                coupled_hits[h, cost] += p * w
        assert native_hits == coupled_hits
        assert conditional_gap == [
            [rb_cov[i][j] - y_cov[i][j] for j in range(mask)] for i in range(mask)
        ]
        psd_difference(count_cov, rb_cov)
        psd_difference(rb_cov, y_cov)
        expected_y = sum((p * cost for p, _, cost, _ in aux), F(0))
        expected_rb = sum((p * cost for p, _, _, cost in baseline), F(0))
        assert expected_rb <= expected_y <= len(case.schedule)
        if case.name == "stationary-99-01":
            assert mu == (F(99, 100), F(1, 100)) and y_cov[1][1] == 0
            assert case.heads(case.initial, 0)[case.observed].q[:mask] != mu
            assert rb_cov[1][1] == F(9, 10000) and expected_rb == F(11, 10) and expected_y == 2
        if case.name == "contextual-epsilon":
            assert mu[0] == F(19, 20) and y_cov[0][0] == F(9, 10000) and rb_cov[0][0] == F(63, 2000)
            assert expected_y * y_cov[0][0] < expected_rb * rb_cov[0][0]
        if case.name == "coherent-cost-counterexample":
            assert mu[1] == F(49, 200) and rb_cov == y_cov
            assert expected_y == F(3, 2) and expected_rb == F(249, 200)
            assert expected_y * y_cov[0][0] > expected_rb * rb_cov[0][0]
        report.append(
            {
                "case": case.name,
                "native_leaves": len(baseline),
                "aux_leaves": len(aux),
                "mean": list(map(str, mu)),
                "candidate_nfe": str(expected_y),
                "stopped_nfe": str(expected_rb),
            }
        )
    invalid = Head((F(1, 2), F(1, 4), F(1, 4)), law(1, 1))
    for action in (
        invalid.validate,
        lambda: Case("revision", (2, 2), 0, (1, 1), cases()[0].heads, True).validate(),
    ):
        try:
            action()
        except ValueError:
            continue
        raise AssertionError("unsupported contract was accepted")
    return {
        "protocol": "A88-independent-rational-v1",
        "cases": report,
        "refusals": 2,
        "scope": "finite rational laws and logical NFE only; no native/model/performance claim",
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--audit", action="store_true", help="only after source freeze")
    if parser.parse_args().audit:
        print(json.dumps(audit(), sort_keys=True))
