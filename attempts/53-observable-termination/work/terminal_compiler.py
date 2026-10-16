"""Classical flat backward pass; original IDs and first EOS stay explicit."""

from .flat_language import EMPTY, MANY, analyze, classify, concat, join
from .numeric_json import STATE_COUNT, TAIL, NumericJSON


class NumericSuffix(NumericJSON):
    def __post_init__(self):
        if not 0 <= self.eos < len(self.emissions) or self.pad != self.eos:
            raise ValueError("explicit original EOS=PAD required")
        if any(type(e) is not bytes for e in self.emissions):
            raise TypeError("original byte emissions required")

    def step(self, state, token):
        if state == TAIL:
            return TAIL
        return super().step(10 if state == 0 else state, token)


def project(raw, erase_whitespace):
    return raw.translate(None, b" \t\r\n") if erase_whitespace else raw


class TerminalCompiler:
    def __init__(self, grammar, erase_whitespace):
        self.grammar = grammar
        effects, members, self.mapping = grammar.classes()
        self.effects, self.members = effects, members
        self.erase = erase_whitespace
        self.labels = []
        self.representatives = []
        for tokens in members:
            reps = []
            for v in tokens:
                out = b"" if v == grammar.eos else project(grammar.emissions[v], self.erase)
                if out not in reps:
                    reps.append(out)
                if len(reps) == 2:
                    break
            self.representatives.append(tuple(reps))
            self.labels.append(classify(reps))
        self.eos_class = self.mapping[grammar.eos]
        if self.members[self.eos_class] != (grammar.eos,):
            raise ValueError("first-EOS control must have its own class")

    def validate(self, width, fixed):
        if type(width) is not int or not 1 <= width <= 64:
            raise ValueError("bounded canvas required")
        if any(
            type(i) is not int
            or not 0 <= i < width
            or type(v) is not int
            or not 0 <= v < len(self.grammar.emissions)
            for i, v in fixed.items()
        ):
            raise ValueError("original fixed ID/position outside canvas")
        stops = [i for i, v in fixed.items() if v == self.grammar.eos]
        if len(stops) > 1 or (stops and max(fixed) != stops[0]):
            raise ValueError("EOS would truncate an original fixed ID")

    def choices(self, i, fixed):
        if i in fixed:
            v = fixed[i]
            return (
                (
                    self.mapping[v],
                    (
                        b""
                        if v == self.grammar.eos
                        else project(self.grammar.emissions[v], self.erase),
                    ),
                ),
            )
        return enumerate(self.representatives)

    def classify(self, width, fixed):
        self.validate(width, fixed)
        suffix = [EMPTY] * STATE_COUNT
        last = max(fixed, default=-1)
        for i in reversed(range(width)):
            values = [EMPTY] * STATE_COUNT
            for c, reps in self.choices(i, fixed):
                eos = c == self.eos_class
                label = classify(reps)
                for s, target in enumerate(self.effects[c]):
                    if s == TAIL or target < 0:
                        continue
                    if eos:
                        value = b"" if target == TAIL and i >= last else EMPTY
                    else:
                        value = concat(label, suffix[target])
                    values[s] = join(values[s], value)
            suffix = values
        return suffix[0]

    def generic_graph_control(self, width, fixed):
        """Two representative strings suffice for exact singleton classification.

        This separate generic DAG algorithm gives the SAME classical rule;
        it is a correctness control, not a novel competing theory.
        """
        self.validate(width, fixed)
        terminal = (width + 1) * STATE_COUNT
        edges = [[] for _ in range(terminal + 1)]
        last = max(fixed, default=-1)
        for i in range(width):
            for c, reps in self.choices(i, fixed):
                for s, target in enumerate(self.effects[c]):
                    if s == TAIL or target < 0:
                        continue
                    if c == self.eos_class:
                        if target == TAIL and i >= last:
                            edges[i * STATE_COUNT + s].append((b"", terminal))
                    else:
                        for out in reps:
                            edges[i * STATE_COUNT + s].append((out, (i + 1) * STATE_COUNT + target))
        return analyze(edges, {terminal})[0]

    def witness_projection(self, word):
        if not word or word[-1] != self.grammar.eos or self.grammar.eos in word[:-1]:
            raise ValueError("original first-EOS witness required")
        state = 0
        for v in word:
            state = self.grammar.step(state, v)
            if state < 0:
                raise ValueError("invalid witness")
        if state != TAIL:
            raise ValueError("nonterminal witness")
        return project(b"".join(self.grammar.emissions[v] for v in word[:-1]), self.erase)


def encode(value):
    if value is EMPTY:
        return {"kind": "EMPTY"}
    if value is MANY:
        return {"kind": "MANY"}
    return {"kind": "ONE", "utf8": value.decode("utf8")}
