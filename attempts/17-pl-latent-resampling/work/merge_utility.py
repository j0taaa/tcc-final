"""Merge unchanged seven-control evidence with the compact profile campaign.

This is a comparison between campaigns, not simultaneous paired timings.
No row, unsuccessful method or event is removed.
"""

import argparse
import hashlib
import json
from pathlib import Path


def read(folder):
    metadata = json.loads((folder / "metadata.json").read_text())
    rows = [json.loads(s) for s in (folder / "rows.jsonl").read_text().splitlines()]
    queries = [r for r in rows if r["stage"] == "query"]
    assert len(queries) == 144 * len(metadata["methods"])
    keys = [(r["case"], r["power"], r["k"], r["repetition"], r["method"]) for r in queries]
    assert len(set(keys)) == len(keys)
    return metadata, rows, dict(zip(keys, queries, strict=True))


def merge(first, second, output):
    a, rows_a, query_a = read(first)
    b, rows_b, query_b = read(second)
    assert a["batch_size"] == b["batch_size"] == 4096
    assert a["prefix_checkpoint"] == b["prefix_checkpoint"] == 1024
    assert a["source_inputs"] == b["source_inputs"]
    assert set(a["methods"]).isdisjoint(b["methods"])
    events = {}
    for row in [*query_a.values(), *query_b.values()]:
        key = row["case"], row["power"], row["k"]
        evidence = row["order"], row["observed"]
        assert key not in events or events[key] == evidence
        events[key] = evidence
    assert len(events) == 48
    preserved, prefixes = 0, 0
    labels = {
        "profiles_indexed1": "profiles",
        "profiles_indexed2": "profiles_coarse2",
        "profiles_indexed4": "profiles_coarse4",
    }
    for key, new in query_b.items():
        old = query_a[(*key[:-1], labels[key[-1]])]
        if new["status"] == old["status"] == "complete":
            assert new["paths_sha256"] == old["paths_sha256"]
            assert new["attempts"] == old["attempts"]
            assert new["histograms"] == old["histograms"]
            preserved += 1
        if "prefix_1024" in old and "prefix_1024" in new:
            for field in ("paths_sha256", "attempts", "histograms"):
                assert new["prefix_1024"][field] == old["prefix_1024"][field]
            prefixes += 1
    output.mkdir(parents=True, exist_ok=False)
    metadata = dict(
        producer={"seven_controls": a["producer"], "indexed_controls": b["producer"]},
        methods=a["methods"] + b["methods"],
        batch_size=4096,
        prefix_checkpoint=1024,
        source_inputs=a["source_inputs"],
        comparison=(
            "Same events/seeds/repetition IDs across sequential campaigns; "
            "not simultaneous paired timings"
        ),
        profile_streams_identical=dict(complete_queries=preserved, prefixes_1024=prefixes),
        sources={
            str(folder): {
                p.name: hashlib.sha256(p.read_bytes()).hexdigest()
                for p in folder.iterdir()
                if p.is_file()
            }
            for folder in (first, second)
        },
    )
    (output / "metadata.json").write_text(json.dumps(metadata, indent=2) + "\n")
    with (output / "rows.jsonl").open("x") as stream:
        for source, rows in ((a["producer"], rows_a), (b["producer"], rows_b)):
            for row in rows:
                stream.write(json.dumps(dict(row, producer=source)) + "\n")
    print(
        json.dumps(
            {
                "events": len(events),
                "methods": len(metadata["methods"]),
                "identical_streams": preserved,
                "identical_prefixes": prefixes,
            }
        )
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("first", "second", "output"):
        parser.add_argument("--" + name, type=Path, required=True)
    args = parser.parse_args()
    merge(args.first, args.second, args.output)
