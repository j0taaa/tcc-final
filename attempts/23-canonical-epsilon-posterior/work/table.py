"""Shared complete vocabulary lexer table; deterministic original-token mapping."""

from array import array

from .lexer import STATES, scan


class LexerTable:
    def __init__(self, adapter):
        self.adapter = adapter
        self.groups, self.by_state, self.by_token = [], {}, {}
        for q in STATES:
            effects, members = {}, []
            mapping = array("i", [-1]) * adapter.vocabulary_size
            for token, word in enumerate(adapter.emissions):
                effect = None if word is None else scan(word, q)
                if effect is None:
                    continue
                gid = effects.get(effect)
                if gid is None:
                    gid = len(self.groups) + len(members)
                    effects[effect] = gid
                    members.append([])
                mapping[token] = gid
                members[gid - len(self.groups)].append(token)
            offset = len(self.groups)
            self.groups.extend(
                (q, *effect, tuple(members[gid - offset])) for effect, gid in effects.items()
            )
            self.by_state[q] = tuple(range(offset, len(self.groups)))
            self.by_token[q] = mapping
        signatures, classes = {}, []
        self.class_of = array("i", [-1]) * adapter.vocabulary_size
        for token in range(adapter.vocabulary_size):
            signature = tuple(self.by_token[q][token] for q in STATES)
            cid = signatures.get(signature)
            if cid is None:
                cid = len(classes)
                signatures[signature] = cid
                classes.append([])
            classes[cid].append(token)
            self.class_of[token] = cid
        self.classes = tuple(map(tuple, classes))
        self.class_to_local = {
            q: tuple(self.by_token[q][members[0]] for members in self.classes) for q in STATES
        }
        self.local_to_class = [[] for _ in self.groups]
        for q in STATES:
            for cid, gid in enumerate(self.class_to_local[q]):
                if gid >= 0:
                    self.local_to_class[gid].append(cid)
