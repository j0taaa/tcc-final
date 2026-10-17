"""Exact [1,100) decimal-value index of finite rational original-token rows.

Research reference only: one frozen product source, no native decoder binding.
Weighted projection, DAG sums and prefix unranking are classical algorithms.
"""

from collections import defaultdict, deque
from fractions import Fraction


class Normalizer:
    def __init__(self, budget):
        if not isinstance(budget, int) or budget < 1:
            raise ValueError("positive byte bound required")
        self.budget = budget

    @staticmethod
    def start(order):
        return order, "start", 0, False

    @staticmethod
    def accepts(state):
        order, phase, data, stopped = state
        return (
            (phase in {"int", "frac"} and stopped and data == order)
            or (phase == "tail" and data == "")
            or phase == "exp-zero"
        )

    def step(self, state, byte):
        order, phase, data, stopped = state
        char = chr(byte)

        def node(p, d=data, stop=stopped):
            return order, p, d, stop

        def significant(p, d):
            if stopped:
                return [(node(p, d, True), "")] if char == "0" else []
            result = [(node(p, d, False), char)]
            if char != "0":
                result.append((node(p, d, True), char))
            return result

        if phase == "start":
            if char == "0":
                return [(node("zero"), "")]
            return significant("int", 0) if "1" <= char <= "9" else []
        if phase == "zero":
            return [(node("leading", -1), "")] if char == "." else []
        if phase == "leading":
            if char == "0" and data > -self.budget:
                return [(node("leading", data - 1), "")]
            return significant("frac", data) if "1" <= char <= "9" else []
        if phase in {"int", "dot", "frac"}:
            if "0" <= char <= "9":
                if phase == "int":
                    return significant("int", data + 1) if data < self.budget else []
                return significant("frac", data)
            if phase == "int" and char == ".":
                return [(node("dot"), "")]
            if phase != "dot" and stopped and char in "eE":
                return [(node("sign", order - data, False), "")]
            return []
        if phase == "sign":
            if (char == "+" and data >= 0) or (char == "-" and data <= 0):
                return [(node("exp-leading", abs(data)), "")]
            if data < 0:
                return []  # A negative target REQUIRES its minus sign.
            phase = "exp-leading"  # An absent sign consumes this same digit.
        if phase == "exp-leading":
            if char == "0":
                return [(node("exp-zero" if data == 0 else phase), "")]
            digits = str(data)
            if data != 0 and char == digits[0]:
                return [(node("tail", digits[1:]), "")]
            return []
        if phase == "exp-zero":
            return [(state, "")] if char == "0" else []
        if phase == "tail" and data and char == data[0]:
            return [(node("tail", data[1:]), "")]
        return []

    def advance(self, state, data):
        paths = [(state, "")]
        for byte in data:
            paths = [
                (successor, output + label)
                for current, output in paths
                for successor, label in self.step(current, byte)
            ]
        return paths  # Do not deduplicate paths and thereby hide ambiguity.

    def normalize(self, data):
        return [
            header + output
            for order, header in enumerate("ab")
            for state, output in self.advance(self.start(order), data)
            if self.accepts(state)
        ]


class SemanticIndex:
    def __init__(self, rows, byte_of, budget=None):
        rows = [{token: Fraction(weight) for token, weight in row.items()} for row in rows]
        if any(weight < 0 for row in rows for weight in row.values()):
            raise ValueError("nonnegative finite rational weights required")
        bound = sum(max((len(byte_of[t]) for t, w in row.items() if w), default=0) for row in rows)
        if budget is None:
            budget = max(1, bound)
        if budget < bound:
            raise ValueError("byte bound smaller than positive source support")
        self.budget, self.normalizer = budget, Normalizer(budget)
        self.edges, self.final = [], set()

        def fresh():
            self.edges.append([])
            return len(self.edges) - 1

        def arc(source, target, text, weight):
            if not text:
                self.edges[source].append(("", target, weight))
                return
            for i, char in enumerate(text):
                successor = target if i == len(text) - 1 else fresh()
                self.edges[source].append((char, successor, weight if i == 0 else Fraction(1)))
                source = successor

        self.start = fresh()
        layer = {}
        for order, header in enumerate("ab"):
            state = self.normalizer.start(order)
            layer[state] = fresh()
            arc(self.start, layer[state], header, Fraction(1))
        for row in rows:
            next_layer = {}
            for state, source in layer.items():
                for token, weight in row.items():
                    if weight:
                        for successor, output in self.normalizer.advance(state, byte_of[token]):
                            if successor not in next_layer:
                                next_layer[successor] = fresh()
                            arc(source, next_layer[successor], output, weight)
            layer = next_layer
        self.final.update(q for state, q in layer.items() if self.normalizer.accepts(state))
        indegree = [0] * len(self.edges)
        for row in self.edges:
            for _, target, _ in row:
                indegree[target] += 1
        ready = deque(q for q, degree in enumerate(indegree) if degree == 0)
        self.topology = []
        while ready:
            q = ready.popleft()
            self.topology.append(q)
            for _, target, _ in self.edges[q]:
                indegree[target] -= 1
                if indegree[target] == 0:
                    ready.append(target)
        if len(self.topology) != len(self.edges):
            raise ValueError("acyclic source required")
        self.beta = [Fraction(q in self.final) for q in range(len(self.edges))]
        for q in reversed(self.topology):
            self.beta[q] += sum((w * self.beta[t] for _, t, w in self.edges[q]), Fraction(0))
        self.mass = self.beta[self.start]

    def events(self, vector):
        closed = defaultdict(Fraction, vector)
        for q in self.topology:
            if closed[q]:
                for char, target, weight in self.edges[q]:
                    if not char:
                        closed[target] += closed[q] * weight
        terminal = sum((closed[q] for q in self.final), Fraction(0))
        forward, masses = {}, defaultdict(Fraction)
        for q, value in closed.items():
            if value:
                for char, target, weight in self.edges[q]:
                    if char and self.beta[target]:
                        forward.setdefault(char, defaultdict(Fraction))[target] += value * weight
                        masses[char] += value * weight * self.beta[target]
        return terminal, masses, forward

    @staticmethod
    def value(key):
        order, digits = "ab".index(key[0]), key[1:]
        return Fraction(int(digits)) * Fraction(10) ** (order - len(digits) + 1)

    def quantile(self, probability):
        probability = Fraction(probability)
        if not 0 < probability <= 1:
            raise ValueError("quantile probability must be in (0,1]")
        if not self.mass:
            raise ValueError("EMPTY numerical support")
        rank, key, vector = probability * self.mass, "", {self.start: Fraction(1)}
        for _ in range(self.budget + 2):
            terminal, masses, forward = self.events(vector)
            if rank <= terminal:
                return self.value(key)
            rank -= terminal
            for char in sorted(masses):
                if rank <= masses[char]:
                    key, vector = key + char, forward[char]
                    break
                rank -= masses[char]
            else:
                raise ArithmeticError("rank escaped its exact prefix block")
        raise ArithmeticError("canonical key exceeds source byte bound")

    def cdf(self, threshold, inclusive=True):
        if not self.mass:
            raise ValueError("EMPTY numerical support")
        threshold = Fraction(threshold)
        if threshold < 1:
            return Fraction(0)
        if threshold >= 100:
            return Fraction(1)
        order = int(threshold >= 10)
        unit = Fraction(10) ** (order - self.budget + 1)
        digits = threshold // unit
        # Every source value in this decimal order lies on this finer grid.
        include_endpoint = inclusive or threshold != digits * unit
        key = "ab"[order] + str(digits).rstrip("0")
        less, vector = Fraction(0), {self.start: Fraction(1)}
        for char in key:
            terminal, masses, forward = self.events(vector)
            less += terminal + sum((w for c, w in masses.items() if c < char), Fraction(0))
            vector = forward.get(char, {})
        terminal, _, _ = self.events(vector)
        return (less + (terminal if include_endpoint else 0)) / self.mass
