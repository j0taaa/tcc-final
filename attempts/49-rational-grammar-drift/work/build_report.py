"""Derive every numerical table from all six immutable public-audit rows."""

import argparse
import hashlib
import json
from fractions import Fraction as F
from pathlib import Path


def run(output):
    folder = Path(__file__).parent / "evidence" / "public-v9"
    origin = json.loads((folder / "origin.json").read_text())
    for name, expected in origin["sha256"].items():
        assert hashlib.sha256((folder / name).read_bytes()).hexdigest() == expected
    rows = [json.loads(line) for line in (folder / "rows.jsonl").read_text().splitlines()]
    assert {(r["format"], r["epsilon"]) for r in rows} == {
        (name, epsilon)
        for name in ["binary32", "binary16", "bfloat16"]
        for epsilon in ["1/2", "1/10"]
    }
    assert len(rows) == 6 and all(r["status"] == "CERTIFIED_ON_ADMITTED_FOREST" for r in rows)
    output.mkdir(parents=True, exist_ok=False)
    tex = [
        r"\begin{tabular}{llrrrr}",
        r"\toprule",
        r"Format & $\varepsilon$ & $L$ & $U$ & Hellinger upper & Core (s) \\",
        r"\midrule",
    ]
    markdown = [
        "# Complete numerical drift audit (generated)",
        "",
        "All6 predefined cases; same original50,258 IDs and frozen public head.",
        "Not a benchmark, neural quantization experiment or independent corpus.",
        "",
        "| Format | epsilon | L | U | Hellinger upper | Range upper | Core seconds | "
        "Full first audit seconds |",
        "| --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for row in rows:
        lower, upper = F(row["lower"]), F(row["upper"])
        assert 0 <= lower <= upper <= min(1, (1 + F(row["epsilon"])) * lower)
        name = dict(binary32="FP32", binary16="FP16", bfloat16="BF16")[row["format"]]
        h, ratio = F(row["controls"]["hellinger_upper"]), F(row["controls"]["range_upper"])
        tex.append(
            f"{name} & ${row['epsilon']}$ & {float(lower):.3e} & {float(upper):.3e} & "
            f"{float(h):.3e} & {row['core_seconds']:.3f} " + r"\\"
        )
        markdown.append(
            f"| {name} | {row['epsilon']} | {float(lower):.9e} | {float(upper):.9e} | "
            f"{float(h):.9e} | {float(ratio):.9e} | {row['core_seconds']:.6f} | "
            f"{row['full_first_audit_seconds']:.6f} |"
        )
    tex.extend([r"\bottomrule", r"\end{tabular}"])
    fp16 = next(r for r in rows if r["format"] == "binary16" and r["epsilon"] == "1/10")
    factor = F(fp16["controls"]["hellinger_upper"]) / F(fp16["upper"])
    mantissa, exponent = f"{float(F(fp16['upper'])):.5e}".split("e")
    values = [
        f"\\newcommand{{\\FPsixteenUpper}}{{{mantissa}\\times10^{{{int(exponent)}}}}}",
        f"\\newcommand{{\\HellingerFactor}}{{{float(factor):.2f}}}",
        f"\\newcommand{{\\OriginalWordCount}}{{{fp16['valid_original_assignments']:,}}}",
        f"\\newcommand{{\\FPsixteenZeros}}{{{fp16['zeroed_original_entries']:,}}}",
    ]
    (output / "audit-table.tex").write_text("\n".join(tex) + "\n")
    (output / "audit-values.tex").write_text("\n".join(values) + "\n")
    (output / "audit.md").write_text("\n".join(markdown) + "\n")
    (output / "provenance.json").write_text(json.dumps(origin, indent=2) + "\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    run(parser.parse_args().output)
