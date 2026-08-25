"""Read-only integration adapters for the pinned EPIC baseline.

Do not place model-independent solver logic in this package.
"""

from mwpc_exact.epic_adapter.llada import (
    LLADA_EOS_TOKEN_ID,
    LLADA_EOT_TOKEN_ID,
    LLADA_MASK_TOKEN_ID,
    LLADA_MODEL_ID,
    LLADA_TOKENIZER_REVISION,
    PINNED_LLADA_PROFILE,
    LLaDAAdapterProfile,
    LLaDAExactStepRequest,
    LLaDAExactStepResult,
    LLaDATokenUpdate,
    LLaDAUpdateReason,
    prepare_llada_exact_step,
    run_llada_exact_step,
)

__all__ = [
    "LLADA_EOS_TOKEN_ID",
    "LLADA_EOT_TOKEN_ID",
    "LLADA_MASK_TOKEN_ID",
    "LLADA_MODEL_ID",
    "LLADA_TOKENIZER_REVISION",
    "PINNED_LLADA_PROFILE",
    "LLaDAAdapterProfile",
    "LLaDAExactStepRequest",
    "LLaDAExactStepResult",
    "LLaDATokenUpdate",
    "LLaDAUpdateReason",
    "prepare_llada_exact_step",
    "run_llada_exact_step",
]
