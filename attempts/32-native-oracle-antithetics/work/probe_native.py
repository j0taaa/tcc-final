"""Literal native first trajectory and RNG isolation, FAKE heads only."""

import argparse
import hashlib
import itertools
import json
from pathlib import Path

import torch
from constrained_diffusion.constrain_utils import compile_lex_map
from rustformlang.cfg import CFG

from .native_fixture import TinyHead, consume, native
from .native_noise import PairBook, coupled_noise
from .native_state import ModelHistory


def probe(device, seed, temperature, coordinate, max_resamples, mode):
    grammar = CFG.from_text("S -> lexNumber", "S").to_normal_form()
    lexical = compile_lex_map({"lexNumber": "(0|1)"})
    settings = {"temperature": temperature, "max_resamples": max_resamples}
    torch.manual_seed(seed)
    baseline = TinyHead(device)
    reference = consume(baseline, grammar, lexical, settings)
    book = PairBook(seed + 32032)
    namespace = ("A32-fake-native", tuple(settings.items()))
    outputs, counts = [], []
    saved = native.add_gumbel_noise
    for label in (0, 1):
        torch.manual_seed(seed + label * 101)
        proxy = ModelHistory(TinyHead(device), namespace, mode=mode)
        with coupled_noise(native, proxy, book, label, mask_id=5, coordinate=coordinate):
            outputs.append(consume(proxy, grammar, lexical, settings))
        counts.append(proxy.calls)
    if outputs[0] != reference or counts[0] != len(baseline.calls):
        raise AssertionError("literal first path changed")
    if native.add_gumbel_noise is not saved:
        raise AssertionError("native hook leaked")
    # Explicitly verify the auxiliary native row draws restore caller streams.
    before_cpu = torch.random.get_rng_state().clone()
    before_device = torch.cuda.get_rng_state(device).clone() if device == "cuda" else before_cpu
    with book.auxiliary(torch.device(device)):
        torch.rand(17, device=device)
    after_device = (
        torch.cuda.get_rng_state(device) if device == "cuda" else torch.random.get_rng_state()
    )
    if not torch.equal(before_device, after_device) or not torch.equal(
        before_cpu, torch.random.get_rng_state()
    ):
        raise AssertionError("auxiliary noise changed caller RNG stream")
    return dict(
        device=device,
        seed=seed,
        temperature=temperature,
        coordinate=coordinate,
        max_resamples=max_resamples,
        mode=mode,
        first_equal=True,
        rng_isolated=True,
        reference_fake_calls=len(baseline.calls),
        pair_fake_calls=counts,
        complete=[bool(x[-1][2]) for x in outputs],
        rejections=[len(x[-1][1]) for x in outputs],
        shared=book.shared,
        extra_draws=book.extra_draws,
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise SystemExit("refuse to overwrite evidence")
    rows = [
        probe(*x)
        for x in itertools.product(
            ("cpu", "cuda"),
            range(3),
            (0.0, 0.5, 1.0),
            ("first", "entropy"),
            (1, 8),
            ("state", "history", "root"),
        )
    ]
    result = dict(
        scope=(
            "FAKE heads; literal first IDs/recovery/EOS/rejections, "
            "RNG isolation; NOT neural benefit"
        ),
        torch=torch.__version__,
        rows=rows,
        sources={
            p.name: hashlib.sha256(p.read_bytes()).hexdigest()
            for p in Path(__file__).parent.glob("*.py")
        },
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    print(
        json.dumps(
            dict(
                checks=len(rows),
                first_equal=sum(r["first_equal"] for r in rows),
                shared=sum(r["shared"] for r in rows),
                auxiliary_draws=sum(r["extra_draws"] for r in rows),
                fake_calls=sum(r["reference_fake_calls"] + sum(r["pair_fake_calls"]) for r in rows),
            )
        )
    )


if __name__ == "__main__":
    main()
