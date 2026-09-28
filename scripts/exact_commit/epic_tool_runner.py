"""Instrument the pinned upstream generator; never replace its selection logic."""

from __future__ import annotations

import hashlib
import os
import signal
import time
from types import SimpleNamespace


class DecodeLimit(RuntimeError):
    pass


def run_epic(*, model, tokenizer, prompt, grammar, rows, calls, config, method):
    import torch
    from constrained_diffusion.constrain_utils import compile_lex_map
    from constrained_diffusion.eval.dllm.models.llada import generate_constrained as upstream
    from rustformlang.cfg import CFG

    from mwpc_research.tool_parser import epic_byte_grammar, epic_lexical_grammar
    from mwpc_research.tool_screen import normalize_tool_call

    def synchronize():
        if torch.device(model.device).type == "cuda":
            torch.cuda.synchronize()

    restricted = method.startswith("epic_domains_")
    steps = int(method.rsplit("_", 1)[1])
    settings = {
        "CONSTRAINED_DIFFUSION_REGULAR_COVER_BATCH": "1",
        "CONSTRAINED_DIFFUSION_REGULAR_COVER_MIN_BATCH": "2",
        "CONSTRAINED_DIFFUSION_REGULAR_COVER_EXACT": "1",
        "CONSTRAINED_DIFFUSION_DFA_FREE_CHECKER": "1",
    }
    saved_env = {k: os.environ.get(k) for k in settings}
    os.environ.update(settings)
    original_selector = upstream.select_batch_with_regular_cover
    original_check = upstream.check_valid
    prior_handler = signal.getsignal(signal.SIGALRM)
    counters = {"batch_calls": 0, "batch_selected": 0, "check_calls": 0}
    times = {
        "batch_seconds": 0.0,
        "check_seconds": 0.0,
        "forward_seconds": 0.0,
        "domain_mask_seconds": 0.0,
    }
    batch_errors = []
    events = []
    forwards = []
    resamples = []
    failure = None
    status = "incomplete"
    setup_start = time.perf_counter()
    lexical = method.startswith("epic_lexical_")
    cfg_text, cfg_start, lex_rules = (
        epic_lexical_grammar(calls) if lexical else epic_byte_grammar(grammar)
    )
    native_grammar = CFG.from_text(cfg_text, cfg_start).to_normal_form()
    if lexical:
        # Initialize the normal-form cache on the grammar returned by normalization.
        native_grammar = native_grammar.to_normal_form()
    lex_map = compile_lex_map(lex_rules)
    prompt_tensor = torch.tensor([prompt], device=model.device)
    permitted = None
    if restricted:
        permitted = torch.zeros(
            (len(rows), model.config.vocab_size), device=model.device, dtype=torch.bool
        )
        for position, row in enumerate(rows):
            permitted[position, row] = True
    synchronize()
    setup_seconds = time.perf_counter() - setup_start

    class ObservedModel:
        device = model.device

        def __call__(self, tokens):
            if len(forwards) >= config["max_forwards"]:
                raise DecodeLimit("forward_limit")
            synchronize()
            begin = time.perf_counter()
            with torch.no_grad():
                logits = model(tokens).logits
            synchronize()
            seconds = time.perf_counter() - begin
            times["forward_seconds"] += seconds
            forwards.append({"canvas": tokens[0, len(prompt) :].tolist(), "seconds": seconds})
            if permitted is not None:
                begin = time.perf_counter()
                logits[:, len(prompt) :].masked_fill_(~permitted, -torch.inf)
                synchronize()
                times["domain_mask_seconds"] += time.perf_counter() - begin
            return SimpleNamespace(logits=logits)

    def observe_selector(*args, **kwargs):
        counters["batch_calls"] += 1
        begin = time.perf_counter()
        try:
            result = original_selector(*args, **kwargs)
            counters["batch_selected"] += len(result)
            return result
        except Exception as exc:
            # Upstream may catch this and fall back; preserve the diagnostic.
            batch_errors.append({"type": type(exc).__name__, "message": str(exc)})
            raise
        finally:
            times["batch_seconds"] += time.perf_counter() - begin

    def observe_check(*args, **kwargs):
        counters["check_calls"] += 1
        begin = time.perf_counter()
        try:
            return original_check(*args, **kwargs)
        finally:
            times["check_seconds"] += time.perf_counter() - begin

    def deadline(*_):
        raise DecodeLimit("timeout")

    upstream.select_batch_with_regular_cover = observe_selector
    upstream.check_valid = observe_check
    signal.signal(signal.SIGALRM, deadline)
    start = time.perf_counter()
    signal.setitimer(signal.ITIMER_REAL, config["max_generation_seconds"])
    last = [126336] * config["slots"]
    try:
        for tokens, rejected, complete in upstream.generate(
            ObservedModel(),
            prompt_tensor,
            tokenizer,
            native_grammar,
            lex_map,
            prompt_len=len(prompt),
            steps=steps,
            gen_length=config["slots"],
            block_length=config["slots"],
            temperature=0.0,
            cfg_scale=0.0,
            remasking="low_confidence",
            mask_id=126336,
            trace=False,
            constrain=True,
            max_resamples=config["epic_max_resamples"],
        ):
            last = tokens[0, len(prompt) :].tolist()
            resamples = list(rejected)
            events.append(
                {
                    "canvas": last,
                    "complete": bool(complete),
                    "resamples": len(resamples),
                    "forwards": len(forwards),
                }
            )
            if complete:
                status = "complete"
        if status != "complete" and len(resamples) >= config["epic_max_resamples"]:
            status = "resample_limit"
    except DecodeLimit as exc:
        status = str(exc)
    except Exception as exc:
        status = "error"
        failure = {"type": type(exc).__name__, "message": str(exc)}
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, prior_handler)
        upstream.select_batch_with_regular_cover = original_selector
        upstream.check_valid = original_check
        for key, value in saved_env.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value
    synchronize()
    elapsed = time.perf_counter() - start
    decoded = tokenizer.decode(last, skip_special_tokens=True)
    normalized = normalize_tool_call(decoded)
    return {
        "status": status,
        "failure": failure,
        "output": decoded,
        "normalized_output": normalized,
        "syntax_valid": status == "complete" and normalized in calls,
        "token_emissions": {
            str(t): list(tokenizer.decode([t], clean_up_tokenization_spaces=False).encode())
            for t in sorted(set(last))
            if t not in (126081, 126336)
        },
        "forwards": len(forwards),
        "elapsed_excluding_shadow_seconds": elapsed,
        "elapsed_with_diagnostics_seconds": elapsed,
        "epic_setup_seconds": setup_seconds,
        "epic_environment": settings,
        "epic_steps": steps,
        "implementation": "pinned_upstream_llada_generate_with_observation_hooks",
        "exactness_scope": "not_applicable: upstream abstract gaps, no finite-support optimum",
        "proposal_support": "same_positional_domains" if restricted else "native_vocabulary",
        "confidence_policy": "softmax_after_domain_mask" if restricted else "upstream_native",
        "epic_grammar_sha256": hashlib.sha256(cfg_text.encode()).hexdigest(),
        "epic_lex_rules": lex_rules,
        "epic_representation": "lexical" if lexical else "bytes",
        "epic_counters": counters,
        "epic_times": times,
        "epic_batch_errors": batch_errors,
        "epic_events": events,
        "epic_forwards": forwards,
        "epic_resamples": resamples,
        "token_ids": last,
        "solver_status_counts": {status: 1},
        "trace": [],
    }
