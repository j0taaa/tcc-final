"""Rooted best-derivation controls with identical policy/geometry/validation."""

from native_queries import NativeCountWarm, NativeLex, NativePrefix, NativeSpeculative
from rooted_parser import RootParser
from trie_lattice import TrieLattice


class RootLex(NativeLex):
    def __init__(self, state, **kwargs):
        self.root_parser = RootParser(kwargs.get("grammar") or state.grammar)
        super().__init__(state, compressed=True, **kwargs)


class RootSpeculative(NativeSpeculative):
    def __init__(self, state, **kwargs):
        self.root_parser = RootParser(kwargs.get("grammar") or state.grammar)
        super().__init__(state, compressed=True, **kwargs)


class RootPrefix(NativePrefix):
    def __init__(self, state, **kwargs):
        self.root_parser = RootParser(kwargs.get("grammar") or state.grammar)
        super().__init__(state, compressed=True, **kwargs)


class RootCountWarm(NativeCountWarm):
    def __init__(self, state, **kwargs):
        self.root_parser = RootParser(kwargs.get("grammar") or state.grammar)
        super().__init__(state, compressed=True, **kwargs)


def compile_rooted(state, grammar, **limits):
    graph, closes, _ = TrieLattice(state).query(state.canvas, ())
    return RootParser(grammar).parse(graph, state=state, closes=closes, **limits)
