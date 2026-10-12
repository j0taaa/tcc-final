"""Three-class original-source pair; fixed budget, no class mass information."""


def pair(draw, classify, budget, rng):
    if isinstance(budget, bool) or not isinstance(budget, int) or budget < 2:
        raise ValueError("budget must be an integer >=2")

    def label(z):
        i = classify(z)
        if isinstance(i, bool) or not isinstance(i, int) or i not in (0, 1, 2):
            raise ValueError("classifier must return an integer in {0,1,2}")
        return i

    first = draw()
    anchor = label(first)
    counts, others, representatives = [0, 0, 0], [0, 0, 0], [None, None, None]
    counts[anchor] = 1
    for _ in range(1, budget):
        z = draw()
        i = label(z)
        counts[i] += 1
        others[i] += 1
        if rng.randrange(others[i]) == 0:
            representatives[i] = z
    diagonal = [max(0, 2 * n - budget) for n in counts]
    ticket = rng.randrange(2 * counts[anchor])
    for j in range(3):
        if j == anchor:
            weight = 2 * diagonal[j]
        else:
            k = 3 - anchor - j
            weight = counts[anchor] + counts[j] - counts[k]
            weight += diagonal[k] - diagonal[anchor] - diagonal[j]
        if ticket < weight:
            return first, representatives[j]
        ticket -= weight
    raise RuntimeError("invalid empirical coupling row")
