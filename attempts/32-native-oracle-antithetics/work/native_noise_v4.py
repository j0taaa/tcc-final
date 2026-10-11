"""A32v4 numerical-prefix walk/pool/approximate known-p native controls."""

import hashlib
import inspect
import random
from contextlib import contextmanager

from .pool import repair as pool_repair
from .walk import repair

NOISE_SHA = "861d0c0c45b706d5f733da0b654eccc1e6f4eff8c5804614d488acf223782035"
GENERATE_SHA = "d31ced257513dfdd5f4af350e07cfad11cadf1aec78bc5ad987c18539e4baabb"


class PairBook:
    """One serial two-label batch; auxiliary Torch stream is kept separate."""

    def __init__(self, seed, *, budget, strategy="walk"):
        if strategy not in ("walk", "pool", "pool_batch", "known_p"):
            raise ValueError("unknown repair strategy")
        self.strategy = strategy
        self.rng = random.Random(seed + 33033)
        if type(budget) is not int or budget < 2:
            raise ValueError("integer total row budget>=2 required")
        self.budget = budget
        self.seed = seed
        self.tables, self.aux_states = {}, {}
        self.shared, self.extra_draws = 0, 0

    @contextmanager
    def auxiliary(self, device):
        import torch

        if device.type == "cuda" and device.index is None:
            device = torch.device("cuda", torch.cuda.current_device())
        key = (device.type, device.index)
        devices = [device.index] if device.type == "cuda" else []
        with torch.random.fork_rng(devices=devices):
            if key not in self.aux_states:
                self.aux_states[key] = (
                    torch.Generator(device=device).manual_seed(self.seed).get_state()
                )
            if device.type == "cuda":
                torch.cuda.set_rng_state(self.aux_states[key], device)
            else:
                torch.random.set_rng_state(self.aux_states[key])
            try:
                yield
            finally:
                self.aux_states[key] = (
                    torch.cuda.get_rng_state(device)
                    if device.type == "cuda"
                    else torch.random.get_rng_state()
                )


@contextmanager
def coupled_noise(module, proxy, book, label, *, mask_id, partition, coordinate="first"):
    import torch

    if torch.__version__.split("+")[0] != "2.8.0":
        raise ValueError("unaudited native Torch profile")
    if type(label) is not int or label not in (0, 1):
        raise ValueError("two distinct labels required")
    if coordinate not in ("first", "entropy"):
        raise ValueError("predeclared position rule required")
    original = module.add_gumbel_noise
    if hashlib.sha256(inspect.getsource(original).encode()).hexdigest() != NOISE_SHA:
        raise ValueError("native noise source mismatch")
    if hashlib.sha256(inspect.getsource(module.generate).encode()).hexdigest() != GENERATE_SHA:
        raise ValueError("native decoder source mismatch")
    decoder = inspect.unwrap(module.generate).__code__

    def noise(logits, temperature):
        if temperature == 0 or (proxy.mode == "root" and proxy.noise_calls):
            return original(logits, temperature)
        if logits.ndim != 3 or logits.shape[0] != 1 or proxy.inputs is None:
            raise ValueError("unsupported native boundary")
        if logits.device.type not in ("cpu", "cuda"):
            raise ValueError("unsupported native device")
        caller = inspect.currentframe().f_back
        try:
            if caller.f_code is not decoder:
                raise ValueError("outside guarded decoder")
            state = caller.f_locals
            checkpoint = (
                state["num_block"],
                state["i"],
                bool(state["complete"]),
                tuple(("EOS",) if w is module.EOS else w for w in state["generated_words"]),
                len(state["resamples"]),
                tuple(tuple(row) for row in state["num_transfer_tokens"].cpu().tolist()),
                tuple(
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
                ),
            )
            historical = (
                *checkpoint[:4],
                tuple(int(pos) for pos, _ in state["resamples"]),
                *checkpoint[5:],
            )
        finally:
            del caller
        if proxy.mode == "history":
            proxy.history = (*proxy.history, ("noise", historical))
        positions = [i for i, token in enumerate(proxy.inputs[0]) if token == mask_id]
        if not positions:
            return original(logits, temperature)
        values = logits.to(torch.float64)
        if coordinate == "entropy":
            entropies = torch.special.entr(torch.softmax(values[0, positions], dim=-1)).sum(-1)
            if not bool(torch.isfinite(entropies).all()):
                raise ValueError("nonfinite entropy")
            pos = positions[int(entropies.argmax())]
        else:
            pos = positions[0]
        cutoff, project, approximate_p = partition.split(values[0, pos], temperature)
        node = proxy.history if proxy.mode == "history" else (proxy.calls, proxy.inputs, checkpoint)
        key = (
            proxy.namespace,
            proxy.mode,
            node,
            logits.device.type,
            temperature,
            coordinate,
            pos,
            cutoff,
            partition.signature,
        )
        # Literal untouched source draw; first label retains every bit/rank.
        result = original(logits, temperature)

        if key not in book.tables:
            book.tables[key] = (label, project(result[0, pos]))
        else:
            prior, first_class = book.tables[key]
            if prior == label:
                raise ValueError("repeated node within one trajectory")
            book.shared += 1
            with book.auxiliary(logits.device):

                def draw():
                    return original(values[0, pos].view(1, 1, -1), temperature)[0, 0]

                if book.strategy == "walk":
                    row, count = repair(
                        first_class, result[0, pos], draw, project, budget=book.budget
                    )
                elif book.strategy in ("pool", "pool_batch"):
                    if book.strategy == "pool_batch" and book.budget > 2:
                        batch = original(
                            values[0, pos].expand(1, book.budget - 2, -1), temperature
                        )[0]
                        rows = iter(batch)
                        draw = rows.__next__
                    row, count = pool_repair(
                        first_class,
                        result[0, pos],
                        draw,
                        project,
                        book.rng.randrange,
                        budget=book.budget,
                    )
                else:
                    # Competent density-aware control: ideal continuous PL
                    # estimate; NOT claimed exact for native finite rounding.
                    mass = approximate_p if first_class else 1 - approximate_p
                    flip_probability = min(approximate_p, 1 - approximate_p) / mass if mass else 1.0
                    desired = (
                        not first_class if book.rng.random() < flip_probability else first_class
                    )
                    row, count = result[0, pos], 0
                    while project(row) != desired and count < book.budget - 2:
                        row, count = draw(), count + 1
                    if project(row) != desired:
                        raise RuntimeError("known-p conditional row budget refusal")
            result[0, pos] = row
            book.extra_draws += count
        proxy.noise_calls += 1
        return result

    module.add_gumbel_noise = noise
    try:
        yield
    finally:
        module.add_gumbel_noise = original
