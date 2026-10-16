"""Exact scalar correction for original dyadic weights and actual finite tickets."""

from fractions import Fraction as F
from math import prod

from .reference import ceiling


def acceptance(weights, packet, envelope, *, valid=True):
    if not envelope > 0:
        raise ValueError("positive rational envelope required")
    if not valid or any(w == 0 for w in weights):
        return F()
    numerators, exponent = [], 0
    for weight in weights:
        n, d = float(weight).as_integer_ratio()
        if n < 0:
            raise ValueError("negative original weight")
        numerators.append(n)
        exponent += d.bit_length() - 1
    q_numerators, q_exponent = [], 0
    for a, start, end in packet:
        if not 0 <= start < end <= a <= 1 << 41:
            raise ValueError("invalid executed categorical packet")
        b = ceiling(end << 64, a) - ceiling(start << 64, a)
        if not b > 0:
            raise ValueError("zero actual proposal density")
        twos = (b & -b).bit_length() - 1
        q_numerators.append(b >> twos)
        q_exponent += 64 - twos
    num = prod(numerators) * envelope.denominator
    den = prod(q_numerators) * envelope.numerator
    if q_exponent >= exponent:
        num <<= q_exponent - exponent
    else:
        den <<= exponent - q_exponent
    result = F(num, den)
    if not 0 <= result <= 1:
        raise RuntimeError("audited envelope violated; ERROR, never clamp")
    return result
