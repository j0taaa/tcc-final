"""Pinned architecture API check with tiny RANDOM weights, never the checkpoint."""

import argparse
import importlib.util
import json
from pathlib import Path

from .tokenizer_audit import verify_files


def run(folder, output):
    import torch

    output.mkdir(parents=True, exist_ok=False)
    verify_files(folder)
    spec = importlib.util.spec_from_file_location(
        "a52_pinned_model_api", folder / "modeling_qwen3.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    torch.manual_seed(520403)
    config = module.A2DQwen3Config(
        vocab_size=32,
        hidden_size=32,
        intermediate_size=64,
        num_hidden_layers=1,
        num_attention_heads=4,
        num_key_value_heads=2,
        head_dim=8,
        max_position_embeddings=64,
        max_window_layers=1,
        layer_types=["full_attention"],
        use_cache=False,
        pad_token_id=0,
        bos_token_id=1,
        eos_token_id=2,
    )
    config._attn_implementation = "sdpa"
    model = module.A2DQwen3LMHeadModel(config).eval()
    original, changed = torch.tensor([[1, 3, 6, 8]]), torch.tensor([[1, 3, 6, 9]])
    all_valid, padded = torch.ones(1, 4, dtype=torch.long), torch.tensor([[1, 1, 1, 0]])
    calls = 0

    def forward(ids, mask, keep=0):
        nonlocal calls
        calls += 1
        with torch.no_grad():
            return model(ids, attention_mask=mask, use_cache=False, logits_to_keep=keep).logits

    report = {"pretrained_model_forwards": 0, "weights": "random-tiny-architecture-only"}
    try:
        full = forward(original, all_valid)
        cropped = forward(original, all_valid, 2)
        alternative = forward(changed, all_valid)
        before = forward(original, padded)
        after = forward(changed, padded)
        crop_error = float((cropped - full[:, -2:]).abs().max())
        future_effect = float((alternative[:, 0] - full[:, 0]).abs().max())
        padding_error = float((before[:, :3] - after[:, :3]).abs().max())
        if cropped.shape != (1, 2, 32) or crop_error > 1e-6:
            raise AssertionError("head cropping changed requested logits")
        if future_effect <= 1e-9 or padding_error > 1e-6:
            raise AssertionError("bidirectional/padding attention API mismatch")
        report.update(
            {
                "status": "PASS",
                "crop_error": crop_error,
                "future_token_effect": future_effect,
                "padding_error": padding_error,
            }
        )
    except Exception as error:
        report.update({"status": "ERROR", "exception": repr(error)})
        raise
    finally:
        report["toy_model_forward_calls"] = calls
        (output / "summary.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report))


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--tokenizer-dir", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()
    run(args.tokenizer_dir, args.output)
