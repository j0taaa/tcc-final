"""Tiny RANDOM architecture: full-V output only at requested hidden positions."""

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
        "a52_indexed_random", folder / "modeling_qwen3.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    torch.manual_seed(520502)
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
    model = module.A2DQwen3LMHeadModel(config).to(dtype=torch.bfloat16).eval()
    ids = torch.tensor([[1, 3, 6, 8, 9, 4]])
    indices = torch.tensor([1, 3, 5])
    with torch.no_grad():
        full = model(ids, attention_mask=torch.ones_like(ids), use_cache=False).logits
        cropped = model(
            ids, attention_mask=torch.ones_like(ids), use_cache=False, logits_to_keep=indices
        ).logits
    error = float((cropped - full[:, indices]).abs().max())
    report = {
        "status": "PASS" if error == 0 and cropped.shape == (1, 3, 32) else "ERROR",
        "max_error": error,
        "toy_model_forwards": 2,
        "pretrained_forwards": 0,
        "dtype": str(cropped.dtype),
    }
    (output / "summary.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report))
    if report["status"] != "PASS":
        raise AssertionError("indexed BF16 head cropping mismatch")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--tokenizer-dir", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()
    run(args.tokenizer_dir, args.output)
