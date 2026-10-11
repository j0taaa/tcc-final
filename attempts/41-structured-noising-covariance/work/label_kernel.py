"""Same four-pool law with separate raw draws and opaque label queries."""


def pair_labels(draw, key, randrange):
    first, second = draw(), draw()
    a, b = key(first), key(second)
    if a == b:
        return first, draw(), 3
    third = draw()
    c = key(third)
    if c == a:
        return first, draw(), 4
    if c == b:
        return first, second, 3
    fourth = draw()
    d = key(fourth)
    if d == a:
        return first, (second, third)[randrange(2)], 4
    if d == b or d == c:
        return first, fourth, 4
    return first, (second, third, fourth)[randrange(3)], 4
