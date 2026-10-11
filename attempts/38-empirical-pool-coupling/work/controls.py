"""Competent constant-size empirical controls; no model/gold imports."""

import json
from collections import Counter
from decimal import Decimal
from fractions import Fraction


def canonical(payload):
    """Gold-free typed JSON identity; raw payload IDs are never modified."""
    if payload["status"] != "COMPLETE":
        return payload["status"]

    def number(raw):
        if len(raw) > 256:
            raise ValueError("numeric literal budget")
        value = Decimal(raw)
        if abs(value.as_tuple().exponent) > 1024:
            raise ValueError("numeric exponent budget")
        return value

    def fields(pairs):
        if len({k for k, _ in pairs}) != len(pairs):
            raise ValueError("duplicate key")
        return dict(pairs)

    def invalid(_):
        raise ValueError("non-JSON numeric constant")

    def typed(node):
        if isinstance(node, Decimal):
            return "number", str(Fraction(node))
        if isinstance(node, dict):
            return "object", [(k, typed(v)) for k, v in sorted(node.items())]
        if isinstance(node, list):
            return "array", [typed(v) for v in node]
        return "literal", node

    try:
        value = json.loads(
            payload["text"],
            parse_int=number,
            parse_float=number,
            parse_constant=invalid,
            object_pairs_hook=fields,
        )
        return "JSON:" + json.dumps(typed(value), separators=(",", ":"))
    except (ValueError, TypeError, RecursionError):
        return "INVALID_JSON"


def pool(draw, key, randrange, *, early=False):
    items = [draw(), draw(), draw()]
    keys = [key(x) for x in items]
    if early and keys[1] == keys[2]:
        return items[0], items[1], 3
    items.append(draw())
    keys.append(key(items[3]))
    counts = Counter(keys)
    pattern = sorted(counts.values())
    if pattern == [2, 2]:
        indices = [i for i in range(1, 4) if keys[i] != keys[0]]
    elif pattern == [1, 1, 2]:
        target = 1 if counts[keys[0]] == 2 else 2
        indices = [i for i in range(1, 4) if counts[keys[i]] == target]
    else:
        return items[0], items[1], 4
    return items[0], items[indices[randrange(len(indices))]], 4


def novelty_three(draw, key, randrange):
    """Cheap biased search control; do not claim original second marginal."""
    first, second, third = draw(), draw(), draw()
    candidates = [x for x in (second, third) if key(x) != key(first)]
    return first, candidates[randrange(len(candidates))] if candidates else second, 3
