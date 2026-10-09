"""Model-independent domain union and stronger prepared SAT reservoir controls."""


def union_rows(rows, canvas, new_top):
    """Only enlarge free domains; no output witness or target supplies choices."""
    return tuple(
        (fixed,) if fixed is not None else tuple(sorted(set(row).union(new_top[p])))
        for p, (row, fixed) in enumerate(zip(rows, canvas, strict=True))
    )
