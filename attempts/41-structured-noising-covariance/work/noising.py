"""Evaluate only two retained original states; cheap keys never call the model."""

from .kernel import pair
from .source import Source


def evaluate_pair(size, prepare, key, randrange, evaluate):
    source = Source(size, prepare, randrange)
    first, second, queries = pair(source, key, randrange)
    return evaluate(first), evaluate(second), queries
