"""CPU-only independent audit of incremental updates and joint dependencies."""
import argparse
import itertools
import json
from pathlib import Path

import numpy as np

from verifier import Verifier, compile_library

HERE=Path(__file__).resolve().parent


def brute(table,canvas):
    holes=[i for i,c in enumerate(canvas) if c<0]
    for values in itertools.product(range(len(table)),repeat=len(holes)):
        seq=list(canvas)
        for i,c in zip(holes,values,strict=True):seq[i]=c
        q=0
        for c in seq:
            q=int(table[c,q])
            if q<0:break
        if q==table.shape[1]-1:return True
    return False


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--output",type=Path,required=True)
    args=p.parse_args()
    if args.output.exists():raise SystemExit("Refusing overwrite")
    lib,_=compile_library(HERE/"../../.cache/a89")
    rng=np.random.default_rng(89002)
    checks,updates=0,0
    for _ in range(80):
        table=rng.integers(-1,5,size=(4,5),dtype=np.int32)
        engine=Verifier(table,lib)
        cold=Verifier(table,lib)
        canvas=[-1]*5
        expected=brute(table,canvas)
        assert engine.prepare(canvas)==expected
        if not expected:continue
        for pos in rng.permutation(5).tolist():
            valid=[]
            for c in range(4):
                trial=list(canvas);trial[pos]=c
                allowed=brute(table,trial)
                assert engine.allows(pos,c)==allowed
                checks+=1
                if allowed:valid.append(c)
            assert valid
            canvas[pos]=int(rng.choice(valid))
            assert engine.prepare(canvas,pos)
            assert cold.prepare(canvas)
            assert np.array_equal(engine.f,cold.f)
            assert np.array_equal(engine.b,cold.b)
            updates+=1
    # L={ab,cd}; independent marginal membership does not imply joint feasibility.
    table=np.array([[1,-1,-1,-1],[-1,3,-1,-1],
                    [2,-1,-1,-1],[-1,-1,3,-1]],dtype=np.int32)
    e=Verifier(table,lib)
    assert e.prepare([-1,-1])
    assert e.allows(0,0) and e.allows(1,3)
    assert e.prepare([0,-1],0)
    assert not e.allows(1,3)
    assert e.allows(1,1)
    result=dict(status="PASS",oracle_proposals=checks,incremental_updates=updates,
                joint_dependency_counterexample=True,cuda_used=False)
    args.output.write_text(json.dumps(result,indent=2))
    print(json.dumps(result))


if __name__=="__main__":main()
