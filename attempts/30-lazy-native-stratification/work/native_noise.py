"""Opt-in, serial research hook; original EPIC files and policy stay intact."""

import hashlib
import inspect
from contextlib import contextmanager

from .ledger import cpu_double, cuda_double

PINNED_NOISE_SHA256 = "861d0c0c45b706d5f733da0b654eccc1e6f4eff8c5804614d488acf223782035"
PINNED_GENERATE_SHA256 = "d31ced257513dfdd5f4af350e07cfad11cadf1aec78bc5ad987c18539e4baabb"


class ModelHistory:
    """Retain full input histories, rather than merging equal current canvases.

    One proxy per label; immutable batch namespace must include model, grammar,
    tokenizer and ALL decoder settings. Model is frozen/eval and receives the
    same inputs as native EPIC. Capturing histories adds CPU transfers/cost.
    """

    def __init__(self, model, namespace):
        hash(namespace)
        self.model, self.namespace, self.history, self.inputs = model, namespace, (), None

    def __getattr__(self, name):
        return getattr(self.model, name)

    def __call__(self, input_ids, *args, **kwargs):
        if args or kwargs:
            raise ValueError("audited native model boundary accepts only input_ids")
        rows = tuple(tuple(row) for row in input_ids.detach().cpu().tolist())
        self.inputs = rows
        self.history = (*self.history, ("forward", rows))
        return self.model(input_ids)


@contextmanager
def coupled_noise(module, proxy, book, label, *, mask_id, coordinate="entropy"):
    """Temporarily substitute one raw uniform coordinate, preserving all ranks.

    Supported profile: PyTorch2.8.0 CPU/CUDA float64 native noise. No threads or
    concurrent decoder in this process while the hook is installed. Callers
    MUST consume the native generator inside this context. Ledger is fixed-K
    and fresh per batch. Namespace/settings are identical for all labels.
    """
    import torch

    if torch.__version__.split("+")[0] != "2.8.0":
        raise ValueError("unaudited PyTorch uniform-double profile")
    if coordinate not in ("first", "entropy"):
        raise ValueError("coordinate rule must be declared before measuring")
    original = module.add_gumbel_noise
    source = inspect.getsource(original).encode()
    if hashlib.sha256(source).hexdigest() != PINNED_NOISE_SHA256:
        raise ValueError("native noise source differs from the pinned baseline")
    if (
        hashlib.sha256(inspect.getsource(module.generate).encode()).hexdigest()
        != PINNED_GENERATE_SHA256
    ):
        raise ValueError("native decoder control flow differs from the pinned baseline")
    decoder_code = inspect.unwrap(module.generate).__code__
    if type(label) is not int or not 0 <= label < book.size:
        raise ValueError("label outside fixed batch")

    def noise(logits, temperature):
        if temperature == 0:
            return original(logits, temperature)
        if not proxy.history or logits.ndim != 3 or logits.shape[0] != 1:
            raise ValueError("unrecorded/unsupported native noise boundary")
        profile = logits.device.type
        if profile not in ("cpu", "cuda"):
            raise ValueError("unaudited device uniform-double profile")
        caller = inspect.currentframe().f_back
        try:
            if caller.f_code is not decoder_code:
                raise ValueError("noise hook called outside audited native decoder")
            state = caller.f_locals
            words = tuple(("EOS",) if w is module.EOS else w for w in state["generated_words"])
            policy = tuple(
                state[name]
                for name in (
                    "gen_length",
                    "block_length",
                    "steps",
                    "cfg_scale",
                    "remasking",
                    "mask_id",
                    "prompt_len",
                    "max_resamples",
                    "constrain",
                    "inject_gap_size",
                    "max_total_injections",
                    "prelex",
                    "strip_chars",
                )
            )
            checkpoint = (
                state["num_block"],
                state["i"],
                bool(state["complete"]),
                words,
                tuple(int(pos) for pos, _time in state["resamples"]),
                tuple(tuple(row) for row in state["num_transfer_tokens"].cpu().tolist()),
                policy,
            )
        finally:
            del caller
        proxy.history = (*proxy.history, ("noise", checkpoint))
        rows = proxy.inputs
        positions = [i for i, token in enumerate(rows[0]) if token == mask_id]
        if not positions:
            return original(logits, temperature)
        values = logits.to(torch.float64)
        if coordinate == "entropy":
            probs = torch.softmax(values[0, positions], dim=-1)
            entropy = torch.special.entr(probs).sum(dim=-1)
            if not bool(torch.isfinite(entropy).all()):
                raise ValueError("nonfinite entropy at native noise boundary")
            pos = positions[int(torch.argmax(entropy).item())]
        else:
            pos = positions[0]
        token = int(torch.argmax(values[0, pos]).item())
        key = (proxy.namespace, proxy.history, profile, temperature, coordinate, pos, token)
        ticket = book.draw(key, label, 2**53)
        raw = cuda_double(ticket) if profile == "cuda" else cpu_double(ticket)
        uniforms = torch.rand_like(values, dtype=torch.float64)
        uniforms[0, pos, token] = raw
        # Same operations as the untouched add_gumbel_noise. Rejected tokens
        # still use the same whole noisy tensor during native recovery.
        gumbel_noise = (-torch.log(uniforms)) ** temperature
        return values.exp() / gumbel_noise

    module.add_gumbel_noise = noise
    try:
        yield
    finally:
        module.add_gumbel_noise = original
