"""Native EPIC decoding helpers copied from pinned A31 0a27a24; isolated."""

import hashlib
import json
import time
from collections import OrderedDict
from contextlib import nullcontext
from types import SimpleNamespace

import torch
from constrained_diffusion.constrain_utils import (
    EOS,
    autocomplete_valid,
    generated_language,
    partial_output_from_tokens,
)
from constrained_diffusion.eval.dllm.models.llada import generate_constrained as native

from .native_state import ModelHistory
from .numeric_task import strict_json

MASK = 126336


class CachedModel:
    def __init__(self, model, limit):
        self.model, self.device, self.limit = model, model.device, limit
        self.clear()

    def clear(self):
        self.cache = OrderedDict()
        self.bytes = 0
        self.queries = 0
        self.forwards = 0
        self.forward_wall = 0.0
        self.head_digests = []

    def __call__(self, inputs):
        self.queries += 1
        key = inputs.detach().cpu().numpy().tobytes()
        if key in self.cache:
            self.cache.move_to_end(key)
            return SimpleNamespace(logits=self.cache[key].to(self.device).clone())
        torch.cuda.synchronize()
        start = time.perf_counter()
        result = self.model(inputs)
        torch.cuda.synchronize()
        self.forward_wall += time.perf_counter() - start
        self.forwards += 1
        head = result.logits.detach().cpu()
        size = head.numel() * head.element_size()
        self.head_digests.append(
            (
                hashlib.sha256(key).hexdigest(),
                hashlib.sha256(head.view(torch.uint8).numpy().tobytes()).hexdigest(),
            )
        )
        while self.cache and self.bytes + size > self.limit:
            _, old = self.cache.popitem(last=False)
            self.bytes -= old.numel() * old.element_size()
        if size <= self.limit:
            self.cache[key] = head
            self.bytes += size
        return result


class TraceModel(ModelHistory):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.trace = hashlib.sha256()

    def __call__(self, ids, *args, **kwargs):
        self.trace.update(ids.detach().cpu().numpy().tobytes())
        return super().__call__(ids, *args, **kwargs)


def decode(
    model,
    tokenizer,
    ids,
    chat_len,
    grammar,
    lex,
    rules,
    config,
    temperature,
    seed,
    book=None,
    label=0,
    mode=None,
    coordinate="first",
    namespace=None,
    hook=None,
    additional_stuff=None,
):
    torch.manual_seed(seed)
    before_queries, before_forwards = model.queries, model.forwards
    proxy = TraceModel(model, namespace, mode=mode) if mode else model
    context = (
        hook(native, proxy, book, label, mask_id=MASK, coordinate=coordinate)
        if mode
        else nullcontext()
    )
    torch.cuda.synchronize()
    start = time.perf_counter()
    cpu = time.process_time()
    status = "incomplete"
    error = None
    complete = False
    recovery = "not_needed"
    last = torch.cat(
        (ids, torch.full((1, config["gen_length"]), MASK, device=model.device, dtype=torch.long)),
        dim=1,
    )
    rejected = []
    try:
        with context:
            for event in native.generate(
                proxy,
                ids,
                tokenizer,
                grammar,
                lex,
                prompt_len=chat_len,
                gen_length=config["gen_length"],
                block_length=config["block_length"],
                steps=config["steps"],
                temperature=temperature,
                mask_id=MASK,
                constrain=True,
                max_resamples=config["max_resamples"],
                additional_stuff=additional_stuff,
                strip_chars=None,
            ):
                tokens, rejected, complete = event
                last = tokens.clone()
        output_ids = last[0, chat_len:].tolist()
        text = tokenizer.decode(output_ids, skip_special_tokens=True)
        try:
            parsed = strict_json(text)
        except (ValueError, TypeError):
            words = [
                None
                if t == MASK
                else EOS
                if t in (126081, 126348)
                else tokenizer.decode([t], clean_up_tokenization_spaces=False)
                for t in output_ids
            ]
            partial, gap, eos_adj = partial_output_from_tokens(words, None)
            text = autocomplete_valid(
                partial_output=partial,
                first_token_gap=gap,
                last_token_eos_adj=eos_adj,
                generated_lang=generated_language(words, lex, grammar.get_terminals()),
                lex_map=rules,
                subtokens={},
                constraint_lang=grammar,
            )
            recovery = "recovered" if text is not None else "no_completion"
            parsed = strict_json(text) if text is not None else None
        status = "valid_json" if parsed is not None else "incomplete"
    except Exception as exc:
        text = ""
        parsed = None
        output_ids = last[0, chat_len:].tolist()
        status = "error"
        error = {"type": type(exc).__name__, "message": str(exc)}
    torch.cuda.synchronize()
    return dict(
        status=status,
        error=error,
        output=text,
        parsed=parsed,
        original_ids_sha256=hashlib.sha256(json.dumps(output_ids).encode()).hexdigest(),
        wall=time.perf_counter() - start,
        cpu=time.process_time() - cpu,
        queries=model.queries - before_queries,
        forwards=model.forwards - before_forwards,
        native_complete=bool(complete),
        rejections=len(rejected),
        recovery=recovery,
    )
