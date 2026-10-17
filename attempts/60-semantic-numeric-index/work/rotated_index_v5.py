"""Tiny rational source-cut reference for ALL nonnegative JSON magnitudes.

Returns (canonical significand digits, decimal order), never expands10^order.
Cyclic shift/digit arithmetic/prefix queries are classical; no native decoder.
"""

from collections import defaultdict, deque
from fractions import Fraction

from .semantic_index import SemanticIndex


class DAG:
    def __init__(self):
        self.edges, self.final, self.start = [[]], set(), 0

    def fresh(self):
        self.edges.append([])
        return len(self.edges) - 1

    def path(self, source, target, text, weight=Fraction(1)):
        if not text:
            self.edges[source].append(("", target, weight))
        for i, char in enumerate(text):
            successor = target if i + 1 == len(text) else self.fresh()
            self.edges[source].append((char, successor, weight if i == 0 else Fraction(1)))
            source = successor

    def finish(self):
        degree = [0] * len(self.edges)
        for row in self.edges:
            for _, target, _ in row:
                degree[target] += 1
        ready = deque(q for q, n in enumerate(degree) if n == 0)
        self.topology = []
        while ready:
            q = ready.popleft()
            self.topology.append(q)
            for _, target, _ in self.edges[q]:
                degree[target] -= 1
                if degree[target] == 0:
                    ready.append(target)
        if len(self.topology) != len(self.edges):
            raise ValueError("acyclic source required")
        self.beta = [Fraction(q in self.final) for q in range(len(self.edges))]
        for q in reversed(self.topology):
            self.beta[q] += sum((w * self.beta[t] for _, t, w in self.edges[q]), Fraction(0))
        self.mass = self.beta[self.start]


def mantissa_step(phase, residual, stopped, char):
    def digits(next_phase, counter):
        if stopped:
            return [(next_phase, counter, True, "")] if char == "0" else []
        return [(next_phase, counter, False, char)] + (
            [(next_phase, counter, True, char)] if char != "0" else []
        )

    if phase == "start":
        if char == "0":
            return [("zero", residual, False, "")]
        return digits("int", residual) if "1" <= char <= "9" else []
    if phase == "zero":
        return [("leading", residual + 1, False, "")] if char == "." else []
    if phase == "leading":
        if char == "0":
            return [(phase, residual + 1, False, "")]
        return digits("frac", residual) if "1" <= char <= "9" else []
    if phase in {"int", "dot", "frac"}:
        if "0" <= char <= "9":
            return digits("int", residual - 1) if phase == "int" else digits("frac", residual)
        if phase == "int" and char == ".":
            return [("dot", residual, stopped, "")]
    return []


def zero_next(phase, char):
    if phase == "start" and char == "-":
        return "minus"
    if phase in {"start", "minus"} and char == "0":
        return "int"
    if phase == "int" and char == ".":
        return "dot"
    if phase in {"dot", "frac"} and char == "0":
        return "frac"
    if phase in {"int", "frac"} and char in "eE":
        return "sign"
    if phase == "sign" and char in "+-":
        return "first"
    if phase in {"sign", "first", "exp"} and "0" <= char <= "9":
        return "exp"
    return None


class RotatedIndex(DAG):
    # Reuse only V1's classical, unchanged weighted-DAG query algorithms.
    events, quantile = SemanticIndex.events, SemanticIndex.quantile

    def __init__(self, rows, byte_of, budget=None):
        super().__init__()
        rows = [{t: Fraction(w) for t, w in row.items()} for row in rows]
        if any(w < 0 for row in rows for w in row.values()):
            raise ValueError("nonnegative finite rational weights required")
        bound = sum(max((len(byte_of[t]) for t, w in row.items() if w), default=0) for row in rows)
        if budget is None:
            budget = max(1, bound)
        if not isinstance(budget, int) or budget < max(1, bound):
            raise ValueError("valid positive source byte bound required")
        self.byte_bound, self.width, self.budget = budget, budget + 1, 2 * budget + 3
        source, position = DAG(), 0
        for row in rows:
            target = source.fresh()
            for token, weight in row.items():
                if weight:
                    source.path(position, target, byte_of[token].decode("latin1"), weight)
            position = target
        source.final.add(position)
        source.finish()
        self.source = source
        reverse = defaultdict(list)
        for q, row in enumerate(source.edges):
            for _, target, _ in row:
                reverse[target].append(q)
        ancestors = {}

        def can_reach(cut):
            if cut not in ancestors:
                reached, frontier = {cut}, [cut]
                while frontier:
                    for q in reverse[frontier.pop()]:
                        if q not in reached:
                            reached.add(q)
                            frontier.append(q)
                ancestors[cut] = reached
            return ancestors[cut]

        zeros = {source.start: {"start": Fraction(1)}}
        for q in source.topology:
            for char, target, weight in source.edges[q]:
                out = zeros.setdefault(target, defaultdict(Fraction))
                for phase, value in zeros.get(q, {}).items():
                    successor = zero_next(phase, char) if char else phase
                    if successor is not None:
                        out[successor] += value * weight
        self.zero_mass = sum(
            (w for phase, w in zeros.get(position, {}).items() if phase in {"int", "frac", "exp"}),
            Fraction(0),
        )
        if self.zero_mass:
            terminal = self.fresh()
            self.final.add(terminal)
            self.path(self.start, terminal, "0", self.zero_mass)

        pending, memo = deque(), {}

        def node(tag, state):
            key = tag, state
            if key not in memo:
                memo[key] = self.fresh()
                pending.append(key)
            return memo[key]

        def mantissa(cut, counter):
            return node("mantissa", (cut, source.start, "start", counter, False))

        for order in range(-budget, budget + 1):
            self.path(self.start, mantissa(position, order), "1" + self.order_code(order))
        for cut, row in enumerate(source.edges):
            for char, target, weight in row:
                if char in {"e", "E"}:
                    for sign in (-1, 1):
                        start = node("sign", (cut, target, sign, 1, True))
                        self.path(self.start, start, "1" + ("1" if sign == 1 else "0"), weight)

        while pending:
            tag, state = pending.popleft()
            here = memo[tag, state]
            if tag == "mantissa":
                cut, q, phase, counter, stopped = state
                if q == cut:
                    if phase in {"int", "frac"} and counter == 0 and stopped:
                        self.final.add(here)
                    continue
                for char, target, weight in source.edges[q]:
                    if target not in can_reach(cut):
                        continue
                    choices = (
                        mantissa_step(phase, counter, stopped, char)
                        if char
                        else [(phase, counter, stopped, "")]
                    )
                    for p, c, stop, output in choices:
                        if abs(c) <= 2 * budget + 2:
                            self.path(here, node(tag, (cut, target, p, c, stop)), output, weight)
            elif tag == "sign":
                cut, q, sign, input_sign, optional = state
                for char, target, weight in source.edges[q]:
                    if not char:
                        successor = node(tag, (cut, target, sign, input_sign, optional))
                    elif optional and char in "+-":
                        successor = node(tag, (cut, target, sign, 1 if char == "+" else -1, False))
                    elif "0" <= char <= "9":
                        successor = node(
                            "pad", (cut, target, sign, input_sign, int(char), 0, 0, False)
                        )
                    else:
                        continue
                    self.path(here, successor, "", weight)
            elif tag == "pad":
                cut, q, sign, input_sign, held, pos, delta, nonzero = state
                if pos >= self.width:
                    continue
                for digit in range(10):
                    output = str(digit if sign == 1 else 9 - digit)
                    seen = nonzero or digit != 0
                    shifted = 10 * delta + sign * digit
                    if abs(shifted) <= budget + 2 and pos + 1 < self.width:
                        successor = node(
                            tag, (cut, q, sign, input_sign, held, pos + 1, shifted, seen)
                        )
                        self.path(here, successor, output)
                    paired = shifted - input_sign * held
                    if abs(paired) <= budget + 2:
                        successor = node("read", (cut, q, sign, input_sign, pos + 1, paired, seen))
                        self.path(here, successor, output)
            elif tag == "read":
                cut, q, sign, input_sign, pos, delta, nonzero = state
                if q == position:
                    if pos == self.width and abs(delta) <= budget and (sign == 1 or nonzero):
                        self.path(here, mantissa(cut, delta), "")
                    continue
                for char, target, weight in source.edges[q]:
                    if not char:
                        successor = node(tag, (cut, target, sign, input_sign, pos, delta, nonzero))
                        self.path(here, successor, "", weight)
                    elif pos < self.width and "0" <= char <= "9":
                        for digit in range(10):
                            difference = 10 * delta + sign * digit - input_sign * int(char)
                            if abs(difference) <= budget + 2:
                                successor = node(
                                    tag,
                                    (
                                        cut,
                                        target,
                                        sign,
                                        input_sign,
                                        pos + 1,
                                        difference,
                                        nonzero or digit != 0,
                                    ),
                                )
                                self.path(
                                    here, successor, str(digit if sign == 1 else 9 - digit), weight
                                )
        self.finish()
        self.raw_size = len(self.edges), sum(map(len, self.edges))
        if not self.mass:
            self.edges, self.final, self.topology, self.beta = [[]], set(), [0], [Fraction(0)]
        else:
            live = [q for q in self.topology if self.beta[q]]
            renumber = {q: i for i, q in enumerate(live)}
            self.edges = [
                [(c, renumber[t], w) for c, t, w in self.edges[q] if self.beta[t]] for q in live
            ]
            self.final = {renumber[q] for q in self.final if q in renumber}
            self.beta = [self.beta[q] for q in live]
            self.start = renumber[self.start]
            self.topology = list(range(len(live)))

    def order_code(self, order):
        magnitude, reversed_digits = abs(order), []
        while magnitude:
            magnitude, digit = divmod(magnitude, 10)
            reversed_digits.append(str(digit))
        digits = ("".join(reversed(reversed_digits)) or "0").zfill(self.width)
        if len(digits) != self.width:
            raise ValueError("order outside source encoding")
        if order >= 0:
            return "1" + digits
        return "0" + "".join(str(9 - int(c)) for c in digits)

    def value(self, key):
        if key == "0":
            return "0", 0
        sign, encoded = key[1], key[2 : 2 + self.width]
        order = 0
        for char in encoded:
            order = 10 * order + (int(char) if sign == "1" else 9 - int(char))
        return key[2 + self.width :], order if sign == "1" else -order

    def cdf(self, threshold, inclusive=True):
        if not self.mass:
            raise ValueError("EMPTY numerical support")
        digits, order = threshold
        if digits == "0" and order == 0:
            return self.zero_mass / self.mass if inclusive else Fraction(0)
        if (
            not isinstance(order, int)
            or not digits
            or digits[0] == "0"
            or digits[-1] == "0"
            or any(c not in "0123456789" for c in digits)
        ):
            raise ValueError("canonical nonnegative scientific threshold required")
        limit = 10**self.width
        if order >= limit:
            return Fraction(1)
        if order <= -limit:
            return self.zero_mass / self.mass
        key = "1" + self.order_code(order) + digits
        vector, less = {self.start: Fraction(1)}, Fraction(0)
        for char in key:
            terminal, masses, forward = self.events(vector)
            less += terminal + sum((w for c, w in masses.items() if c < char), Fraction(0))
            vector = forward.get(char, {})
        terminal, _, _ = self.events(vector)
        return (less + (terminal if inclusive else 0)) / self.mass
