"""A31 derivative of frozen A30: sufficient-state/history/root noise controls."""

import hashlib
import inspect
from contextlib import contextmanager

from .ledger import cpu_double, cuda_double

PINNED_NOISE_SHA256 = "861d0c0c45b706d5f733da0b654eccc1e6f4eff8c5804614d488acf223782035"
PINNED_GENERATE_SHA256 = "d31ced257513dfdd5f4af350e07cfad11cadf1aec78bc5ad987c18539e4baabb"


class ModelHistory:
    """Capture sufficient current input or preserve the full-history control.

    One proxy per label; immutable batch namespace must include model, grammar,
    tokenizer and ALL decoder settings. Model is frozen/eval and receives the
    same inputs as native EPIC. Capturing histories adds CPU transfers/cost.
    """

    def __init__(self, model, namespace, *, mode="state"):
        hash(namespace)
        if mode not in ("state", "history", "root"):
            raise ValueError("unknown native coordination mode")
        self.model, self.namespace, self.history, self.inputs = model, namespace, (), None
        self.mode, self.calls, self.noise_calls = mode, 0, 0

    def __getattr__(self, name):
        return getattr(self.model, name)

    def __call__(self, input_ids, *args, **kwargs):
        if args or kwargs:
            raise ValueError("audited native model boundary accepts only input_ids")
        if self.mode != "root" or self.calls == 0:
            self.inputs = tuple(tuple(row) for row in input_ids.detach().cpu().tolist())
        if self.mode == "history":
            self.history = (*self.history, ("forward", self.inputs))
        self.calls += 1
        return self.model(input_ids)


@contextmanager
def coupled_noise(module, proxy, book, label, *, mask_id, coordinate="entropy"):
    """Temporarily substitute one raw uniform coordinate, preserving all ranks.

    Supported profile: PyTorch2.8.0 CPU/CUDA float64 native noise. No threads or
    concurrent decoder in this process while the hook is installed. Callers
    MUST consume the native generator inside this context. Ledger is fixed-K
    and fresh per batch. Namespace/settings are identical for all labels.
    State mode only claims score/coverage for final IDs/JSON and status, not
    historical diagnostic rejection lists. Per-label paths stay native.
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
        if proxy.mode == "root" and proxy.noise_calls:
            return original(logits, temperature)
        if proxy.inputs is None or logits.ndim != 3 or logits.shape[0] != 1:
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
        if proxy.mode == "history":
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
        if proxy.mode == "history":
            node = proxy.history
        else:
            # Native future control only uses len(resamples), not old rejected
            # positions/timestamps. They remain native diagnostics, outside
            # the terminal JSON/ID score contract. Phase is NEVER omitted.
            state = (*checkpoint[:4], len(checkpoint[4]), *checkpoint[5:])
            # Also retain the per-label native query ordinal: external forward
            # budgets may use it, and it strictly separates repeated phases.
            node = (proxy.calls, rows, state)
        key = (proxy.namespace, proxy.mode, node, profile, temperature, coordinate, pos, token)
        ticket = book.draw(key, label, 2**53)
        proxy.noise_calls += 1
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
