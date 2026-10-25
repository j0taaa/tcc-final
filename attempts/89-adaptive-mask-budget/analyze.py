"""Read every frozen record; paired units are items, never timing repetitions."""
import argparse
import csv
import json
import statistics as st
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np


def read(path):
    return [json.loads(line) for line in path.read_text().splitlines()]


def select(val):
    result = {}
    for family in ("flat", "grouped"):
        choices = []
        for cap in (32,64,96):
            rows = [r for r in val if r.get("type")=="decode" and
                    r["family"]==family and r["mode"]=="fixed_cpu" and r["initial_capacity"]==cap]
            assert len(rows)==4, (family,cap,len(rows))
            choices.append(dict(capacity=cap,correct=sum(r["correct"] for r in rows),
                                median_seconds=st.median(r["seconds"] for r in rows)))
        winner=min(choices,key=lambda x:(-x["correct"],x["median_seconds"],x["capacity"]))
        result[family]={**winner,"candidates":choices}
    return result


def bootstrap(values):
    values=np.array(values,dtype=float)
    rng=np.random.default_rng(89001)
    draws=rng.choice(values,(10000,len(values)),replace=True)
    return np.quantile(np.median(draws,axis=1),[.025,.975]).tolist()


def analyze(val, test):
    rows=[r for r in test if r.get("type")=="decode"]
    assert len(rows)==336, len(rows)
    groups=defaultdict(list)
    for r in rows:
        groups[r["family"],r["steps"],r["mode"]].append(r)
    summary=[]
    for (family,steps,mode),rr in sorted(groups.items()):
        items=defaultdict(list)
        for r in rr:
            items[r["case"]].append(r)
        assert len(items)==4 and all(len(v)==3 for v in items.values())
        medians=[st.median(r["seconds"] for r in v) for v in items.values()]
        summary.append(dict(family=family,steps=steps,mode=mode,
            correct_runs=sum(r["correct"] for r in rr),valid_runs=sum(r["valid"] for r in rr),
            runs=len(rr),correct_unique=sum(all(r["correct"] for r in v) for v in items.values()),
            valid_unique=sum(all(r["valid"] for r in v) for v in items.values()),
            median_seconds=st.median(medians),median_ci95=bootstrap(medians),
            median_forwards=st.median(r["forwards"] for r in rr),
            median_capacity=st.median(r["final_capacity"] for r in rr),
            median_effective_tokens=st.median(r["effective_tokens"] for r in rr),
            median_input_tokens_sum=st.median(r["input_tokens_sum"] for r in rr),
            total_expansions=sum(len(r["expansions"]) for r in rr),
            total_inserted=sum(r["inserted"] for r in rr),
            max_allocated=max(r["peak_allocated"] for r in rr),
            max_reserved=max(r["peak_reserved"] for r in rr),
            statuses=dict(Counter(r["status"] for r in rr))))
    indexed={(r["case"],r["steps"],r["rep"],r["mode"]):r for r in rows}
    equivalence=[]
    for policy in ("fixed","adaptive"):
        mismatches=[]
        pairs=0
        for key,a in indexed.items():
            if key[-1]!=policy+"_cpu":
                continue
            b=indexed[(*key[:-1],policy+"_gpu")]
            differences=[k for k in ("ids","trace","events","expansions","status") if a[k]!=b[k]]
            if differences:
                mismatches.append(dict(case=key[0],steps=key[1],rep=key[2],fields=differences))
            pairs+=1
        equivalence.append(dict(policy=policy,pairs=pairs,mismatches=mismatches))
    comparisons=[]
    controls=("fixed_cpu","reserve_cpu","simple_cpu","epic")
    for family in ("flat","grouped"):
        for steps in (8,16):
            subset=[r for r in summary if r["family"]==family and r["steps"]==steps]
            # Reporting the best measured control is conservative for the proposal.
            best=min((r for r in subset if r["mode"] in controls),
                     key=lambda r:(-r["correct_unique"],r["median_seconds"],r["mode"]))
            for candidate in ("adaptive_cpu","adaptive_gpu"):
                cr=[r for r in rows if r["family"]==family and r["steps"]==steps and r["mode"]==candidate]
                bycase=defaultdict(list)
                losses,gains=[],[]
                for r in cr:
                    bycase[r["case"]].append(r)
                ratios=[]
                for case,rs in bycase.items():
                    bs=[indexed[case,steps,r["rep"],best["mode"]] for r in rs]
                    ratios.append(st.median(r["seconds"]/b["seconds"] for r,b in zip(rs,bs,strict=True)))
                    cgood=all(r["correct"] for r in rs)
                    bgood=all(r["correct"] for r in bs)
                    if cgood and not bgood:gains.append(case)
                    if bgood and not cgood:losses.append(case)
                valid=all(r["valid"] for r in cr)
                ratio=st.median(ratios)
                gate=valid and not losses and ratio<=.9
                alt=valid and len(gains)-len(losses)>=2 and ratio<=1.1
                comparisons.append(dict(family=family,steps=steps,candidate=candidate,
                    best_control=best["mode"],paired_median_ratio=ratio,ci95=bootstrap(ratios),
                    gains=gains,losses=losses,gate_speed=gate,gate_quality=alt))
    cpu_val=[r for r in val if r.get("type")=="decode" and r["mode"]=="adaptive_cpu"]
    def verifier_time(r):
        return sum(v for k,v in r["times"].items() if k in ("allocate","verify_update","verify_query"))
    fractions=[verifier_time(r)/r["seconds"] for r in cpu_val]
    return dict(selection=select(val),summary=summary,equivalence=equivalence,
        comparisons=comparisons,custom_kernel_gate=dict(threshold=.1,
            median_cpu_validation_verifier_fraction=st.median(fractions),
            passed=st.median(fractions)>=.1),
        totals=dict(runs=len(rows),forwards=sum(r["forwards"] for r in rows),
            decode_seconds=sum(r["seconds"] for r in rows),correct=sum(r["correct"] for r in rows),
            valid=sum(r["valid"] for r in rows),max_rss_bytes=max(r["rss_peak_bytes"] for r in rows)),
        overhead=[r for r in test if r.get("type")!="decode"])


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--val",type=Path,required=True)
    p.add_argument("--test",type=Path)
    p.add_argument("--selection",type=Path)
    p.add_argument("--output",type=Path)
    args=p.parse_args()
    val=read(args.val)
    if args.selection:
        if args.selection.exists():raise SystemExit("Refusing overwrite")
        result=select(val)
        args.selection.write_text(json.dumps(result,indent=2))
    elif args.test and args.output:
        if args.output.exists():raise SystemExit("Refusing overwrite")
        result=analyze(val,read(args.test))
        args.output.write_text(json.dumps(result,indent=2))
        with args.output.with_suffix(".csv").open("w") as stream:
            fields=[k for k in result["summary"][0] if k not in ("median_ci95","statuses")]
            writer=csv.DictWriter(stream,fieldnames=fields,extrasaction="ignore")
            writer.writeheader()
            writer.writerows(result["summary"])
    else:
        raise SystemExit("Provide --selection or --test with --output")
    print(json.dumps(result,indent=2))


if __name__=="__main__":main()
