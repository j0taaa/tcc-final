"""Recreate the predeclared inputs from the pinned public source, without a model."""
import argparse
import hashlib
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--output",type=Path,required=True)
    args=p.parse_args()
    if args.output.exists():raise SystemExit("Refusing overwrite")
    raw=(HERE/"evidence/bbh-word-sorting.json").read_bytes()
    assert hashlib.sha256(raw).hexdigest()=="2a6132d2c99f00d0d2eb1113ac6b4a918bd969d863c48749210d969713db8d43"
    data=json.loads(raw)["examples"]
    order=sorted(range(len(data)),key=lambda i:hashlib.sha256(f"A89-v1:{i}".encode()).hexdigest())
    cases=[]
    for j,i in enumerate(order[:6]):
        words=data[i]["input"].split("List:")[-1].split()
        assert sorted(words)==data[i]["target"].split()
        for family in ("flat","grouped"):
            expected=sorted(words)
            if family=="grouped":
                expected=[[w for w in sorted(words) if w[0]==c] for c in sorted(set(w[0] for w in words))]
            instruction=("Return a compact JSON array of the words sorted alphabetically." if family=="flat" else
                "Return a compact JSON array of arrays. Group the words by first letter; sort groups by that letter and words alphabetically inside each group. Do not include the group letters separately.")
            cases.append(dict(id=f"{family}-{i}",index=i,split="VAL" if j<2 else "TEST",
                family=family,words=words,prompt=instruction+
                " Use no spaces, code fences, explanations, or extra keys. Include every input word exactly once.\nWords: "+" ".join(words),expected=expected))
    args.output.write_text(json.dumps(cases,indent=2))
    assert args.output.read_bytes()==(HERE/"evidence/inputs.json").read_bytes()
    print("Inputs reproduce byte for byte")


if __name__=="__main__":main()
