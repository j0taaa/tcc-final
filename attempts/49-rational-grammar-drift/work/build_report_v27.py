"""Generate every ordered 0.1 pair from BOTH complete immutable campaigns."""

import argparse
import hashlib
import json
from pathlib import Path


def run(output):
    root = Path(__file__).parent
    sources, decisions = {}, {}
    for version in [25, 26]:
        origin = json.loads((root / f"evidence/origin-external-v{version}.json").read_text())
        for name, expected in origin["files"].items():
            assert hashlib.sha256((root / name).read_bytes()).hexdigest() == expected
        path = root / f"external-decision-v{version}.json"
        assert hashlib.sha256(path.read_bytes()).hexdigest() == origin["decision_sha256"]
        decisions[version] = json.loads(path.read_text())
        sources[version] = origin
    assert decisions[25]["passed_primary_pairs"] == 0
    assert decisions[26]["independent_confirmation"] is False
    protocol = json.loads((root / "protocol-v25.json").read_text())
    table = [
        r"\begin{tabular}{lrrrrrrr}",
        r"\toprule",
        r"Document / masks & & \multicolumn{2}{c}{FP32} & \multicolumn{2}{c}{FP16}"
        r" & \multicolumn{2}{c}{BF16} \\",
        r" & & V25 & V26 & V25 & V26 & V25 & V26 \\",
        r"\midrule",
    ]
    for case in protocol["source_corpus"]["cases"]:
        label = case["file"].removeprefix("y_").removesuffix(".json").replace("_", r"\_")
        for masks in protocol["mask_counts"]:
            cells = []
            for kind in protocol["formats"]:
                for version in [25, 26]:
                    row = next(
                        r
                        for r in decisions[version]["all45pairs"]
                        if (r["case"], r["mask_count"], r["format"]) == (case["key"], masks, kind)
                    )
                    ratio = row.get("cheap_to_candidate_ratio")
                    cells.append(f"{ratio:.5f}" if isinstance(ratio, float) else "ref.")
            table.append(f"{label} & {masks} & " + " & ".join(cells) + r" \\")
        table.append(r"\addlinespace")
    table.extend([r"\bottomrule", r"\end{tabular}"])
    values = [
        f"\\newcommand{{\\IndependentPassed}}{{{decisions[25]['passed_primary_pairs']}}}",
        f"\\newcommand{{\\DevelopmentPassed}}{{{decisions[26]['passed_development_pairs']}}}",
    ]
    summary = json.loads((root / "evidence/external-v25/summary.json").read_text())
    independent_ratios = [
        r["cheap_to_candidate_ratio"]
        for r in decisions[25]["all45pairs"]
        if r["primary_unseen"] and "cheap_to_candidate_ratio" in r
    ]
    development_ratios = [
        r["cheap_to_candidate_ratio"]
        for r in decisions[26]["all45pairs"]
        if "cheap_to_candidate_ratio" in r
    ]
    numbers = dict(
        ExternalRows=summary["rows"],
        ExternalCertificates=summary["counts"]["CERTIFIED_ON_ADMITTED_FOREST"],
        ExternalRefusals=summary["counts"]["RESOURCE_REFUSAL"],
        IndependentPairs=decisions[25]["primary_pairs"],
        DevelopmentPairs=decisions[26]["development_pairs"],
        ClosestIndependentRatio=f"{max(independent_ratios):.5f}",
        BestDevelopmentRatio=f"{max(development_ratios):.5f}",
        ExternalWall=f"{summary['wall_cpu'][0]:,.3f}",
        RootOracleCases=json.loads((root / "evidence/root-oracle-v26/summary.json").read_text())[
            "cases"
        ],
        LowerOracleCases=json.loads((root / "evidence/two-sided-v27/summary.json").read_text())[
            "original_id_forest_cases"
        ],
        LowerUndefined=json.loads((root / "evidence/two-sided-v27/summary.json").read_text())[
            "undefined_zero_mass"
        ],
        FamilyCases=json.loads((root / "evidence/scalar-gap-v27/summary.json").read_text())[
            "cases"
        ],
        MaintainedTests=json.loads((root / "evidence/checks-v27.json").read_text())["tests"],
    )
    values.extend(f"\\newcommand{{\\{name}}}{{{value}}}" for name, value in numbers.items())
    output.mkdir(parents=True, exist_ok=False)
    (output / "audit-table.tex").write_text("\n".join(table) + "\n")
    (output / "audit-values.tex").write_text("\n".join(values) + "\n")
    (output / "provenance.json").write_text(json.dumps(sources, indent=2) + "\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    run(parser.parse_args().output)
