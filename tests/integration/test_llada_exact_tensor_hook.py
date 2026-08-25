from __future__ import annotations

import pytest

from mwpc_exact import (
    AdaptiveSupportConfig,
    CompositionalByteLevelAdapter,
    EOSMode,
    EOSPolicy,
    ExactBackend,
    ExactStrategyConfig,
    ProposalWeightMode,
)
from mwpc_exact.epic_adapter.llada import LLaDAAdapterProfile, run_llada_exact_step
from mwpc_exact.reference.grammar import CnfGrammar, Nonterminal, Terminal, TerminalProduction

torch = pytest.importorskip("torch", reason="install the pinned EPIC CPU environment")
llada_baseline = pytest.importorskip(
    "constrained_diffusion.eval.dllm.models.llada.generate_constrained",
    reason="install the pinned EPIC CPU environment",
)
regular_cover_baseline = pytest.importorskip(
    "constrained_diffusion.regular_cover",
    reason="install the pinned EPIC CPU environment",
)


@pytest.mark.integration
def test_exact_hook_commits_to_a_real_single_batch_torch_row() -> None:
    original_serial = llada_baseline.generate
    original_epic = regular_cover_baseline.select_batch_with_regular_cover
    eos, eot, mask = 1, 2, 3
    profile = LLaDAAdapterProfile(
        model_id="offline/torch-llada-style-fixture",
        tokenizer_revision="fixed",
        mask_token_id=mask,
        eos_policy=EOSPolicy(
            EOSMode.REQUIRED,
            termination_token_ids=(eos, eot),
            pad_token_id=eos,
        ),
    )
    grammar = CnfGrammar(
        nonterminals=(Nonterminal(0, "S"),),
        terminals=(Terminal(0, ord("a")),),
        start_nonterminal_id=0,
        terminal_productions=(TerminalProduction(0, 0, 0),),
    )
    adapter = CompositionalByteLevelAdapter((b"a", None, None, None))
    config = ExactStrategyConfig(
        adaptive_support=AdaptiveSupportConfig(initial_k=1, k_max=1),
        weight_mode=ProposalWeightMode.CONFIDENCE,
        eos_policy=profile.eos_policy,
        backend=ExactBackend.PYTHON,
        failure_fallback_strategy=None,
    )
    token_row = torch.tensor([0, mask, mask], dtype=torch.long)
    logits = torch.tensor(
        [
            [10.0, 0.0, -1.0, -2.0],
            [10.0, 0.0, -1.0, -2.0],
            [0.0, 10.0, 9.0, -2.0],
        ],
        dtype=torch.float64,
    )
    tracking: list[object] = ["prompt", None, None]

    outcome = run_llada_exact_step(
        grammar,
        token_ids=token_row,
        logits=logits,
        predicted_token_ids=torch.tensor([0, 0, eos]),
        confidence_values=torch.tensor([-float("inf"), 0.9, 0.8]),
        decoded_tracking=tracking,
        decode_token=lambda token_id: f"token-{token_id}",
        eos_marker="<EOS>",
        prompt_length=1,
        generation_length=2,
        active_block_end=3,
        k_s=2,
        tokenizer_adapter=adapter,
        config=config,
        profile=profile,
    )

    assert token_row.tolist() == [0, 0, eos]
    assert tracking == ["prompt", "token-0", "<EOS>"]
    assert outcome.complete is True
    assert llada_baseline.generate is original_serial
    assert regular_cover_baseline.select_batch_with_regular_cover is original_epic
