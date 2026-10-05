import pytest
from scripts.exact_commit.complete_conflict_campaign import valid_prefix


def test_recovery_preserves_complete_records_and_only_accepts_zero_suffix(tmp_path):
    p = tmp_path / "partial.jsonl"
    prefix = b'{"status":"completed","instance_id":"a"}\n'
    p.write_bytes(prefix + bytes(8))
    assert valid_prefix(p) == (prefix, [{"status": "completed", "instance_id": "a"}])
    p.write_bytes(prefix + b"\0bad")
    with pytest.raises(ValueError, match="nonzero"):
        valid_prefix(p)
    p.write_bytes(prefix + b"{")
    with pytest.raises(ValueError):
        valid_prefix(p)
