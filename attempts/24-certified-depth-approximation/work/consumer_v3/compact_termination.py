"""Direct EOT/PAD lexical adapter for immutable compact CFG control sources.

The prior written proof specifies the isolated end-predicate hook. Compiler,
inside/outside and provenance-sampling sources remain byte-for-byte unchanged.
"""

import importlib
import sys
import types
from array import array

from mwpc_exact.reference.byte_grammars import _SourceGrammarBuilder
from mwpc_exact.reference.normalization import normalize_to_cnf

from ..frozen_control import materialize
from ..lexer import END, MARK, NUMBER, PUNCT, STRING, finish

DONE, EOT_TERMINAL = 1000, 13


def end_of_terminated_canvas(state):
    return () if state == DONE else None


def lexical_table(surrogate, eot, pad):
    """Share the SAME refined global classes and exact summaries as candidates."""
    groups, by_state = [], {}
    by_token = {
        q: array("i", [-1]) * surrogate.adapter.vocabulary_size for q in (*surrogate.by_state, DONE)
    }

    def add(q, target, word, members):
        if not members:
            return
        gid = len(groups)
        groups.append((q, target, word, tuple(members)))
        by_state.setdefault(q, []).append(gid)
        for token in members:
            by_token[q][token] = gid

    for q in surrogate.by_state:
        for gid in surrogate.by_state[q]:
            _, target, word, members = surrogate.groups[gid]
            add(q, target, word, [t for t in members if t not in (eot, pad)])
        tail = finish(q)
        if tail is not None:
            add(q, DONE, (*tail, EOT_TERMINAL), (eot,))
    add(DONE, DONE, (EOT_TERMINAL,), (pad,))
    class_to_local = {
        q: tuple(by_token[q][members[0]] for members in surrogate.classes) for q in by_token
    }
    local_to_class = [[] for _ in groups]
    for q in by_token:
        for cid, gid in enumerate(class_to_local[q]):
            if gid >= 0:
                # Check WHOLE classes, preserving original aliases and zeros.
                if any(by_token[q][t] != gid for t in surrogate.classes[cid]):
                    raise ValueError("termination lexer splits the declared global partition")
                local_to_class[gid].append(cid)
    return types.SimpleNamespace(
        adapter=surrogate.adapter,
        classes=surrogate.classes,
        class_of=surrogate.class_of,
        groups=groups,
        by_state={q: tuple(by_state.get(q, ())) for q in by_token},
        by_token=by_token,
        class_to_local=class_to_local,
        local_to_class=local_to_class,
    )


def grammar(*, marked):
    names = ("S", "V", "A", "Items", "MoreItems", "O", "Members", "MoreMembers", "Skip", "Pads")
    builder = _SourceGrammarBuilder(names, start="S")

    def rule(head, *body):
        lifted = []
        for symbol in body:
            if isinstance(symbol, int):
                if marked:
                    lifted.append("Skip")
                lifted.append(bytes([symbol]))
            else:
                lifted.append(symbol)
        builder.rule(head, *lifted)

    rule("S", "V", EOT_TERMINAL, "Pads", END)
    rule("Pads")
    rule("Pads", EOT_TERMINAL, "Pads")
    rule("V", "A")
    rule("V", "O")
    rule("V", STRING)
    rule("V", NUMBER)
    rule("A", PUNCT[91], "Items", PUNCT[93])
    rule("Items")
    rule("Items", "V", "MoreItems")
    rule("MoreItems")
    rule("MoreItems", PUNCT[44], "V", "MoreItems")
    rule("O", PUNCT[123], "Members", PUNCT[125])
    rule("Members")
    rule("Members", STRING, PUNCT[58], "V", "MoreMembers")
    rule("MoreMembers")
    rule("MoreMembers", PUNCT[44], STRING, PUNCT[58], "V", "MoreMembers")
    if marked:
        builder.rule("Skip")
        builder.rule("Skip", bytes([MARK]), "Skip")
    return normalize_to_cnf(builder.build()).grammar


def load():
    target, source, archive_hash = materialize()
    name = "_a24_terminated_compact_frozen"
    if name not in sys.modules:
        package = types.ModuleType(name)
        package.__path__ = [str(target / "attempts/23-canonical-epsilon-posterior/work")]
        sys.modules[name] = package
    modules = {
        key: importlib.import_module(name + "." + key) for key in ("forest", "epsilon", "posterior")
    }
    # Isolated lexical interface hook; original file contents stay unchanged.
    modules["forest"].finish = end_of_terminated_canvas
    modules["grammars"] = {True: grammar(marked=True), False: grammar(marked=False)}
    return modules, dict(
        source_commit=source,
        source_archive_sha256=archive_hash,
        lexical_hook="isolated forest.finish: epsilon iff DONE; new EOT/PAD table and grammar",
    )


class CompactCache:
    def __init__(self, table, canvas, method, *, modules=None, **limits):
        modules = load()[0] if modules is None else modules
        if method not in ("exact_local", "exact_bidir_local", "exact_eps_local"):
            raise ValueError("unknown direct terminated CFG control")
        epsilon = method == "exact_eps_local"
        factory = modules["epsilon"].EpsilonPrepared if epsilon else modules["forest"].Prepared
        kind = "bidir_local" if method == "exact_bidir_local" else "local"
        self.prepared = factory(table, canvas, modules["grammars"][not epsilon], kind, **limits)
        self.posterior_type = modules["posterior"].Posterior
        self.class_of = tuple(table.class_of)

    def reweight(self, weights):
        if weights.stats.partition.class_of != self.class_of:
            raise ValueError("compact cache changed original global partition")
        return self.posterior_type(self.prepared, weights)
