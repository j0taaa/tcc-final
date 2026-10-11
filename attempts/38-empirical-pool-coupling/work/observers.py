"""Sound consumer observations; preserve complete original payloads and failures."""

from .controls import canonical
from .native_task import evaluate


def fine(payload):
    """Typed JSON identity with the interpreter's identical raw-text budget."""
    if len(payload["text"]) > 65536:
        return "OBSERVER_TEXT_BUDGET"
    return canonical(payload)


def semantic(payload):
    """Gold-free exact execution value; failure is an outcome, never resampled."""
    if payload["status"] != "COMPLETE":
        return "FAIL"
    try:
        return "VALUE:" + str(evaluate(payload["text"]))
    except (ValueError, ZeroDivisionError, RecursionError, OverflowError):
        return "FAIL"
