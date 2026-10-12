"""Safe deterministic draw cap; arbitrary wall-time fallback is not provided."""


def pair(draw, classify, barrier, cap):
    for value in (barrier, cap):
        if not isinstance(value, int) or isinstance(value, bool) or value < 2:
            raise ValueError("barrier and cap must be integers >=2")
    first = draw()
    label = classify(first)
    if label not in (0, 1):
        raise ValueError("classifier must return a binary label")
    height, count, same = 1, 1, None
    while 0 < height < barrier and count < cap:
        last = draw()
        current = classify(last)
        if current not in (0, 1):
            raise ValueError("classifier must return a binary label")
        if current == label:
            height += 1
            same = last
        else:
            height -= 1
        count += 1
    if height == 0:
        return first, last, count
    assert same is not None
    return first, same, count
