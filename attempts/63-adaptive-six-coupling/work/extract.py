"""Extract a deterministic cap-six policy from its frozen rational stopping flow."""

from __future__ import annotations

import argparse
import hashlib
import json
from fractions import Fraction as F
from math import factorial
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("certificate", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    raw = args.certificate.read_bytes()
    cert = json.loads(raw)
    assert cert["cap"] == 6 and cert["certified"]
    x = {k: F(v) for k, v in cert["primal"].items()}
    states = sorted({v.split(":")[0] for v in x}, key=lambda s: (len(s), s))
    policy, stop_mass = {}, {h: F(0) for h in range(1, 7)}
    for s in states:
        reach = 1 - sum(
            (
                v
                for name, v in x.items()
                if s.startswith(name.split(":")[0]) and len(name.split(":")[0]) < len(s)
            ),
            F(0),
        )
        actions = {int(k.split(":")[1]): v for k, v in x.items() if k.split(":")[0] == s and v}
        assert reach in (0, 1), "non-deterministic reach"
        if actions:
            assert reach == 1 and len(actions) == 1 and next(iter(actions.values())) == 1
            policy[s] = next(iter(actions))
            m = len(set(s))
            stop_mass[len(s)] += F(factorial(3) // factorial(3 - m), 3 ** len(s))
    assert sum(stop_mass.values()) == 1
    expected = sum((h * p for h, p in stop_mass.items()), F(0))
    assert expected == F(386, 81)
    result = {
        "certificate_sha256": hashlib.sha256(raw).hexdigest(),
        "key_actions": policy,
        "uniform_stop_mass": {str(h): str(p) for h, p in stop_mass.items()},
        "uniform_expected_calls": str(expected),
    }
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({k: v for k, v in result.items() if k != "key_actions"}))


if __name__ == "__main__":
    main()
