"""Small independent current-suite oracle; historical tests remain archived."""

import importlib.util
import sys
from pathlib import Path

WORK = Path(__file__).resolve().parents[1] / "attempts/18-monotone-grammatical-decoding/work"
sys.path.insert(0, str(WORK))
try:
    spec = importlib.util.spec_from_file_location(
        "monotone_correctness", WORK / "test_correctness.py"
    )
    if spec is None or spec.loader is None:
        raise ImportError("cannot locate isolated monotone oracle")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    Correctness = module.Correctness
finally:
    sys.path.pop(0)
