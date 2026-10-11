"""A31: native fake-head replay of state/history/root; NOT a neural benchmark."""

import argparse
import hashlib
import importlib
import json
from pathlib import Path
from types import SimpleNamespace

import torch
from constrained_diffusion.constrain_utils import compile_lex_map
from constrained_diffusion.eval.dllm.models.llada import generate_constrained as native
from rustformlang.cfg import CFG

from .ledger import HistoryLedger, cpu_double, cuda_double
from .native_noise import ModelHistory, coupled_noise


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


class SameNativeTicket:
    def __init__(self, values, transform):
        self.values, self.transform = iter(values), transform

    def randrange(self, stop):
        if stop == 1:
            return 0
        if stop != 2**53:
            raise AssertionError("unexpected RNG request")
        value = float(next(self.values))
        ticket = 2**53 - 1 if self.transform is cuda_double and value == 0 else int(value * 2**53)
        if self.transform(ticket) != value:
            raise AssertionError("native value outside audited uniform profile")
        return ticket


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


def probe(device, seed, temperature, coordinate, max_resamples, mode):
    grammar = CFG.from_text("S -> lexNumber", "S").to_normal_form()
    lexical = compile_lex_map({"lexNumber": "(0|1)"})
    settings = {"temperature": temperature, "max_resamples": max_resamples}
    torch.manual_seed(seed)
    model, raw = TinyHead(device), []
    original_rand = torch.rand_like

    def observed_rand(*args, **kwargs):
        result = original_rand(*args, **kwargs)
        raw.append(result.cpu().clone())
        return result

    torch.rand_like = observed_rand
    try:
        reference = consume(model, grammar, lexical, settings)
    finally:
        torch.rand_like = original_rand
    chosen = []
    for (tokens, logits), uniforms in zip(model.calls, raw, strict=True) if temperature else ():
        positions = (tokens[0] == 5).nonzero().flatten().tolist()
        if coordinate == "entropy":
            entropy = torch.special.entr(torch.softmax(logits[0, positions].double(), dim=-1)).sum(
                -1
            )
            pos = positions[int(entropy.argmax())]
        else:
            pos = positions[0]
        chosen.append(uniforms[0, pos, int(logits[0, pos].argmax())])
    transform = cuda_double if device == "cuda" else cpu_double
    book = HistoryLedger(1, SameNativeTicket(chosen, transform))
    torch.manual_seed(seed)
    proxy = ModelHistory(
        TinyHead(device), ("tiny-native-correctness", tuple(settings.items())), mode=mode
    )
    original_noise = native.add_gumbel_noise
    with coupled_noise(native, proxy, book, 0, mask_id=5, coordinate=coordinate):
        actual = consume(proxy, grammar, lexical, settings)
    if native.add_gumbel_noise is not original_noise or actual != reference:
        raise AssertionError("native trajectory/recovery/EOS diverged or hook was not restored")
    if len(proxy.model.calls) != len(model.calls):
        raise AssertionError("native forwards diverged")
    if mode == "history":
        prior_rejections = [
            len(event[1][4]) for key in book.tables for event in key[2] if event[0] == "noise"
        ]
    else:
        prior_rejections = [key[2][2][4] for key in book.tables]
    return {
        "device": device,
        "mode": mode,
        "seed": seed,
        "temperature": temperature,
        "coordinate": coordinate,
        "max_resamples": max_resamples,
        "equal": True,
        "forwards": len(model.calls),
        "rejections": len(reference[-1][1]),
        "complete": bool(reference[-1][2]),
        "max_prior_rejections_in_keys": max(prior_rejections, default=0),
        "original_token_aliases": [0, 3],
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    rows = [
        probe(device, seed, temperature, coordinate, max_resamples, mode)
        for device in ("cpu", "cuda")
        for seed in range(3)
        for temperature in (0.0, 0.5, 1.0)
        for coordinate in ("first", "entropy")
        for max_resamples in (1, 8)
        for mode in ("state", "history", "root")
    ]
    result = {
        "scope": "native EPIC replay; fake logits; no neural forward or speed claim",
        "torch": torch.__version__,
        "rows": rows,
        "producer_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "hook_sha256": hashlib.sha256(
            Path(importlib.import_module(__package__ + ".native_noise").__file__).read_bytes()
        ).hexdigest(),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({"checks": len(rows), "equal": sum(r["equal"] for r in rows)}))


if __name__ == "__main__":
    main()
