import copy
import hashlib
import json
from contextlib import contextmanager
from pathlib import Path

import pytest

from mwpc_research import geocoding

QUESTION = 'Locate "São Paulo".'
CALL = "get_location(name='São Paulo')"


def test_independent_checker_accepts_all_archived_live_v1_records_without_network(monkeypatch):
    from scripts.exact_commit.verify_query_demo import verify

    def no_network(*args, **kwargs):
        raise AssertionError("certificate checking must remain offline")

    monkeypatch.setattr(geocoding, "urlopen", no_network)
    root = Path(__file__).resolve().parents[2] / "docs/artifacts/demo"
    records = [root / "geocoding_v1", *sorted((root / "geocoding_comparators_v1").iterdir())]
    assert len(records) == 4
    for directory in records:
        result = verify(directory)
        assert result["status"] == "query_empty"
        assert result["api_recorded"]


def test_quote_free_profile_excludes_corrupted_spans_and_preserves_place_names():
    question = 'Find the geographic coordinates of "Belo Horizonte".'
    legacy = geocoding.geocoding_catalog(question)
    restricted = geocoding.geocoding_catalog(question, "quote_free_names_v2")
    assert "get_location(name='Belo Horizonte')" in restricted
    assert "get_location(name='Belo')" in restricted
    assert "get_location(name='Horizonte')" in restricted
    bad = """get_location(name='of "Belo Horizonte')"""
    assert bad in legacy and bad not in restricted
    geocoding.validated_url(bad, question)
    with pytest.raises(ValueError):
        geocoding.validated_url(bad, question, "quote_free_names_v2")
    apostrophe = geocoding.geocoding_catalog("Locate O'Fallon.", "quote_free_names_v2")
    assert any(
        "O'Fallon" == geocoding.scalar_call_arguments(c, geocoding.FUNCTION)["name"]
        for c in apostrophe
    )
    with pytest.raises(ValueError, match="Unknown"):
        geocoding.geocoding_catalog(question, "undeclared")


def test_dispatch_encodes_only_the_validated_allowlisted_call():
    url = geocoding.validated_url(CALL, QUESTION)
    assert url.startswith(geocoding.ENDPOINT + "?")
    assert "name=S%C3%A3o+Paulo" in url and "count=3" in url
    for bad in [
        "evil(name='São Paulo')",
        "get_location(name='unmentioned')",
        "get_location(name=__import__('os').system('false'))",
        "get_location(name=3)",
    ]:
        with pytest.raises(ValueError):
            geocoding.validated_url(bad, QUESTION)


def test_api_uses_bounded_read_and_handles_empty_error_and_oversize(monkeypatch):
    class Response:
        raw = b'{"results": []}'

        def read(self, count):
            assert count == 1_048_577
            return self.raw

    @contextmanager
    def open_url(request, timeout):
        assert timeout == 15 and request.get_method() == "GET"
        yield Response()

    monkeypatch.setattr(geocoding, "urlopen", open_url)
    api = geocoding.fetch_location(CALL, QUESTION)
    assert api["payload"] == {"results": []}
    assert api["response_sha256"] == hashlib.sha256(Response.raw).hexdigest()
    for raw in (b'{"error": true}', b"[]", b" " * 1_048_577):
        Response.raw = raw
        with pytest.raises(ValueError):
            geocoding.fetch_location(CALL, QUESTION)


def test_replay_never_contacts_network_and_rejects_changed_record(tmp_path, monkeypatch):
    def no_network(*args, **kwargs):
        raise AssertionError("replay must not contact a service")

    monkeypatch.setattr(geocoding, "urlopen", no_network)
    record = {
        "mode": "live",
        "function": copy.deepcopy(geocoding.FUNCTION),
        "request": QUESTION,
        "generation": {"status": "complete", "output": CALL},
        "policy": {"name": "confidence_0.8"},
        "status": "query_complete",
        "api": {
            "url": geocoding.validated_url(CALL, QUESTION),
            "raw_response": "{}",
            "response_sha256": hashlib.sha256(b"{}").hexdigest(),
            "payload": {},
        },
    }
    directory = tmp_path / "record"
    geocoding.save_record(directory, record)
    read = geocoding.read_record(directory)
    assert read == record
    assert geocoding.display_record(read, replay=True)["mode"].startswith("replay;")
    with pytest.raises(FileExistsError):
        geocoding.save_record(directory, record)
    (directory / "record.json").write_text("{}")
    with pytest.raises(ValueError, match="checksum"):
        geocoding.read_record(directory)
    # Updating a checksum cannot make a mismatched dispatch consistent.
    record["api"]["url"] = "https://example.invalid/"
    geocoding.save_record(tmp_path / "bad_url", record)
    with pytest.raises(ValueError, match="URL"):
        geocoding.read_record(tmp_path / "bad_url")
    record["api"]["url"] = geocoding.validated_url(CALL, QUESTION)
    record["api"]["payload"] = json.loads('{"different": true}')
    geocoding.save_record(tmp_path / "bad_payload", record)
    with pytest.raises(ValueError, match="payload"):
        geocoding.read_record(tmp_path / "bad_payload")


def test_rejected_dispatch_can_be_replayed_without_claiming_a_query(tmp_path, monkeypatch):
    def no_network(*args, **kwargs):
        raise AssertionError("rejected dispatch replay must not contact a service")

    monkeypatch.setattr(geocoding, "urlopen", no_network)
    record = {
        "mode": "live",
        "function": copy.deepcopy(geocoding.FUNCTION),
        "request": QUESTION,
        "generation": {"status": "complete", "output": "get_location(name='unmentioned')"},
        "policy": {"name": "confidence_0.8"},
        "status": "query_failed",
        "api": None,
        "failure": {"type": "ValueError", "message": "Call rejected before dispatch"},
    }
    geocoding.save_record(tmp_path / "rejected", record)
    assert geocoding.read_record(tmp_path / "rejected") == record
    record["status"] = "query_complete"
    geocoding.save_record(tmp_path / "false_success", record)
    with pytest.raises(ValueError):
        geocoding.read_record(tmp_path / "false_success")
