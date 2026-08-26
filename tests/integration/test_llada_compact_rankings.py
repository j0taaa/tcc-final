from __future__ import annotations

import pytest

from mwpc_exact import EOSMode, EOSPolicy, ProposalWeightMode
from mwpc_exact.epic_adapter.llada import LLaDAAdapterProfile, prepare_llada_exact_step

torch = pytest.importorskip("torch", reason="install the pinned EPIC CPU environment")


@pytest.mark.integration
def test_live_tensor_boundary_keeps_only_kmax_rankings_on_cpu() -> None:
    prompt_length = 2
    generation_length = 3
    vocabulary_size = 4096
    logits = torch.zeros((prompt_length + generation_length, vocabulary_size))
    logits[2, 17] = 9.0
    logits[3, 18] = 8.0
    logits[4, 19] = 7.0
    request = prepare_llada_exact_step(
        token_ids=(1, 2, 5, 5, 5),
        logits=logits,
        predicted_token_ids=(1, 2, 17, 18, 19),
        confidence_values=(0.0, 0.0, 0.9, 0.8, 0.7),
        prompt_length=prompt_length,
        generation_length=generation_length,
        active_block_end=prompt_length + generation_length,
        k_s=3,
        weight_mode=ProposalWeightMode.CONFIDENCE,
        permitted_token_ids=tuple(range(vocabulary_size)),
        support_k_max=4,
        profile=LLaDAAdapterProfile(
            model_id="fixture",
            tokenizer_revision="fixture",
            mask_token_id=5,
            eos_policy=EOSPolicy(EOSMode.ABSENT),
        ),
    )
    assert request.logit_shape == (generation_length, vocabulary_size)
    assert request.ranked_support_rows.max_k == 4
    assert sum(len(row) for row in request.ranked_support_rows.token_ids_by_position) == 12
    assert request.ranked_support_rows.token_ids_by_position[0][0] == 17
    assert not hasattr(request, "logits")
