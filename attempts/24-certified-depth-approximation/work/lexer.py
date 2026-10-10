"""Independent deterministic UTF8/JSON lexical scanner, frozen origin recorded."""

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
