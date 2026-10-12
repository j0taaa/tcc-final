"""Original-source pair; no deadlines, neural calls or probability inputs."""


def pair(draw, classify, barrier):
    if not isinstance(barrier, int) or isinstance(barrier, bool) or barrier < 2:
        raise ValueError("barrier must be an integer >=2")
    first = draw()
    label = classify(first)
    if label not in (0, 1):
        raise ValueError("classifier must return a binary label")
    height, count = 1, 1
    while 0 < height < barrier:
        last = draw()
        current = classify(last)
        if current not in (0, 1):
            raise ValueError("classifier must return a binary label")
        height += 1 if current == label else -1
        count += 1
    return first, last, count
