"""Fake native fixture copied from A31 source0a27a24, not neural evidence."""

from types import SimpleNamespace

import torch
from constrained_diffusion.eval.dllm.models.llada import generate_constrained as native


class TinyTokenizer:
    pieces = ("0", "1", "x", "0", "<eos>", "<mask>", "prompt")

    def __init__(self):
        self.special_tokens_map = {"eos_token": "<eos>"}

    def decode(self, token):
        return self.pieces[int(token)]

    def batch_decode(self, tokens):
        return [self.decode(token) for token in tokens]


class TinyHead:
    def __init__(self, device):
        self.device = device
        self.calls = []

    def __call__(self, tokens):
        values = torch.tensor(
            [0.2, 0.1, 2.2, -2.0, -1.0, -torch.inf, -torch.inf], device=self.device
        )
        logits = values.expand(1, tokens.shape[1], -1).clone()
        if int((tokens == 5).sum()) == 1:
            logits[:, :, 4] = 2.0
        self.calls.append((tokens.detach().cpu().clone(), logits.detach().cpu().clone()))
        return SimpleNamespace(logits=logits)


def consume(model, grammar, lexical, settings):
    return tuple(
        (
            tuple(tuple(row) for row in tokens.cpu().tolist()),
            tuple(pos for pos, _t in rejected),
            done,
        )
        for tokens, rejected, done in native.generate(
            model,
            torch.tensor([[6]], device=model.device),
            TinyTokenizer(),
            grammar,
            lexical,
            prompt_len=1,
            steps=2,
            gen_length=2,
            block_length=2,
            mask_id=5,
            constrain=True,
            **settings,
        )
    )
