from __future__ import annotations

from copy import deepcopy

import pytest
from scripts.exact_commit.build_probability_results import check_case, manifest


def fixture():
    probe = {"id": "nested", "prefix": "[", "suffix": "]"}
    config = {
        "probes": [probe],
        "slots": [1, 2],
        "model_revision": "model-rev",
        "tokenizer_revision": "token-rev",
        "seed": 300000,
    }
    case = {
        "probe": probe,
        "id": "nested-1",
        "slots": 1,
        "model_revision": "model-rev",
        "tokenizer_revision": "token-rev",
        "seed": 300000,
        "array_file": "nested-1.npz",
        "canvas": [0, None, 1],
        "masked_positions": [1],
    }
    return config, case, (b"[", b"]", None)


def test_probability_provenance_rejects_swapped_target_canvas_slots_and_revisions():
    config, case, emissions = fixture()
    check_case(config, case, "nested-1", emissions)
    for changes in (
        {"probe": {**case["probe"], "prefix": "]"}},
        {"canvas": [1, None, 1]},
        {"canvas": [0, 2, 1]},
        {"masked_positions": [True]},
        {"masked_positions": [0]},
        {"model_revision": "another"},
        {"seed": 4},
        {"array_file": "other.npz"},
    ):
        with pytest.raises(ValueError):
            check_case(config, {**deepcopy(case), **changes}, "nested-1", emissions)


def test_probability_manifest_cannot_hide_an_unlisted_nested_manifest(tmp_path):
    from scripts.exact_commit.run_conflict_real import sha

    (tmp_path / "manifest.json").write_text("{}")
    manifest(tmp_path)
    nested = tmp_path / "proofs"
    nested.mkdir()
    (nested / "manifest.json").write_text("{}")
    with pytest.raises(ValueError, match="inventory"):
        manifest(tmp_path)
    import json

    (tmp_path / "manifest.json").write_text(
        json.dumps({"proofs/manifest.json": sha(nested / "manifest.json")})
    )
    manifest(tmp_path)
