"""Opt-in full-wrapper smoke with FAKE large-ID head, never neural evidence."""

import argparse
import functools
import hashlib
import json
import random
from pathlib import Path
from types import SimpleNamespace
from typing import ClassVar

import torch
from constrained_diffusion.constrain_utils import compile_lex_map, preprocessed_generate_stuff
from rustformlang.cfg import CFG

from .native_decode_v4 import decode
from .native_experiment_v4 import fingerprint
from .native_noise_v4 import PairBook, coupled_noise
from .numeric_partition import NumericPartition
from .numeric_task import task
from .raw_anchored_ledger import AnchoredLedger
from .raw_noise import coupled_noise as raw_noise


class Tokenizer:
    special_tokens_map: ClassVar = {"eos_token": "<eos>"}
    pieces: ClassVar = {
        0: "0",
        1: "1",
        2: "prompt",
        3: '{"answer":',
        4: "}",
        126081: "<eos>",
        126336: "<mask>",
    }

    def decode(self, tokens, skip_special_tokens=False, **kwargs):
        if isinstance(tokens, int) or (isinstance(tokens, torch.Tensor) and tokens.ndim == 0):
            return self.pieces.get(int(tokens), "x")
        return "".join(
            self.pieces.get(int(t), "x")
            for t in tokens
            if not skip_special_tokens or int(t) not in (126081, 126336)
        )

    def batch_decode(self, tokens):
        return [self.decode(t) for t in tokens]


class Head:
    def __init__(self):
        self.device = torch.device("cuda")
        self.queries = self.forwards = 0

    def __call__(self, ids):
        self.queries += 1
        self.forwards += 1
        logits = torch.full((*ids.shape, 126337), -torch.inf, device=self.device)
        logits[..., 126081] = -3.0
        logits[:, 2, 0] = 0.2
        logits[:, 2, 1] = 0.1
        logits[:, 3, 4] = 1.0
        return SimpleNamespace(logits=logits)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise SystemExit("refuse to overwrite smoke evidence")
    here = Path(__file__).parent
    config = json.loads((here / "protocol-v4.json").read_text())
    config.update(gen_length=2, block_length=2, steps=2, max_resamples=8)
    t, tokenizer = task("FAKE wrapper case"), Tokenizer()
    grammar = CFG.from_text(t["grammar"], "S").to_normal_form()
    lex = compile_lex_map(t["lexical"])
    additional = preprocessed_generate_stuff(tokenizer, grammar, lex)
    partition = NumericPartition(("0", "1"))
    rows, references = [], {}
    with torch.no_grad():
        for temperature in config["temperatures"]:
            for method in config["methods"]:
                seed, book, hook = 123, None, None
                if method["kind"] in ("walk", "pool", "pool_batch", "known_p"):
                    book = PairBook(456, budget=method["budget"], strategy=method["kind"])
                    hook = functools.partial(coupled_noise, partition=partition)
                elif method["kind"] == "raw":
                    book, hook = AnchoredLedger(2, random.Random(456)), raw_noise
                model = Head()
                pair = []
                for label in range(method["K"]):
                    sample = decode(
                        model,
                        tokenizer,
                        torch.tensor([[2, 3]], device=model.device),
                        1,
                        grammar,
                        lex,
                        t["lexical"],
                        config,
                        0.0 if method["kind"] == "mixed" and label else temperature,
                        seed + label * config["torch_seed_label_offset"],
                        book=book,
                        label=label,
                        mode=method.get("mode"),
                        namespace=("fake-numeric-wrapper", temperature),
                        coordinate="first",
                        hook=hook,
                        additional_stuff=additional,
                    )
                    parsed = sample.pop("parsed")
                    if parsed is None or set(parsed) != {"answer"}:
                        raise AssertionError((method["id"], temperature, sample))
                    pair.append(sample)
                first = fingerprint(pair[0])
                if first != references.setdefault(temperature, first):
                    raise AssertionError("wrapper changed first native trajectory")
                rows.append(
                    dict(method=method["id"], temperature=temperature, first_equal=True, pair=pair)
                )
    result = dict(
        scope="FAKE 126337-ID head; full wrapper, not neural/timing evidence",
        rows=rows,
        sources={p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in here.glob("*.py")},
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    print(
        json.dumps(
            dict(checks=len(rows), first_equal=len(rows), samples=sum(len(r["pair"]) for r in rows))
        )
    )


if __name__ == "__main__":
    main()
