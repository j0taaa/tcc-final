"""Deterministic RFC8259 UTF8 scanner: all states, no known mask context."""

from mwpc_exact.reference.byte_grammars import _SourceGrammarBuilder
from mwpc_exact.reference.normalization import normalize_to_cnf

OUT, STR, ESC = 0, 1, 2
U1, U2, U3, U4 = 3, 4, 5, 6
C1, C2, C3, E0, ED, F0, F4 = 7, 8, 9, 10, 11, 12, 13
MINUS, ZERO, INT, DOT, FRAC, EX, SIGN, EXP = range(14, 22)
PUNCT = {b: i for i, b in enumerate(b"{}[]:,")}
STRING, NUMBER, TRUE, FALSE, NULL, MARK, END = range(6, 13)
KEYWORDS = (b"true", b"false", b"null")
PREFIXES = tuple(w[:i] for w in KEYWORDS for i in range(1, len(w)))
KSTATES = {p: 22 + i for i, p in enumerate(PREFIXES)}
KREVERSE = {v: k for k, v in KSTATES.items()}
STATES = tuple(range(22 + len(PREFIXES)))
NUM_FINAL = (ZERO, INT, FRAC, EXP)


def step(q, b):
    if q == OUT:
        if b in PUNCT:
            return OUT, (PUNCT[b],)
        if b in b" \t\r\n":
            return OUT, ()
        if b == 34:
            return STR, ()
        if b == 45:
            return MINUS, ()
        if b == 48:
            return ZERO, ()
        if 49 <= b <= 57:
            return INT, ()
        if bytes([b]) in KSTATES:
            return KSTATES[bytes([b])], ()
        return None
    if q == STR:
        if b == 34:
            return OUT, (STRING,)
        if b == 92:
            return ESC, ()
        if 32 <= b < 128:
            return STR, ()
        if 194 <= b < 224:
            return C1, ()
        if 224 <= b < 240:
            return (E0 if b == 224 else ED if b == 237 else C2), ()
        if 240 <= b <= 244:
            return (F0 if b == 240 else F4 if b == 244 else C3), ()
        return None
    if q == ESC:
        if b in b'"\\/bfnrt':
            return STR, ()
        return (U4, ()) if b == 117 else None
    if q in (U1, U2, U3, U4):
        return ((STR if q == U1 else q - 1), ()) if b in b"0123456789abcdefABCDEF" else None
    if q in (C1, C2, C3, E0, ED, F0, F4):
        low, high, target = {
            C1: (128, 191, STR),
            C2: (128, 191, C1),
            C3: (128, 191, C2),
            E0: (160, 191, C1),
            ED: (128, 159, C1),
            F0: (144, 191, C2),
            F4: (128, 143, C2),
        }[q]
        return (target, ()) if low <= b <= high else None
    if q in KREVERSE:
        prefix = KREVERSE[q] + bytes([b])
        if prefix in KEYWORDS:
            # Primitive values have identical syntactic continuations. Keeping
            # their original IDs in lexical fibers preserves values and weights.
            return OUT, (NUMBER,)
        return (KSTATES[prefix], ()) if prefix in KSTATES else None
    if q == MINUS:
        return (ZERO if b == 48 else INT, ()) if 48 <= b <= 57 else None
    if q in (ZERO, INT):
        if 48 <= b <= 57:
            return (INT, ()) if q == INT else None
        if b == 46:
            return DOT, ()
        if b in b"eE":
            return EX, ()
    elif q == DOT:
        return (FRAC, ()) if 48 <= b <= 57 else None
    elif q == FRAC:
        if 48 <= b <= 57:
            return FRAC, ()
        if b in b"eE":
            return EX, ()
    elif q == EX:
        if b in b"+-":
            return SIGN, ()
        return (EXP, ()) if 48 <= b <= 57 else None
    elif q == SIGN:
        return (EXP, ()) if 48 <= b <= 57 else None
    elif q == EXP and 48 <= b <= 57:
        return EXP, ()
    if q in NUM_FINAL:
        rest = step(OUT, b)
        return None if rest is None else (rest[0], (NUMBER, *rest[1]))
    return None


def scan(word, state=OUT):
    output = []
    for byte in word:
        result = step(state, byte)
        if result is None:
            return None
        state, emitted = result
        output.extend(emitted)
    return state, tuple(output)


def finish(q):
    if q == OUT:
        return ()
    return (NUMBER,) if q in NUM_FINAL else None


class Partition:
    """Lazy per-request signatures; cached classification costs remain measured."""

    def __init__(self, adapter):
        self.original = adapter
        self.by_token, self.by_signature, self.representatives = {}, {}, []

    def classify(self, token):
        if token not in self.by_token:
            word = self.original.emissions[token]
            signature = tuple(None if word is None else scan(word, q) for q in STATES)
            cid = self.by_signature.get(signature)
            if cid is None:
                cid = len(self.representatives)
                self.by_signature[signature] = cid
                self.representatives.append(token)
            self.by_token[token] = cid
        return self.by_token[token]


def ClassAdapter(partition):
    from mwpc_exact.tokenizer_bytes import CompositionalByteLevelAdapter

    return CompositionalByteLevelAdapter(
        tuple(partition.original.emissions[t] for t in partition.representatives)
    )


def lexical_grammar():
    names = ("S", "V", "A", "Items", "MoreItems", "O", "Members", "MoreMembers", "Skip")
    b = _SourceGrammarBuilder(names, start="S")

    # Each grammar terminal is preceded by exactly one Skip occurrence;
    # remaining MARKs belong to final Skip. No arbitrary boundary insertions.
    def rule(head, *body):
        lifted = []
        for x in body:
            if isinstance(x, int):
                lifted.extend(("Skip", bytes([x])))
            else:
                lifted.append(x)
        b.rule(head, *lifted)

    rule("S", "V", END)
    for nonterminal in ("A", "O"):
        rule("V", nonterminal)
    for terminal in (STRING, NUMBER):
        rule("V", terminal)
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
    b.rule("Skip")
    b.rule("Skip", bytes([MARK]), "Skip")
    return normalize_to_cnf(b.build()).grammar
