"""Frozen descriptive corpus FIT audit; not model/decoder evaluation."""

import argparse
import hashlib
import json
import resource
import subprocess
import time
from collections import Counter
from decimal import Decimal
from pathlib import Path

PIN = "9a94995b9279ae3af3aed4b2629172790b968d14"
BOUND_KEYS = ("minimum", "maximum", "exclusiveMinimum", "exclusiveMaximum")
COMPLEX = ("$ref", "$dynamicRef", "allOf", "anyOf", "oneOf", "not", "if", "then", "else")


class RawNumber(str):
    pass


def number(raw):
    if not isinstance(raw, RawNumber):
        return None
    value = Decimal(raw)
    if not value.is_finite():
        raise ValueError("nonfinite numeric lexeme")
    return value


def bounds(schema):
    lows, highs = [], []
    for plain, exclusive, target in (
        ("minimum", "exclusiveMinimum", lows),
        ("maximum", "exclusiveMaximum", highs),
    ):
        value = number(schema.get(plain))
        if value is not None:
            target.append((value, schema.get(exclusive) is True, str(schema[plain])))
        value = number(schema.get(exclusive))
        if value is not None:
            target.append((value, True, str(schema[exclusive])))
    low = max(lows, key=lambda x: (x[0], x[1])) if lows else None
    high = min(highs, key=lambda x: (x[0], not x[1])) if highs else None
    return low, high


def schema_nodes(schema):
    if not isinstance(schema, dict):
        return
    yield schema
    for key in (
        "properties",
        "patternProperties",
        "definitions",
        "$defs",
        "dependentSchemas",
        "dependencies",
    ):
        for child in schema.get(key, {}).values() if isinstance(schema.get(key), dict) else ():
            yield from schema_nodes(child)
    for key in (
        "items",
        "additionalItems",
        "additionalProperties",
        "propertyNames",
        "contains",
        "not",
        "if",
        "then",
        "else",
        "unevaluatedItems",
        "unevaluatedProperties",
        "allOf",
        "anyOf",
        "oneOf",
        "prefixItems",
    ):
        child = schema.get(key)
        for item in child if isinstance(child, list) else [child]:
            yield from schema_nodes(item)


def aligned(schema, instance, counts, pointer=""):
    if not isinstance(schema, dict):
        return
    if any(key in schema for key in COMPLEX):
        counts["skipped_ref_or_combinator_nodes"] += 1
        return
    if isinstance(instance, RawNumber) and any(key in schema for key in BOUND_KEYS):
        yield pointer, schema, instance
    if isinstance(instance, dict):
        props = schema.get("properties", {})
        if isinstance(props, dict):
            for key, child in instance.items():
                if key in props:
                    segment = key.replace("~", "~0").replace("/", "~1")
                    yield from aligned(props[key], child, counts, pointer + "/" + segment)
    if isinstance(instance, list):
        prefix = schema.get("prefixItems", [])
        items = schema.get("items")
        for i, child in enumerate(instance):
            if isinstance(prefix, list) and i < len(prefix):
                sub = prefix[i]
            elif isinstance(items, list):
                sub = items[i] if i < len(items) else None
            else:
                sub = items
            yield from aligned(sub, child, counts, pointer + "/" + str(i))


def main(source, output):
    assert (
        subprocess.check_output(["git", "-C", str(source), "rev-parse", "HEAD"], text=True).strip()
        == PIN
    )
    assert not subprocess.check_output(
        ["git", "-C", str(source), "status", "--porcelain"], text=True
    ).strip()
    tree = subprocess.check_output(
        ["git", "-C", str(source), "ls-tree", "-rz", "HEAD", "--", "maskbench/data"], text=True
    )
    files = []
    for item in tree.split("\0"):
        if item:
            metadata, path = item.split("\t", 1)
            if path.endswith(".json"):
                files.append((path, metadata.split()[2]))
    assert len(files) == 11306
    output.mkdir(parents=True, exist_ok=False)
    counts, by_source, errors = Counter(), {}, []
    begin = time.monotonic()
    with (
        (output / "manifest.jsonl").open("w") as manifest,
        (output / "observations.jsonl").open("w") as observations,
    ):
        for path, oid in files:
            if (
                time.monotonic() - begin > 600
                or resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * 1024 > 1024**3
            ):
                raise RuntimeError("declared600s/1GiB resource cap")
            data = (source / path).read_bytes()
            blob = b"blob " + str(len(data)).encode() + b"\0" + data
            assert hashlib.sha1(blob).hexdigest() == oid
            manifest.write(
                json.dumps(
                    {
                        "path": path,
                        "git_oid": oid,
                        "bytes": len(data),
                        "sha256": hashlib.sha256(data).hexdigest(),
                    }
                )
                + "\n"
            )
            counts["files"] += 1
            counts["source_bytes"] += len(data)
            group = Path(path).stem.split("---", 1)[0]
            per = by_source.setdefault(group, Counter())
            per["files"] += 1
            try:
                packet = json.loads(data, parse_int=RawNumber, parse_float=RawNumber)
                schema = packet["schema"]
                bounded = sum(
                    any(key in node for key in BOUND_KEYS) for node in schema_nodes(schema)
                )
                counts["bounded_schema_nodes"] += bounded
                per["bounded_schema_nodes"] += bounded
                for index, test in enumerate(packet.get("tests", [])):
                    label = test.get("valid")
                    counts["test_instances"] += 1
                    per["test_instances"] += 1
                    for pointer, node, raw in aligned(schema, test.get("data"), counts):
                        low, high = bounds(node)
                        if low is None and high is None:
                            counts["numeric_fields_without_effective_interval"] += 1
                            continue
                        value = number(raw)
                        scientific = "e" in raw.lower()
                        mantissa = raw.lower().split("e", 1)[0]
                        long_fraction = "." in mantissa and len(mantissa.split(".", 1)[1]) > 6
                        valid_local = (
                            low is None or value > low[0] or (value == low[0] and not low[1])
                        ) and (
                            high is None or value < high[0] or (value == high[0] and not high[1])
                        )
                        record = {
                            "file": path,
                            "test": index,
                            "pointer": pointer,
                            "label": label,
                            "raw": str(raw),
                            "type": node.get("type"),
                            "low": None if low is None else [low[2], low[1]],
                            "high": None if high is None else [high[2], high[1]],
                            "scientific": scientific,
                            "fraction_gt6": long_fraction,
                            "valid_local_interval": valid_local,
                        }
                        observations.write(json.dumps(record, ensure_ascii=False) + "\n")
                        tags = ["bounded_numeric_fields"]
                        if scientific:
                            tags.append("scientific_fields")
                        if long_fraction:
                            tags.append("fraction_gt6_fields")
                        if low is not None and high is not None and low[0] > 0:
                            tags.append("positive_finite_intervals")
                        if low is not None and high is not None and high[0] < 0:
                            tags.append("negative_finite_intervals")
                        if low is None or high is None:
                            tags.append("open_intervals")
                        if (low is None or low[0] < 0 or (low[0] == 0 and not low[1])) and (
                            high is None or high[0] > 0 or (high[0] == 0 and not high[1])
                        ):
                            tags.append("intervals_admitting_zero")
                        field_type = node.get("type")
                        tags.append(
                            f"{field_type}_type_fields"
                            if field_type in ("number", "integer")
                            else "other_or_unspecified_type_fields"
                        )
                        if label is True:
                            tags.append("labeled_valid_fields")
                            if scientific:
                                tags.append("labeled_valid_scientific_fields")
                            if long_fraction:
                                tags.append("labeled_valid_fraction_gt6_fields")
                            if not valid_local:
                                tags.append("local_interval_violations_in_labeled_valid")
                        for tag in tags:
                            counts[tag] += 1
                            per[tag] += 1
            except Exception as exc:
                errors.append({"file": path, "exception": type(exc).__name__, "message": str(exc)})
    assert counts["source_bytes"] == 143978678
    report = {
        "status": "COMPLETE" if not errors else "COMPLETE_WITH_ERRORS",
        "producer": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
        "source_commit": PIN,
        "scope": (
            "descriptive conformance-corpus FIT ONLY; direct properties/items; "
            "no ref/combinator resolution"
        ),
        "counts": dict(counts),
        "by_source": {k: dict(v) for k, v in by_source.items()},
        "errors": errors,
        "new_model_forwards": 0,
        "competitive_timing": False,
        "positive_campaign_gate": False,
    }
    (output / "summary.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({k: v for k, v in report.items() if k != "by_source"}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    main(args.source, args.output)
