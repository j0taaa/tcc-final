"""Original-token lexer controls and class facade; never send class IDs to NN."""

from dataclasses import replace

from mwpc_exact.backend import ExactBackend
from mwpc_exact.support import SupportPolicy, build_per_position_support
from mwpc_exact.types import SupportKind

from .grammar_selectors import CachedPrefix, Recompute
from .lex_lattice import LexLattice
from .lexer import ClassAdapter, Partition
from .monotone import Monotone, validate_order
from .native_queries import NativeQuery
from .relevant_forest import relevant_forest
from .rooted_parser import RootParser
from .rooted_selectors import RootLex, RootPrefix, RootSpeculative


def compile_lexical(state, grammar, **limits):
    graph, closes, _ = LexLattice(state).query(state.canvas, ())
    return relevant_forest(RootParser(grammar).parse(graph, state=state, closes=closes, **limits))


class LexRoot(RootLex):
    def __init__(self, state, *, grammar):
        self.root_parser = RootParser(grammar)
        NativeQuery.initialize(self, state, ExactBackend.RUST, False, grammar)
        self.compressed = True
        self.geometry = LexLattice(state)
        Recompute.__init__(self, self.plan, lex=True)


class LexSpeculative(RootSpeculative):
    def __init__(self, state, *, grammar):
        self.root_parser = RootParser(grammar)
        NativeQuery.initialize(self, state, ExactBackend.RUST, False, grammar)
        self.compressed = True
        self.geometry = LexLattice(state)
        Recompute.__init__(self, self.plan, lex=True)


class LexPrefix(RootPrefix):
    def __init__(self, state, *, grammar):
        # Avoid constructing a byte trie or initial byte query unnecessarily.
        super().__init__(state, grammar=grammar, lazy=True)
        self.geometry = LexLattice(state)


class ClassEngine:
    """All-state quotient, with monotonic commits and same-class expansions.

    One proposal per free position is an explicit research facade limitation.
    Strong class-level SAT and rooted controls share exactly the same grouping.
    """

    def __init__(self, state, grammar, kind, partition=None, reserve_rows=None, **limits):
        self.partition = partition or Partition(state.tokenizer_adapter)
        self.canvas = list(state.canvas)
        self.kind = kind
        self.state = state
        self.groups = self.group(state.support.rows)
        basis = self.groups if reserve_rows is None else self.group(reserve_rows)
        rows = tuple(tuple(sorted(g)) for g in basis)
        canvas = tuple(None if t is None else self.partition.classify(t) for t in self.canvas)
        support = build_per_position_support(
            canvas=canvas,
            policy=SupportPolicy(
                kind=SupportKind.EXPLICIT,
                vocabulary_size=len(self.partition.representatives),
                pruning_description="internal lexical class image of declared original support",
            ),
            explicit_support=dict(enumerate(rows)),
        )
        internal = replace(
            state,
            grammar=grammar,
            canvas=canvas,
            support=support,
            tokenizer_adapter=ClassAdapter(self.partition),
            proposals=(),
        )
        self.internal_state = internal
        if kind in ("root", "speculative"):
            self.inner = (LexRoot if kind == "root" else LexSpeculative)(internal, grammar=grammar)
        else:
            plan = compile_lexical(internal, grammar, **limits)
            if kind == "monotone":
                self.inner = Monotone(plan)
            elif kind == "sat":
                from .reservoir_sat import ReserveSat

                self.inner = ReserveSat(plan, tuple(tuple(g) for g in self.groups))
            elif kind == "prefix":
                self.inner = CachedPrefix(plan)
            else:
                raise ValueError("unknown class engine")
        self.update_rank()

    def group(self, rows):
        groups = []
        for row in rows:
            g = {}
            for token in row:
                g.setdefault(self.partition.classify(token), []).append(token)
            groups.append({c: tuple(sorted(tokens)) for c, tokens in g.items()})
        return tuple(groups)

    def update_rank(self):
        if hasattr(self.inner, "geometry"):
            self.inner.geometry.rank_rows = tuple(
                tuple(sorted(g, key=lambda c: g[c][0])) for g in self.groups
            )
            self.inner.minimum_position = None

    def update_original_domains(self, state):
        groups = self.group(state.support.rows)
        if any(
            not set(g).issubset(self.internal_state.support.rows[p]) for p, g in enumerate(groups)
        ):
            return False
        self.groups, self.state = groups, state
        if hasattr(self.inner, "update_domains"):
            self.inner.update_domains(tuple(tuple(g) for g in groups))
        self.update_rank()
        return True

    @property
    def current(self):
        word = getattr(self.inner, "current", None)
        if word is None:
            return None
        return tuple(self.groups[p][c][0] for p, c in enumerate(word))

    @current.setter
    def current(self, word):
        if hasattr(self.inner, "current"):
            self.inner.current = tuple(self.partition.classify(t) for t in word)

    def fix(self, p, token):
        c = self.partition.classify(token)
        if c not in self.groups[p] or token not in self.groups[p][c]:
            raise ValueError("original commitment outside active support")
        if hasattr(self.inner, "commit"):
            self.inner.commit(p, c)
        elif hasattr(self.inner, "fix"):
            self.inner.fix(p, c)
        else:
            self.inner.canvas[p] = c
        self.canvas[p] = token

    def transition(self, proposals, *, threshold=0.8, cap=None):
        validate_order(proposals)
        if len({p for p, _, _ in proposals}) != len(proposals):
            raise NotImplementedError("class facade requires one proposal per position")
        cap = len(self.canvas) if cap is None else cap
        if type(cap) is not int or cap < 1:
            raise ValueError("cap must be positive")
        if self.kind in ("root", "speculative"):
            mapped = [(p, self.partition.classify(t), w) for p, t, w in proposals]
            choices = self.inner.transition(mapped, threshold=threshold, cap=cap)
            proposed = {p: t for p, t, _ in proposals}
            updates = []
            for p, c in choices:
                token = proposed.get(p)
                if token is None or self.partition.classify(token) != c:
                    token = self.groups[p][c][0]
                self.canvas[p] = token
                updates.append((p, token))
            return tuple(updates)
        # Original-ID order for canonical fallback, including raw aliases that
        # occur after a smaller-ID token in another class. Never min(class ID).
        feasible = self.inner.feasible if self.kind == "monotone" else self.inner.try_token
        updates = []
        for p, t, confidence in proposals:
            if confidence < threshold or len(updates) == cap:
                break
            if self.canvas[p] is None and feasible(p, self.partition.classify(t)):
                self.fix(p, t)
                updates.append((p, t))
        if updates:
            return tuple(updates)
        for p, t, _ in proposals:
            if self.canvas[p] is None and feasible(p, self.partition.classify(t)):
                self.fix(p, t)
                return ((p, t),)
        p = self.canvas.index(None)
        for c in sorted(self.groups[p], key=lambda c: self.groups[p][c][0]):
            if feasible(p, c):
                t = self.groups[p][c][0]
                self.fix(p, t)
                return ((p, t),)
        raise ValueError("infeasible_on_support")

    def close(self):
        if hasattr(self.inner, "close"):
            self.inner.close()
