"""The pinned LLaDA initial-mask transfer schedule, independent of tensors."""


def transfer_schedule(slot_count: int, steps: int) -> tuple[int, ...]:
    """Match upstream quotient/remainder allocation for a single full block.

    Freeze once from the initial masks. Do not reset the budget to the canvas
    length or recompute it from the number of masks after a selector rejects.
    """
    if any(isinstance(value, bool) or not isinstance(value, int) for value in (slot_count, steps)):
        raise TypeError("slot_count and steps must be integers")
    if slot_count < 1 or not 1 <= steps <= slot_count:
        raise ValueError("require 1 <= steps <= slot_count")
    quotient, remainder = divmod(slot_count, steps)
    return tuple(quotient + (index < remainder) for index in range(steps))
