"""Competent native SAT control, classical Tseitin encoding plus one-hot tokens.

Research-only dependency python-sat==1.9.dev15 (MIT); Cadical195 backend.
Shares only the structural forest. SAT returns original token assignments.
"""

from itertools import combinations

from grammar_selectors import CachedPrefix
from pysat.solvers import Solver


class SatPrefix(CachedPrefix):
    def __init__(self, plan):
        self.plan, self.canvas = plan, list(plan.state.canvas)
        self.calls = 0
        self.variables = {}
        next_id = len(plan.terms) + 1
        clauses = []
        for p, row in enumerate(plan.state.support.rows):
            choices = []
            for token in row:
                self.variables[p, token] = next_id
                choices.append(next_id)
                next_id += 1
            clauses.append(choices)
            clauses.extend([-a, -b] for a, b in combinations(choices, 2))
            if self.canvas[p] is not None:
                clauses.append([self.variables[p, self.canvas[p]]])
        for node, terms in enumerate(plan.terms):
            alternatives = []
            for term in terms:
                term_id = next_id
                next_id += 1
                alternatives.append(term_id)
                if term.choice is not None:
                    p, i = term.choice
                    inputs = [self.variables[p, plan.state.support.rows[p][i]]]
                else:
                    inputs = [child + 1 for child in term.children]
                clauses.extend([-term_id, x] for x in inputs)
                clauses.append([term_id, *(-x for x in inputs)])
                clauses.append([-term_id, node + 1])
            clauses.append([-(node + 1), *alternatives])
        if plan.root is None:
            raise ValueError("infeasible_on_support")
        clauses.append([plan.root + 1])
        self.solver = Solver(name="cadical195", bootstrap_with=clauses)
        self.current = self.solve(self.canvas)
        if self.current is None:
            self.solver.delete()
            raise ValueError("infeasible_on_support")

    def solve(self, canvas, proposals=(), prefix=None):
        self.calls += 1
        assumptions = []
        for p, token in enumerate(canvas):
            if token is not None:
                variable = self.variables.get((p, token))
                if variable is None:
                    return None
                assumptions.append(variable)
        if prefix is not None:
            p, limit = prefix
            assumptions += [
                -self.variables[p, t] for t in self.plan.state.support.rows[p] if t > limit
            ]
        if not self.solver.solve(assumptions=assumptions):
            return None
        model = {lit for lit in self.solver.get_model() if lit > 0}
        return tuple(
            next(t for t in row if self.variables[p, t] in model)
            for p, row in enumerate(self.plan.state.support.rows)
        )

    def fix(self, position, token):
        self.canvas[position] = token
        self.solver.add_clause([self.variables[position, token]])

    def canonical(self):
        p = self.canvas.index(None)
        row = self.plan.state.support.rows[p]
        lo, hi = 0, row.index(self.current[p])
        while lo < hi:
            mid = (lo + hi) // 2
            current = self.solve(self.canvas, prefix=(p, row[mid]))
            if current is None:
                lo = mid + 1
            else:
                self.current = current
                hi = row.index(current[p])
        return p, row[lo]

    def close(self):
        self.solver.delete()
