"""Classify an actually newly accepted original token, never a raw proposal."""


def number_checkpoint(previous, current, decode, *, start, mask_id, special_ids):
    """First new number-bearing slot in canvas order, then first ASCII digit."""
    if len(previous) != len(current) or not 0 <= start <= len(current):
        raise ValueError("incompatible checkpoint canvases")
    for position in range(start, len(current)):
        token = current[position]
        if previous[position] != mask_id or token == mask_id or token in special_ids:
            continue
        emission = decode(token)
        digit = next((char for char in emission if char in "0123456789"), None)
        if digit is not None:
            return dict(position=position, token_id=token, emission=emission, digit=int(digit))
    return None
