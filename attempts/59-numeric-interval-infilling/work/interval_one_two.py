"""Minimal original [1,2) numeral compiler; no decoder/model integration."""

from collections import defaultdict
from fractions import Fraction


class NumberNFA:
    def __init__(self, budget):
        if not isinstance(budget, int) or budget < 1:
            raise ValueError("positive byte budget required")
        self.edges, self.eps, self.accept = defaultdict(list), {}, set()
        self.start = ("start",)

        def edge(source, symbol, target):
            self.edges[source].append((ord(symbol), target))

        def tail(text):
            node = ("tail", text)
            if node in self.edges:
                return node
            self.edges[node] = []
            if text:
                edge(node, text[0], tail(text[1:]))
            else:
                self.accept.add(node)
            return node

        zero_exp = ("exponent-zero",)
        edge(zero_exp, "0", zero_exp)
        self.accept.add(zero_exp)
        for exponent in range(-budget, budget + 1):
            sign, lead = ("sign", exponent), ("lead", exponent)
            self.eps[sign] = lead  # No sign: epsilon belongs before next BYTE.
            if exponent >= 0:
                edge(sign, "+", lead)
            if exponent <= 0:
                edge(sign, "-", lead)
            if exponent == 0:
                edge(lead, "0", zero_exp)
            else:
                edge(lead, "0", lead)
                digits = str(abs(exponent))
                edge(lead, digits[0], tail(digits[1:]))

        edge(self.start, "0", ("integer-zero",))
        edge(self.start, "1", ("integer", 0))
        edge(("integer-zero",), ".", ("leading", -1))
        for order in range(-budget, budget + 1):
            fraction = ("fraction", order)
            for digit in "0123456789":
                edge(fraction, digit, fraction)
            complete = [fraction]
            if order >= 0:
                integer, dot = ("integer", order), ("dot", order)
                edge(integer, ".", dot)
                for digit in "0123456789":
                    edge(dot, digit, fraction)
                    if order < budget:
                        edge(integer, digit, ("integer", order + 1))
                complete.append(integer)
            else:
                leading = ("leading", order)
                edge(leading, "1", fraction)
                if order > -budget:
                    edge(leading, "0", ("leading", order - 1))
            for node in complete:
                for letter in "eE":
                    edge(node, letter, ("sign", -order))
                if order == 0:
                    self.accept.add(node)

    def closure(self, vector):
        # This specialized graph has exactly one acyclic epsilon layer.
        result = defaultdict(Fraction, vector)
        for node, weight in vector.items():
            if node in self.eps:
                result[self.eps[node]] += weight
        return result

    def advance(self, vector, data):
        """No FINAL closure here: token boundaries are not epsilon boundaries."""
        for symbol in data:
            result = defaultdict(Fraction)
            for node, weight in self.closure(vector).items():
                for label, successor in self.edges.get(node, ()):
                    if label == symbol:
                        result[successor] += weight
            vector = result
        return vector

    def paths(self, data):
        vector = self.closure(self.advance({self.start: Fraction(1)}, data))
        return sum((vector.get(node, 0) for node in self.accept), Fraction(0))

    def size(self):
        states = set(self.edges) | set(self.eps) | set(self.eps.values()) | self.accept
        states.update(target for row in self.edges.values() for _, target in row)
        return len(states), sum(map(len, self.edges.values())) + len(self.eps)


def token_mass(automaton, rows, byte_of):
    """Classical sum-product, arbitrary original IDs/aliases and fixed slots."""
    vector = {automaton.start: Fraction(1)}
    for row in rows:
        combined = defaultdict(Fraction)
        for token, probability in row.items():
            for state, weight in automaton.advance(vector, byte_of[token]).items():
                combined[state] += probability * weight
        vector = combined
    final = automaton.closure(vector)
    return sum((final.get(node, 0) for node in automaton.accept), Fraction(0))
