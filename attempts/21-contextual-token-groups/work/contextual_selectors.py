"""Original-token GAC and SAT over overlapping contextual groups, exact clamps."""

from mwpc_exact.backend import ExactBackend

from .context_lattice import ContextLattice
from .grammar_selectors import Recompute
from .lexer import OUT
from .lexical_selectors import LexRoot
from .monotone import Monotone, validate_order
from .native_queries import NativeQuery
from .relevant_forest import relevant_forest
from .rooted_parser import RootParser


class ContextRoot(LexRoot):
    def __init__(self, state, grammar, cache=None):
        self.root_parser = RootParser(grammar)
        NativeQuery.initialize(self, state, ExactBackend.RUST, False, grammar)
        self.compressed = True
        self.geometry = ContextLattice(state, cache)
        Recompute.__init__(self, self.plan, lex=True)

    def update_original_domains(self, state):
        if tuple(self.canvas) != state.canvas:
            raise ValueError("context reuse cannot release or change commitments")
        if not self.geometry.update(state):
            return False
        self.plan.state = state
        self.base = state.support
        return True


class ContextEngine:
    def __init__(self, state, grammar, kind, cache=None, **limits):
        self.canvas = list(state.canvas)
        self.geometry = ContextLattice(state, cache)
        virtual, graph, closes = self.geometry.virtual(grammar)
        self.plan = relevant_forest(
            RootParser(grammar).parse(graph, state=virtual, closes=closes, **limits)
        )
        self.kind = kind
        if kind == "monotone":
            self.inner = Monotone(self.plan)
        elif kind == "sat":
            from .native_sat import SatPrefix

            self.inner = SatPrefix(self.plan)
            self.selectors = {}
        else:
            raise ValueError("unknown contextual engine")

    def update_original_domains(self, state):
        if tuple(self.canvas) != state.canvas:
            raise ValueError("context reuse cannot release or change commitments")
        return self.geometry.update(state)

    def feasible(self, p, t):
        groups = self.geometry.by_token[p].get(t, ())
        return any(self.inner.feasible(p, g) for g in groups)

    def retain(self, p, groups):
        # Decremental circuit propagation is classic. A raw commitment may
        # retain MULTIPLE q-specific groups; do not fix an arbitrary group.
        from collections import deque

        inner = self.inner
        queue = deque(
            (True, tid)
            for i, g in enumerate(self.plan.state.support.rows[p])
            if g not in groups
            for tid in inner.by_choice[p, i]
        )
        while queue:
            deactivate, item = queue.popleft()
            if not deactivate:
                for tid in inner.by_node[item]:
                    inner._remove_flow(tid, queue)
                continue
            if not inner.active[item]:
                continue
            inner.active[item] = False
            inner.deactivated += 1
            inner._remove_flow(item, queue)
            node = inner.terms[item][0]
            inner.live[node] -= 1
            if not inner.live[node]:
                queue.extend((True, tid) for tid in inner.by_child[node])
        if not inner.live[self.plan.root]:
            raise RuntimeError("supported original commitment removed all completions")

    def selector(self, p, t):
        # Tseitin OR for raw-token membership. Aliases sharing memberships
        # reuse the selector; its definition stays constant under safe growth.
        groups = tuple(sorted(self.geometry.by_token[p].get(t, ())))
        key = (p, groups)
        if key not in self.selectors:
            variable = self.inner.solver.nof_vars() + 1
            inputs = [self.inner.variables[p, g] for g in groups]
            self.inner.solver.add_clause([-variable, *inputs])
            for x in inputs:
                self.inner.solver.add_clause([-x, variable])
            self.selectors[key] = variable
        return self.selectors[key]

    def try_token(self, p, t):
        groups = self.geometry.by_token[p].get(t, ())
        if self.inner.current[p] in groups:
            return True
        self.inner.calls += 1
        if not self.inner.solver.solve(assumptions=[self.selector(p, t)]):
            return False
        model = {v for v in self.inner.solver.get_model() if v > 0}
        self.inner.current = tuple(
            next(g for g in row if self.inner.variables[i, g] in model)
            for i, row in enumerate(self.plan.state.support.rows)
        )
        return True

    @property
    def current(self):
        if self.kind != "sat":
            return None
        return tuple(
            self.canvas[p]
            if self.canvas[p] is not None
            else min(self.geometry.groups[g]["members"].intersection(self.geometry.active_rows[p]))
            for p, g in enumerate(self.inner.current)
        )

    @current.setter
    def current(self, word):
        if self.kind != "sat":
            return
        q, groups = OUT, []
        for p, t in enumerate(word):
            target, output = self.geometry.cache.get(t, q)
            gid = self.geometry.by_key[p, q, target, output]
            groups.append(gid)
            q = target
        self.inner.current = tuple(groups)

    def fix(self, p, t):
        groups = self.geometry.by_token[p].get(t, ())
        if self.kind == "monotone":
            if not self.feasible(p, t):
                raise ValueError("incompatible original commitment")
            self.retain(p, groups)
        else:
            self.inner.solver.add_clause([self.selector(p, t)])
        self.canvas[p] = t

    def transition(self, proposals, *, threshold=0.8, cap=None):
        validate_order(proposals)
        if len({p for p, _, _ in proposals}) != len(proposals):
            raise NotImplementedError("contextual facade requires one proposal per position")
        cap = len(self.canvas) if cap is None else cap
        if type(cap) is not int or cap < 1:
            raise ValueError("cap must be positive")
        viable = self.feasible if self.kind == "monotone" else self.try_token
        updates = []
        for p, t, w in proposals:
            if w < threshold or len(updates) == cap:
                break
            if self.canvas[p] is None and viable(p, t):
                self.fix(p, t)
                updates.append((p, t))
        if updates:
            return tuple(updates)
        for p, t, _ in proposals:
            if self.canvas[p] is None and viable(p, t):
                self.fix(p, t)
                return ((p, t),)
        p = self.canvas.index(None)
        for t in sorted(self.geometry.active_rows[p]):
            if viable(p, t):
                self.fix(p, t)
                return ((p, t),)
        raise ValueError("infeasible_on_support")

    def close(self):
        if self.kind == "sat":
            self.inner.close()
