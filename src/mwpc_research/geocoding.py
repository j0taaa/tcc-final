"""Validated dispatch for one read-only geocoding tool; never evaluate model code."""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from mwpc_research.grounded_calls import grounded_catalog, scalar_call_arguments
from mwpc_research.schema_calls import normalize_schema_call

FUNCTION: dict[str, Any] = {
    "name": "get_location",
    "description": "Search for geographic coordinates by city or place name. Read only.",
    "parameters": {
        "type": "dict",
        "properties": {
            "name": {"type": "string", "description": "City or place named in the request."}
        },
        "required": ["name"],
    },
}
ENDPOINT = "https://geocoding-api.open-meteo.com/v1/search"
ATTRIBUTION = "Open-Meteo Geocoding API; location data by GeoNames (https://www.geonames.org/)"


def validated_url(call: str, question: str) -> str:
    arguments = scalar_call_arguments(call, FUNCTION)
    if arguments is None or normalize_schema_call(call) not in grounded_catalog(FUNCTION, question):
        raise ValueError("Call fails the schema or question-derived support validation")
    name = arguments["name"]
    if not 2 <= len(name) <= 100 or any(ord(c) < 32 for c in name):
        raise ValueError("Location name must have 2-100 printable characters")
    return (
        ENDPOINT + "?" + urlencode({"name": name, "count": 3, "language": "en", "format": "json"})
    )


def fetch_location(call: str, question: str) -> dict[str, Any]:
    url = validated_url(call, question)
    request = Request(url, headers={"User-Agent": "MWPC-TCC-research-demo/1.0"})
    with urlopen(request, timeout=15) as response:
        raw = response.read(1_048_577)
    if len(raw) > 1_048_576:
        raise ValueError("API response exceeds one MiB")
    payload = json.loads(raw)
    if not isinstance(payload, dict) or payload.get("error"):
        raise ValueError("Geocoding API returned an invalid/error response")
    return {
        "url": url,
        "fetched_at_utc": datetime.now(UTC).isoformat(),
        "attribution": ATTRIBUTION,
        "response_sha256": hashlib.sha256(raw).hexdigest(),
        "raw_response": raw.decode("utf-8"),
        "payload": payload,
    }


def save_record(directory: Path, record: dict[str, Any]) -> None:
    directory.mkdir(parents=True, exist_ok=False)
    raw = (json.dumps(record, indent=2, ensure_ascii=False, allow_nan=False) + "\n").encode()
    (directory / "record.json").write_bytes(raw)
    (directory / "manifest.json").write_text(
        json.dumps({"record.json": hashlib.sha256(raw).hexdigest()}, indent=2) + "\n"
    )


def read_record(directory: Path) -> dict[str, Any]:
    raw = (directory / "record.json").read_bytes()
    manifest = json.loads((directory / "manifest.json").read_text())
    if manifest != {"record.json": hashlib.sha256(raw).hexdigest()}:
        raise ValueError("Replay record checksum mismatch")
    record: dict[str, Any] = json.loads(raw)
    if record.get("mode") != "live" or record.get("function") != FUNCTION:
        raise ValueError("Replay must originate from the recorded live demo schema")
    if record["generation"]["status"] == "complete":
        api = record.get("api")
        try:
            url = validated_url(record["generation"]["output"], record["request"])
        except ValueError:
            # Failed dispatch is evidence too. It cannot authorize a recorded query.
            failure = record.get("failure")
            if (
                api is not None
                or record.get("status") != "query_failed"
                or not isinstance(failure, dict)
                or failure.get("type") != "ValueError"
                or not isinstance(failure.get("message"), str)
            ):
                raise
            return record
        if api:
            if api["url"] != url:
                raise ValueError("Recorded API URL does not match the validated call")
            if hashlib.sha256(api["raw_response"].encode()).hexdigest() != api["response_sha256"]:
                raise ValueError("Recorded API response checksum mismatch")
            if json.loads(api["raw_response"]) != api["payload"]:
                raise ValueError("Recorded API payload differs from its raw response")
    elif record.get("api"):
        raise ValueError("Incomplete generation must not execute a query")
    return record


def display_record(record: dict[str, Any], *, replay: bool) -> dict[str, Any]:
    api = record.get("api") or {}
    return {
        "mode": "replay; no inference or network access" if replay else "live inference and query",
        "request": record["request"],
        "method": record["policy"]["name"],
        "status": record["status"],
        "generated_call": record["generation"].get("output"),
        "model_forwards": record["generation"].get("forwards", 0),
        "locations": api.get("payload", {}).get("results", []),
        "fetched_at_utc": api.get("fetched_at_utc"),
        "source": api.get("url"),
        "attribution": api.get("attribution"),
        "failure": record.get("failure"),
    }
