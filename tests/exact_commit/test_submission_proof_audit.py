from __future__ import annotations

from pathlib import Path

from mwpc_exact import (
    Proposal,
    SupportKind,
    SupportPolicy,
    build_per_position_support,
    build_token_lattice,
)

ROOT = Path(__file__).resolve().parents[2]
ARTICLE = ROOT / "paper" / "main.tex"
AUDIT = ROOT / "docs" / "evidence" / "submission-proof-audit.md"


def test_optimal_batch_proof_matches_positive_weight_certificate_contract() -> None:
    article = ARTICLE.read_text(encoding="utf-8")

    assert (
        r"\Match_C^+(y)&=\{j\in\{1,\ldots,m\}:y_{i_j}=t_j,\ w_j>0\}"
        in article
    )
    assert r"J^*=\Match_C^+(y^*)" in article
    assert r"J^*\gets\{j:y^*_{i_j}=t_j,\ w_j>0\}" in article
    assert "Zero-weight proposals do not change the objective" in article

    support = build_per_position_support(
        canvas=(None,),
        policy=SupportPolicy(kind=SupportKind.EXPLICIT, vocabulary_size=2),
        explicit_support={0: (1,)},
    )
    lattice = build_token_lattice(
        support=support,
        proposals=(
            Proposal(10, position=0, token_id=1, weight=2),
            Proposal(11, position=0, token_id=1, weight=0),
            Proposal(12, position=0, token_id=1, weight=3),
        ),
    )
    path = next(lattice.iter_paths())

    assert path.objective_value == 5.0
    assert path.matched_proposal_ids == (10, 12)
    assert lattice.zero_weight_proposal_ids == (11,)


def test_proof_audit_maps_every_formal_result_and_closes_submission_field() -> None:
    audit = AUDIT.read_text(encoding="utf-8")
    checklist = (ROOT / "paper" / "FIELDS_TO_FILL.md").read_text(encoding="utf-8")

    for formal_result in (
        "Theorem 1",
        "Corollary 1",
        "Theorem 2",
        "Theorem 3",
        "Theorem 4",
        "Propositions 1--2",
    ):
        assert formal_result in audit
    assert "- [x] Review every proof against the final implementation" in checklist
