from __future__ import annotations

import copy
import json
import subprocess
import sys
from dataclasses import replace

import pytest
from test_original_budget_certificate import fixture

from mwpc_exact.budget_bounds import budget_input_fingerprint
from mwpc_exact.budget_proof import budget_proof_data, read_budget_proof, verify_budget_proof
from mwpc_exact.budgeted_commit import budgeted_commit_frontier


def payload():
    state, _ = fixture()
    return state, budget_proof_data(state, budgeted_commit_frontier(state, 2))


def test_portable_proof_roundtrip_and_external_input_binding():
    state, data = payload()
    encoded = json.loads(json.dumps(data))
    restored, results = read_budget_proof(encoded)
    assert restored == state
    assert len(results) == 3
    report = verify_budget_proof(
        encoded, expected_input=state, expected_input_fingerprint=budget_input_fingerprint(state)
    )
    assert report["verification_scope"] == "original_input_and_resource_optimality"
    for foreign in (replace(state, proposals=()),):
        with pytest.raises(ValueError, match="external input"):
            verify_budget_proof(encoded, expected_input=foreign)
    with pytest.raises(ValueError, match="fingerprint"):
        verify_budget_proof(encoded, expected_input_fingerprint="0" * 64)


@pytest.mark.parametrize(
    "change",
    (
        "tokens",
        "commitments",
        "weight",
        "bytes",
        "prefix",
        "arc_reward",
        "support",
        "missing_cap",
        "false_id",
    ),
)
def test_portable_checker_rejects_changes_to_original_inputs_or_metadata(change):
    _, original = payload()
    data = copy.deepcopy(original)
    if change == "tokens":
        data["frontier"][1]["witness_token_ids"] = [3]
    elif change == "commitments":
        data["frontier"][1]["committed_proposal_ids"] = []
    elif change == "weight":
        data["input"]["selection"]["proposals"][0]["weight"] = 200
    elif change == "bytes":
        data["input"]["selection"]["tokenizer_adapter"]["emissions_hex"][0] = "78"
    elif change == "prefix":
        data["compilation"]["nodes"][-1][3] = "78"
    elif change == "arc_reward":
        data["graph"]["arcs"][-1][4] = [100, 1]
    elif change == "support":
        data["input"]["selection"]["support"]["rows"][0] = [0]
    elif change == "missing_cap":
        data["frontier"] = data["frontier"][1:]
    elif change == "false_id":
        data["frontier"][1]["witness_arc_ids"] = [False]
    with pytest.raises((ValueError, TypeError)):
        verify_budget_proof(data)


def test_independent_verification_does_not_import_budgeted_optimizer(tmp_path):
    _, data = payload()
    artifact = tmp_path / "proof.json"
    artifact.write_text(json.dumps(data))
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            "import json,sys; from mwpc_exact.budget_proof import verify_budget_proof; "
            "verify_budget_proof(json.load(open(sys.argv[1]))); "
            "assert 'mwpc_exact.reference.budgeted_parser' not in sys.modules; "
            "assert 'mwpc_exact.budgeted_commit' not in sys.modules",
            str(artifact),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
