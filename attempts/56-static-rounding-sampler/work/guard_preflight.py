"""Complete the original invalid-support/zero-mass numerical preflight scope."""

import argparse
import hashlib
import json
from pathlib import Path
from random import Random

import torch

from .frozen_control.interval_sampler import IntervalSampler
from .static_frontend import StaticDAG


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    output = parser.parse_args().output
    output.mkdir(parents=True, exist_ok=False)
    refusals = []
    for name, classes, layers in (
        ("duplicate_original_id", ((0, 0),), ((((0, (0,)),),),)),
        ("overlapping_arcs", ((0,),), ((((0, (0,)), (0, (0,))),),)),
        ("invalid_target", ((0,),), ((((1, (0,)),),),)),
    ):
        try:
            StaticDAG(classes, layers, (True,))
        except ValueError:
            refusals.append(name)
        else:
            raise AssertionError(name)
    classes, layers = ((0,),), ((((0, (0,)),),),)
    engine = StaticDAG(classes, layers, (True,))
    engine.capture_ptx = True
    for name, value in (("negative", -1.0), ("nan", float("nan")), ("above_one", 2.0)):
        try:
            engine.query(torch.full((1, 1), value, dtype=torch.float64, device="cuda"))
        except ValueError:
            refusals.append(name)
        else:
            raise AssertionError(name)
    try:
        engine.query(torch.ones((1, 1), dtype=torch.float32, device="cuda"))
    except ValueError:
        refusals.append("wrong_dtype")
    else:
        raise AssertionError("wrong_dtype")
    zero = torch.zeros((1, 1), dtype=torch.float64, device="cuda")
    result = engine.query(zero)
    assert result["lower"] == result["upper"] == 0
    sampler = IntervalSampler(classes, layers, (True,))
    sampler.engine = engine
    try:
        sampler.sample(zero, torch.zeros((1, 1, 3), dtype=torch.int64, device="cuda"), [Random(56)])
    except ValueError as error:
        assert "zero exact target mass" in str(error)
        refusals.append("zero_mass_no_word")
    else:
        raise AssertionError("no word can be returned from zero target mass")
    ptx = dict(engine.ptx)
    # Capture arithmetic specializations also used by the previous finite-law audit.
    classes, layers = ((0, 1), (2, 3)), ((((0, (0,)), (0, (1,))),), (((0, (0, 1)),),))
    engine = StaticDAG(classes, layers, (True,))
    engine.capture_ptx = True
    result = engine.query(torch.full((2, 4), 0.5, dtype=torch.float64, device="cuda"))
    assert result["lower"] <= 4 <= result["upper"]
    ptx.update(engine.ptx)
    folder = output / "ptx"
    folder.mkdir()
    for digest, content in ptx.items():
        assert ".ftz" not in content
        (folder / (digest + ".ptx")).write_text(content)
    payload = dict(
        status="PASS",
        refusals=refusals,
        zero_mass_exact_checks=1,
        additional_ptx_modules=len(ptx),
        new_model_forwards=0,
        timing_claim=False,
        source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        scope="original protocol boundary supplement; previous records unchanged",
    )
    (output / "summary.json").write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    print(json.dumps(payload, sort_keys=True))


if __name__ == "__main__":
    main()
