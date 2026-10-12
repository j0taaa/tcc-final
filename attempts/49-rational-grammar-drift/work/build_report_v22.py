"""Derive the complete 24-row consolidated table from immutable V21 evidence."""

import argparse
import hashlib
import json
from fractions import Fraction as F
from pathlib import Path


def run(output):
    root = Path(__file__).parent
    origin = json.loads((root / "evidence/origin-v21.json").read_text())
    folder = root / "evidence/public-v21"
    for name, expected in origin["records"][0]["files"].items():
        assert hashlib.sha256((folder / name).read_bytes()).hexdigest() == expected
    metadata = json.loads((folder / "metadata.json").read_text())
    assert metadata["producer"] == origin["producer"]
    rows = [json.loads(line) for line in (folder / "rows.jsonl").read_text().splitlines()]
    names = {
        "adaptive_angular": "Angular",
        "calibrated_endpoint": "Endpoint",
        "hybrid_endpoint": "Hybrid",
        "ordered_planar": "Ordered",
    }
    expected = {
        (kind, epsilon, name)
        for kind in ["binary32", "binary16", "bfloat16"]
        for epsilon in ["1/2", "1/10"]
        for name in names
    }
    assert len(rows) == 24
    assert {(r["format"], r["epsilon"], r["engine"].rsplit(".", 1)[-1]) for r in rows} == expected
    tex = [
        r"\begin{tabular}{lllrrrrr}",
        r"\toprule",
        r"Format & $\varepsilon$ & Core & $L$ & $U$ & Cheap $U$ & Core W/C & Full W/C \\",
        r"\midrule",
    ]
    markdown = [
        "# All24 functional V21 results (generated)",
        "",
        "One reused public packet; wall/CPU seconds. No independent speed gate/new forwards.",
        "All input, preparation, exact normalizers, rounding and strong scalar controls charged.",
        "",
        "| Format | epsilon | Engine | L | U | Best cheap U | Core wall/CPU | Full wall/CPU |",
        "| --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for row in rows:
        assert row["status"] == "CERTIFIED_ON_ADMITTED_FOREST"
        lower, upper = F(row["lower"]), F(row["upper"])
        cheap = min(
            F(row["controls"]["mass_aware"]["upper"]),
            F(row["controls"]["hellinger_upper"]),
            F(row["controls"]["range_upper"]),
        )
        assert 0 <= lower <= upper <= min(1, (1 + F(row["epsilon"])) * lower)
        assert lower <= cheap
        assert len(row["costs_wall_cpu"]) == 6
        assert all(
            abs(row["full_first_audit_wall_cpu"][i] - sum(c[i] for c in row["costs_wall_cpu"].values()))
            < 1e-9
            for i in [0, 1]
        )
        kind = dict(binary32="FP32", binary16="FP16", bfloat16="BF16")[row["format"]]
        name = names[row["engine"].rsplit(".", 1)[-1]]
        core = "/".join(f"{x:.3f}" for x in row["costs_wall_cpu"]["core"])
        full = "/".join(f"{x:.3f}" for x in row["full_first_audit_wall_cpu"])
        tex.append(
            f"{kind} & ${row['epsilon']}$ & {name} & {float(lower):.2e} & {float(upper):.2e} & "
            f"{float(cheap):.2e} & {core} & {full} " + r"\\"
        )
        markdown.append(
            f"| {kind} | {row['epsilon']} | {name} | {float(lower):.12e} | {float(upper):.12e} | "
            f"{float(cheap):.12e} | {core} | {full} |"
        )
    tex.extend([r"\bottomrule", r"\end{tabular}"])
    fp16 = next(
        r
        for r in rows
        if (r["format"], r["epsilon"], r["engine"].rsplit(".", 1)[-1])
        == ("binary16", "1/10", "ordered_planar")
    )
    best_fp16 = min(
        F(fp16["controls"]["mass_aware"]["upper"]),
        F(fp16["controls"]["hellinger_upper"]),
        F(fp16["controls"]["range_upper"]),
    )
    factor = best_fp16 / F(fp16["upper"])

    def sci(value):
        mantissa, exponent = f"{float(F(value)):.5e}".split("e")
        return f"{mantissa}\\times10^{{{int(exponent)}}}"

    values = [
        f"\\newcommand{{\\FPsixteenUpper}}{{{sci(fp16['upper'])}}}",
        f"\\newcommand{{\\CheapUpper}}{{{sci(best_fp16)}}}",
        f"\\newcommand{{\\CheapFactor}}{{{float(factor):.2f}}}",
        f"\\newcommand{{\\OriginalWordCount}}{{{fp16['valid_original_assignments']:,}}}",
        f"\\newcommand{{\\FPsixteenZeros}}{{{fp16['zeroed_original_entries']:,}}}",
        f"\\newcommand{{\\AuditProducer}}{{{origin['producer'][:7]}}}",
    ]
    output.mkdir(parents=True, exist_ok=False)
    (output / "audit-table.tex").write_text("\n".join(tex) + "\n")
    (output / "audit-values.tex").write_text("\n".join(values) + "\n")
    (output / "audit.md").write_text("\n".join(markdown) + "\n")
    (output / "provenance.json").write_text(json.dumps(origin, indent=2) + "\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    run(parser.parse_args().output)
