"""Independent recomputation controls: witness-reusing greedy and integer lex.

Shared forest is structural only. No floating priority scores, no weighted
epsilon preprocessing, no removal of alternatives before choosing the objective.
"""

from monotone import validate_order


def witness(plan, canvas, proposals=()):
    bits = {}
    for j, (position, token, _) in enumerate(proposals):
        bits[position, token] = bits.get((position, token), 0) + (1 << (len(proposals) - j - 1))
    scores = [-1] * len(plan.terms)
    chosen = [-1] * len(plan.terms)
    for node in plan.order:
        for index, term in enumerate(plan.terms[node]):
            if term.choice is not None:
                p, i = term.choice
                token = plan.state.support.rows[p][i]
                if canvas[p] is not None and canvas[p] != token:
                    continue
                score = bits.get((p, token), 0)
            elif term.children:
                left, right = term.children
                if scores[left] < 0 or scores[right] < 0:
                    continue
                score = scores[left] + scores[right]
            else:
                score = 0
            if score > scores[node]:
                scores[node], chosen[node] = score, index
                if not proposals:
                    break
    if plan.root is None or scores[plan.root] < 0:
        return None
    output = [None] * len(canvas)
    pending = [plan.root]
    while pending:
        node = pending.pop()
        term = plan.terms[node][chosen[node]]
        if term.choice is not None:
            p, i = term.choice
            if output[p] is not None:
                raise RuntimeError("forest reused a token position")
            output[p] = plan.state.support.rows[p][i]
        pending.extend(term.children)
    if any(t is None for t in output):
        raise RuntimeError("forest omitted a token slot")
    return tuple(output)


class Recompute:
    def __init__(self, plan, *, lex=False):
        self.plan = plan
        self.canvas = list(plan.state.canvas)
        self.lex = lex
        self.calls = 0

    def solve(self, canvas, proposals=()):
        self.calls += 1
        return witness(self.plan, canvas, proposals)

    def canonical(self):
        p = self.canvas.index(None)
        current = self.solve(
            self.canvas, [(p, t, 1.0) for t in sorted(self.plan.state.support.rows[p])]
        )
        if current is None:
            raise ValueError("infeasible_on_support")
        return p, current[p]

    def transition(self, proposals, *, threshold=0.8, cap=None):
        validate_order(proposals)
        if cap is None:
            cap = len(self.canvas)
        if type(cap) is not int or cap < 1:
            raise ValueError("cap must be a positive integer")
        if self.lex:
            current = self.solve(self.canvas, proposals)
            if current is None:
                raise ValueError("infeasible_on_support")
            accepted = [(p, t, w) for p, t, w in proposals if current[p] == t]
        else:
            tentative = list(self.canvas)
            current = self.solve(tentative)
            if current is None:
                raise ValueError("infeasible_on_support")
            accepted = []
            for p, token, confidence in proposals:
                if tentative[p] is not None:
                    if tentative[p] == token:
                        accepted.append((p, token, confidence))
                    continue
                if current[p] != token:
                    trial = list(tentative)
                    trial[p] = token
                    candidate = self.solve(trial)
                    if candidate is None:
                        continue
                    current = candidate
                tentative[p] = token
                accepted.append((p, token, confidence))
        # Unique physical positions; source confidence is kept outside lex bits.
        updates = {}
        for p, token, confidence in accepted:
            if confidence >= threshold and self.canvas[p] is None and len(updates) < cap:
                updates.setdefault(p, token)
        if not updates:
            free = [(p, token) for p, token, _ in accepted if self.canvas[p] is None]
            if free:
                updates = dict(free[:1])
            else:
                # Canonical fallback specified for ALL compared methods. This
                # differs from the archived M24 arbitrary-witness fallback.
                p, token = self.canonical()
                updates[p] = token
        if not updates:
            raise RuntimeError("no progress despite feasible forest")
        for p, token in updates.items():
            self.canvas[p] = token
        return tuple(updates.items())


class CachedPrefix(Recompute):
    """Strong classical control: persist witness and stop at observable prefix."""

    def __init__(self, plan):
        super().__init__(plan)
        self.current = self.solve(self.canvas)
        if self.current is None:
            raise ValueError("infeasible_on_support")

    def try_token(self, position, token):
        if self.current[position] == token:
            return True
        trial = list(self.canvas)
        trial[position] = token
        candidate = self.solve(trial)
        if candidate is None:
            return False
        self.current = candidate
        return True

    def fix(self, position, token):
        self.canvas[position] = token

    def transition(self, proposals, *, threshold=0.8, cap=None):
        validate_order(proposals)
        cap = len(self.canvas) if cap is None else cap
        if type(cap) is not int or cap < 1:
            raise ValueError("cap must be positive")
        updates = []
        for p, token, confidence in proposals:
            if confidence < threshold or len(updates) == cap:
                break
            if self.canvas[p] is None and self.try_token(p, token):
                self.fix(p, token)
                updates.append((p, token))
        if updates:
            return tuple(updates)
        for p, token, _ in proposals:
            if self.canvas[p] is None and self.try_token(p, token):
                self.fix(p, token)
                return ((p, token),)
        p, token = self.canonical()
        self.fix(p, token)
        return ((p, token),)
