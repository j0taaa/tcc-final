#!/usr/bin/env python3
"""Check all query attempts offline and generate their non-benchmark inventory."""

import argparse
import json
from collections import Counter
from pathlib import Path

from verify_query_demo import verify

ROOT = Path(__file__).resolve().parents[2]
OUTPUT = ROOT / "docs/research/generated"


def build():
    records = []
    for version in (1, 2):
        base = ROOT / "docs/artifacts/demo"
        paths = [base / f"geocoding_v{version}"]
        paths += sorted((base / f"geocoding_comparators_v{version}").iterdir())
        assert len(paths) == 4
        for path in paths:
            checked = verify(path)
            record = json.loads((path / "record.json").read_text())
            checked.update(
                {
                    "phase": version,
                    "record_directory": path.relative_to(ROOT).as_posix(),
                    "request": record["request"],
                    "generated_call": record["generation"]["output"],
                    "model_forwards": record["generation"]["forwards"],
                    "support_policy": record["config"].get("grounding_policy", "question_spans_v1"),
                    "catalog_size": len(record["support"]["catalog"]),
                    "api_url": (record.get("api") or {}).get("url"),
                    "api_response_sha256": (record.get("api") or {}).get("response_sha256"),
                    "fetched_at_utc": (record.get("api") or {}).get("fetched_at_utc"),
                }
            )
            records.append(checked)
    result = {
        "records": records,
        "phases": {
            str(v): dict(Counter(r["status"] for r in records if r["phase"] == v)) for v in (1, 2)
        },
        "scope": "One fixed geographic request; v2 is post-hoc application diagnosis. "
        "All eight attempts are retained. This is not a benchmark accuracy estimate, "
        "paired performance comparison, or evidence of decoder superiority.",
    }
    lines = [
        "# Consulta real e diagnóstico de suporte",
        "",
        result["scope"],
        "",
        "| Fase | Política | Estado API | Forwards | Certificados conferidos | Chamada |",
        "|---|---|---|---:|---:|---|",
    ]
    for r in records:
        lines.append(
            f"| {r['phase']} | {r['method']} | {r['status']} | {r['model_forwards']} | "
            f"{r['checked_certificates']} | `{r['generated_call'].strip()}` |"
        )
    lines += ["", "Fontes, hashes, datas e suporte declarado ficam no JSON associado.", ""]
    return {
        "m25-query-demo-summary.json": json.dumps(result, indent=2) + "\n",
        "m25-query-demo-results.md": "\n".join(lines),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    for name, value in build().items():
        path = OUTPUT / name
        if args.check:
            assert path.read_text() == value, path
        else:
            path.write_text(value)
    print("All eight query records independently verified")


if __name__ == "__main__":
    main()
