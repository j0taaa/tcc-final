"""CARS §3 reference for a frozen product, with bulk lexical-group pruning.

The default oracle uses grammar-prefix validity and safe finite-suffix bounds.
The optional perfect oracle proves support/length feasibility by memoized DFS.
No LM calls or fake zero costs. This is not the authors' native AR decoder.
"""

from time import monotonic

from mwpc_exact.cfg_posterior import CompilationLimit

from .envelope import CounterDistribution, ExactEnvelope, OriginalChoices
from .forest import coaccessible_layers
from .lexer import OUT, finish
from .posterior import Posterior, class_weights
from .stack_control import consume


class Node:
    def __init__(self, p, state, total):
        self.p, self.state, self.total = p, state, total
        self.children, self.learned = {}, False


class Cars:
    def __init__(self, table, weights, *, perfect=False, counter=False, timeout_seconds=120):
        self.table, self.weights, self.perfect = table, weights, perfect
        self.deadline = monotonic() + timeout_seconds
        sums = class_weights(table, weights)
        self.choices = OriginalChoices(table, weights, sums)
        self.rows = [
            [sum(row[c] for c in table.local_to_class[g]) for g in range(len(table.groups))]
            for row in sums
        ]
        self.den = [1] * (len(weights.canvas) + 1)
        for p in reversed(range(len(weights.canvas))):
            self.den[p] = self.den[p + 1] * weights.denominators[p]
        self.allowed = coaccessible_layers(table, weights.canvas, deadline=self.deadline)
        self.caps = [(0, 0)] * (len(weights.canvas) + 1)
        self.caps[-1] = (1, 0)  # final NUMBER can flush; no final closing delimiter
        for p in reversed(range(len(weights.canvas))):
            words = [
                table.groups[g][2]
                for q in self.allowed[p]
                for g in table.by_state[q]
                if self.rows[p][g] and table.groups[g][1] in self.allowed[p + 1]
            ]
            terms, closes = self.caps[p + 1]
            self.caps[p] = (
                terms + max(map(len, words), default=0),
                closes + max((sum(t in (1, 3) for t in word) for word in words), default=0),
            )
        self.requirements, self.transitions, self.viable = {}, {}, {}
        self.lexical_allowed = self.allowed
        self.suffix_closes = [c[1] for c in self.caps]
        self.counter = (
            CounterDistribution(
                table, weights, sums, prepared=self, timeout_seconds=self.deadline - monotonic()
            )
            if counter
            else None
        )
        if self.counter is not None:
            self.counter.choices = self.choices
        self.root = Node(
            0, (OUT, ("V",)), self.den[0] if self.counter is None else self.counter.total
        )
        self.nodes, self.trials = 1, 0

    def guard(self):
        if monotonic() > self.deadline:
            raise CompilationLimit("CARS whole deadline; no valid sample")

    def advance(self, p, state, gid):
        if gid < 0:
            return None
        _, target, word, _ = self.table.groups[gid]
        if target not in self.allowed[p + 1]:
            return None
        key = state[1], word
        if key not in self.transitions:
            self.transitions[key] = consume(state[1], word)
        after = self.transitions[key]
        if after is None:
            return None
        if after not in self.requirements:
            self.requirements[after] = (
                sum(type(x) is int or x == "V" for x in after),
                sum(x in (1, 3) for x in after),
            )
        if any(a > b for a, b in zip(self.requirements[after], self.caps[p + 1], strict=True)):
            return None
        if p + 1 == len(self.weights.canvas):
            final = finish(target)
            if final is None or consume(after, final) != ():
                return None
        return target, after

    def feasible(self, p, state):
        """Perfect original-support feasibility; costs fully charged to CARS."""
        self.guard()
        key = p, state
        if key not in self.viable:
            if p == len(self.weights.canvas):
                final = finish(state[0])
                result = final is not None and consume(state[1], final) == ()
            else:
                result = any(
                    self.feasible(p + 1, after)
                    for g in self.table.by_state[state[0]]
                    if self.rows[p][g] and (after := self.advance(p, state, g)) is not None
                )
            self.viable[key] = result
        return self.viable[key]

    def base(self, node, gid):
        """Unvisited suffix mass in q or the exactly balanced counter proposal."""
        if self.counter is None:
            return self.den[node.p + 1]
        _, target, net, low, _ = self.counter.counter.effects[self.counter.counter.of_group[gid]]
        height = sum(t in (1, 3) for t in node.state[1])
        return 0 if height + low < 0 else self.counter.beta(node.p + 1, target, height + net)

    def propose(self, rng):
        node, word = self.root, []
        for p in range(len(self.weights.canvas)):
            self.guard()
            q = node.state[0]
            gids = self.table.by_state[q]
            masses = [
                self.rows[p][g]
                * (node.children[g].total if g in node.children else self.base(node, g))
                for g in gids
            ]
            invalid = (
                0
                if node.learned or self.counter is not None
                else self.weights.denominators[p] - sum(self.rows[p][g] for g in gids)
            )
            masses.append(invalid * self.den[p + 1])
            if sum(masses) != node.total:
                raise RuntimeError("CARS trie lost original probability mass")
            choice = Posterior.choose(masses, rng)
            if choice == len(gids):
                classes = tuple(c for c, g in enumerate(self.table.class_to_local[q]) if g < 0)
                word.append(self.choices.token(p, classes, rng))
                return tuple(word)  # future draws cannot repair this lexical prefix
            else:
                gid = gids[choice]
                word.append(self.choices.group(p, gid, rng))
                after = self.advance(p, node.state, gid)
                if after is None or (self.perfect and not self.feasible(p + 1, after)):
                    return tuple(word)  # safely abort at the first impossible prefix
                child = node.children.get(gid)
                # Unvisited prefixes keep ALL base suffix mass. Testing the
                # sampled child only aborts; it does not mask viable siblings
                # before drawing. This distinction preserves the accepted law.
                node = child if child is not None else Node(p + 1, after, self.base(node, gid))
        return tuple(word)

    def learn(self, word):
        node, path = self.root, []
        for p, token in enumerate(word):
            self.guard()
            q = node.state[0]
            path.append(node)
            for g in self.table.by_state[q]:
                if not self.rows[p][g] or g in node.children:
                    continue
                after = self.advance(p, node.state, g)
                viable = after is not None and (not self.perfect or self.feasible(p + 1, after))
                if not viable:
                    node.children[g] = Node(p + 1, after, 0)
                    self.nodes += 1
            gid = self.table.by_token[q][token]
            if gid < 0 or (gid in node.children and not node.children[gid].total):
                break
            if gid not in node.children:
                node.children[gid] = Node(
                    p + 1, self.advance(p, node.state, gid), self.base(node, gid)
                )
                self.nodes += 1
            node = node.children[gid]
        # Lexically invalid next choices are all safely excluded at each visited
        # grammar prefix. Recompute upward rather than subtract rounded masses.
        for node in reversed(path):
            node.learned = True
            node.total = sum(
                self.rows[node.p][g]
                * (node.children[g].total if g in node.children else self.base(node, g))
                for g in self.table.by_state[node.state[0]]
            )

    def valid(self, word):
        # Independent strict byte/JSON recognizer, shared with the envelope.
        return ExactEnvelope.valid(self, word)

    def sample(self, rng, *, max_trials=1_000_000):
        if type(max_trials) is not int or max_trials <= 0:
            raise ValueError("positive integer candidate budget required")
        for trial in range(1, max_trials + 1):
            if not self.root.total:
                raise ValueError("zero allowed mass; original support infeasible")
            word = self.propose(rng)
            valid = len(word) == len(self.weights.canvas) and self.valid(word)
            self.learn(word)  # published update also applies to successful draws
            self.trials += 1
            if valid:
                return word, trial
        raise CompilationLimit("CARS candidate budget; no valid sample")
