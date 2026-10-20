"""Correct the fixed-support caller error in frozen audit.py at 8ab90057.

The original producer and its failure record remain immutable. Same cases,
weights, pins, seeds, oracle, sampler and gates; only the API input is repaired.
"""

from unittest.mock import patch

import audit

original_builder = audit.build_per_position_support


def compatible_support(*, canvas, policy, explicit_support):
    corrected = {
        k: (fixed,) if fixed is not None else explicit_support[k] for k, fixed in enumerate(canvas)
    }
    return original_builder(canvas=canvas, policy=policy, explicit_support=corrected)


if __name__ == "__main__":
    with patch.object(audit, "build_per_position_support", compatible_support):
        audit.main()
