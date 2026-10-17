"""Capture the original masked loop's final MODEL-logit proposal, no backbone."""

from __future__ import annotations

import ast
import hashlib
import importlib
import json
import sys
from contextlib import contextmanager
from pathlib import Path

import torch
from native_adapter import PIN, TerminalSnapshot


def bit_digest(tensor):
    payload = tensor.detach().contiguous().view(torch.uint8).cpu().numpy().tobytes()
    description = f"{tensor.dtype}:{tuple(tensor.shape)}:".encode()
    return hashlib.sha256(description + payload).hexdigest()


def load_masked():
    root = Path(__file__).parent / "masked_source_v6"
    manifest = json.loads((root / "manifest.json").read_text())
    assert manifest["commit"] == PIN
    for row in manifest["files"]:
        assert hashlib.sha256((root / row["file"]).read_bytes()).hexdigest() == row["sha256"]
    if "mosaic" in sys.modules:
        assert Path(sys.modules["mosaic"].__file__).resolve().is_relative_to(root.resolve())
    precision = torch.get_float32_matmul_precision()
    sys.path.insert(0, str(root))
    try:
        matcher = importlib.import_module("mosaic.matcher")
        loop = importlib.import_module("mosaic.dlm.llada")
    finally:
        sys.path.pop(0)
        torch.set_float32_matmul_precision(precision)
    source = root / "integrations/vllm/mosaic_vllm.py"
    tree = ast.parse(source.read_text())
    names = {"_offset_groups", "_propose"}
    functions = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name in names]
    assert {n.name for n in functions} == names
    namespace = {"torch": torch, "FREE": -1}
    exec(compile(ast.Module(body=functions, type_ignores=[]), str(source), "exec"), namespace)
    return {"matcher": matcher, "loop": loop, "functions": namespace, "origin": manifest}


class ControlTokens:
    """Explicit actual control IDs; synthetic names only inside the readout API."""

    def __init__(self, tokenizer, eot, pad):
        self.tokenizer, self.eot, self.pad = tokenizer, eot, pad

    def convert_tokens_to_ids(self, text):
        assert text in ("<eot>", "<pad>")
        return self.eot if text == "<eot>" else self.pad

    def decode(self, token):
        return self.tokenizer.decode(int(token))


class LastProposal:
    def __init__(self, runtime, tokenizer, labels, eot, pad, expected_calls, last_masks):
        self.runtime = runtime
        self.tokenizer = ControlTokens(tokenizer, eot, pad)
        self.labels = tuple(labels)
        self.expected_calls, self.last_masks = expected_calls, last_masks
        self.calls, self.trace = 0, []
        self.snapshot = None

    @contextmanager
    def attach(self, matcher):
        from native_adapter import rng_state

        original = matcher.propose_x0

        def hook(logits, tokens, mask_token_id, temperature=0.0, return_marginal=True):
            self.calls += 1
            self.trace.append(
                {"tokens_sha256": bit_digest(tokens), "logits_sha256": bit_digest(logits)}
            )
            if self.calls == self.expected_calls:
                assert temperature == 0.0 and return_marginal
                assert int((tokens == mask_token_id).sum()) == self.last_masks
                free = torch.where(tokens == mask_token_id, -1, tokens)
                self.raw_logits = logits.detach().clone()
                self.snapshot = TerminalSnapshot.capture(
                    self.runtime, matcher, logits.float(), free, 0, (), self.tokenizer, self.labels
                )
                self.before_rng = rng_state()
            output = original(logits, tokens, mask_token_id, temperature, return_marginal)
            if self.calls == self.expected_calls:
                self.first = tuple(output[0][0].tolist())
                self.after_rng = rng_state()
                self.caller_logits = logits
            return output

        matcher.propose_x0 = hook
        try:
            yield self
            assert self.calls == self.expected_calls and self.snapshot is not None
        finally:
            matcher.propose_x0 = original
