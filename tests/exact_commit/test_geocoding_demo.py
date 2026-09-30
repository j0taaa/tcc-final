import copy
import hashlib
import json
from contextlib import contextmanager

import pytest

from mwpc_research import geocoding

QUESTION = 'Locate "São Paulo".'
CALL = "get_location(name='São Paulo')"


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
