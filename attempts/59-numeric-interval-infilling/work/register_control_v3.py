"""Classical lazy semantic register control, independent of the candidate NFA."""

from collections import defaultdict
from fractions import Fraction


class RegisterNumber:
    start = ("start",)

    def __init__(self, budget):
        if not isinstance(budget, int) or budget < 1:
            raise ValueError("positive byte budget required")
        self.budget = budget

    @staticmethod
    def _leading(target, char):
        if char == "0":
            return ("exp-zero",) if target == 0 else ("exp-leading", target)
        digits = str(target)
        return ("exp-tail", digits[1:]) if char == digits[0] else None

    def next(self, state, byte):
        if state is None:
            return None
        char, phase = chr(byte), state[0]
        if phase == "start":
            return {"0": ("zero",), "1": ("integer", 0)}.get(char)
        if phase == "zero":
            return ("before-significant", -1) if char == "." else None
        if phase == "before-significant":
            order = state[1]
            if char == "1":
                return ("fraction", order)
            if char == "0" and order > -self.budget:
                return (phase, order - 1)
            return None
        if phase in ("integer", "fraction", "dot"):
            order = state[1]
            if char in "0123456789":
                if phase != "integer":
                    return ("fraction", order)
                return (phase, order + 1) if order < self.budget else None
            if phase == "integer" and char == ".":
                return ("dot", order)
            if phase != "dot" and char in "eE":
                return ("exp-sign", -order)
            return None
        if phase == "exp-sign":
            target = state[1]
            if (char == "+" and target >= 0) or (char == "-" and target <= 0):
                return ("exp-leading", abs(target))
            return self._leading(target, char) if target >= 0 else None
        if phase == "exp-leading":
            return self._leading(state[1], char)
        if phase == "exp-zero":
            return state if char == "0" else None
        if phase == "exp-tail" and state[1] and char == state[1][0]:
            return (phase, state[1][1:])
        return None

    @staticmethod
    def accepts(state):
        return state is not None and (
            state == ("exp-zero",)
            or state == ("exp-tail", "")
            or state in (("integer", 0), ("fraction", 0))
        )

    def advance(self, state, data):
        for byte in data:
            state = self.next(state, byte)
        return state

    def mass(self, rows, byte_of):
        vector = {self.start: Fraction(1)}
        cache = {}
        for row in rows:
            result = defaultdict(Fraction)
            for state, weight in vector.items():
                for token, probability in row.items():
                    key = (state, byte_of[token])
                    if key not in cache:
                        cache[key] = self.advance(state, byte_of[token])
                    target = cache[key]
                    if target is not None:
                        result[target] += weight * probability
            vector = result
        return sum((weight for state, weight in vector.items() if self.accepts(state)), Fraction(0))
