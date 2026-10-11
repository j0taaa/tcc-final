"""Opt-in literal EPIC + anchored controls on frozen external JSON inputs."""

import argparse
import hashlib
import json
import os
import random
import time
from collections import OrderedDict
from contextlib import nullcontext
from pathlib import Path
from types import SimpleNamespace

import torch
from constrained_diffusion.constrain_utils import (
    EOS,
    autocomplete_valid,
    compile_lex_map,
    generated_language,
    partial_output_from_tokens,
)
from constrained_diffusion.eval.dllm.models.llada import generate_constrained as native
from rustformlang.cfg import CFG

from .anchored_ledger import AnchoredLedger
from .native_noise_v3 import ModelHistory, coupled_noise
from .official_checker import load_checker, strict_json
from .schema_task import task

HERE = Path(__file__).parent
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


class ObservedLedger(AnchoredLedger):
    def __init__(self, *args):
        super().__init__(*args)
        self.visitors = {}
        self.extra_reunions = 0
        self.shared = 0

    def observe(self, proxy, key, checkpoint):
        proxy.trace.update(repr(checkpoint).encode())
        digest = proxy.trace.digest()
        if key in self.visitors:
            self.shared += 1
            self.extra_reunions += digest != self.visitors[key]
        else:
            self.visitors[key] = digest


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
):
    torch.manual_seed(seed)
    before_queries, before_forwards = model.queries, model.forwards
    proxy = TraceModel(model, namespace, mode=mode) if mode else model
    context = (
        coupled_noise(native, proxy, book, label, mask_id=MASK, coordinate=coordinate)
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


def main():
    from transformers import AutoModel, AutoTokenizer, BitsAndBytesConfig

    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--pilot", action="store_true")
    args = parser.parse_args()
    if args.output.exists():
        raise SystemExit("refuse to overwrite prior evidence")
    config = json.loads((HERE / "protocol-v3.json").read_text())
    manifest = json.loads((HERE / "external-inputs-v3.json").read_text())
    if (
        hashlib.sha256((HERE / "external-inputs-v3.json").read_bytes()).hexdigest()
        != config["inputs_sha256"]
    ):
        raise ValueError("frozen input mismatch")
    gold = {
        r["id"]: r["ground_truth"]
        for r in map(
            json.loads,
            Path(".cache/a31-bfcl-inputs/answers-simple-python.json").read_text().splitlines(),
        )
    }
    check = load_checker(Path(".cache/a31-bfcl-inputs/ast_checker.py"))
    os.environ.update(config["native_env"])
    torch.set_num_threads(config["cpu_threads"])
    tokenizer = AutoTokenizer.from_pretrained(
        config["model_id"], revision=config["revision"], local_files_only=True
    )
    actual = AutoModel.from_pretrained(
        config["model_id"],
        revision=config["revision"],
        local_files_only=True,
        trust_remote_code=True,
        torch_dtype=torch.bfloat16,
        device_map={"": 0},
        quantization_config=BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_use_double_quant=True,
            bnb_4bit_compute_dtype=torch.bfloat16,
        ),
    ).eval()
    if actual.config._commit_hash != config["revision"]:
        raise ValueError("model revision mismatch")
    model = CachedModel(actual, config["cache_bytes"])
    args.output.parent.mkdir(parents=True, exist_ok=True)
    sources = {f.name: hashlib.sha256(f.read_bytes()).hexdigest() for f in HERE.glob("*.py")}
    meta = {
        "phase": "pilot-development" if args.pilot else "development",
        "torch": torch.__version__,
        "hardware": torch.cuda.get_device_name(),
        "sources": sources,
        "config": config,
        "scope": "real LLaDA NF4 + native EPIC; all outputs/statuses; no heldout confirmation",
    }
    args.output.with_suffix(".metadata.json").write_text(json.dumps(meta, indent=2) + "\n")
    seeds = config["development_seeds"][:1] if args.pilot else config["development_seeds"]
    with torch.no_grad(), args.output.open("x") as stream:
        for record in manifest["development"]:
            begin = time.perf_counter()
            begin_cpu = time.process_time()
            t = task(record)
            grammar = CFG.from_text(t["grammar"], "S").to_normal_form()
            lex = compile_lex_map(t["lexical"])
            chat = tokenizer.apply_chat_template(
                [{"role": "user", "content": t["instruction"]}],
                add_generation_prompt=True,
                tokenize=True,
            )
            all_ids = chat + tokenizer.encode(t["prefix"], add_special_tokens=False)
            setup_wall, setup_cpu = time.perf_counter() - begin, time.process_time() - begin_cpu
            if len(all_ids) > config["max_prompt_tokens"]:
                stream.write(
                    json.dumps(
                        {
                            "id": record["id"],
                            "status": "prompt_budget_refusal",
                            "prompt_tokens": len(all_ids),
                        }
                    )
                    + "\n"
                )
                stream.flush()
                continue
            ids = torch.tensor([all_ids], device=model.device)
            for seed in seeds:
                for temperature in [0.0, *config["temperatures"]]:
                    if temperature == 0 and seed != seeds[0]:
                        continue
                    for coordinate in config["coordinates"]:
                        if temperature == 0 and coordinate != "first":
                            continue
                        first_ids = None
                        for method in config["methods"]:
                            if temperature == 0 and method != "iid":
                                continue
                            pair_begin = time.perf_counter()
                            pair_cpu = time.process_time()
                            model.clear()
                            torch.cuda.reset_peak_memory_stats()
                            book = ObservedLedger(
                                2, random.Random(seed + config["ledger_seed_offset"])
                            )
                            namespace = (
                                record["id"],
                                t["grammar_sha256"],
                                tuple(config["native_env"].items()),
                                config["revision"],
                                temperature,
                                coordinate,
                            )
                            pair = [
                                decode(
                                    model,
                                    tokenizer,
                                    ids,
                                    len(chat),
                                    grammar,
                                    lex,
                                    t["lexical"],
                                    config,
                                    temperature,
                                    seed + label * config["torch_seed_second_offset"],
                                    book,
                                    label,
                                    None if method == "iid" else method,
                                    coordinate,
                                    namespace,
                                )
                                for label in range(1 if temperature == 0 else 2)
                            ]
                            verification = time.perf_counter()
                            verification_cpu = time.process_time()
                            for sample in pair:
                                try:
                                    sample["correct"] = bool(
                                        sample["parsed"] is not None
                                        and check(
                                            record["function"][0],
                                            sample["parsed"],
                                            gold[record["id"]],
                                        )
                                    )
                                except Exception as exc:
                                    sample["correct"] = False
                                    sample["verifier_error"] = str(exc)
                                sample.pop("parsed")
                            verifier_wall = time.perf_counter() - verification
                            verifier_cpu = time.process_time() - verification_cpu
                            if first_ids is None:
                                first_ids = pair[0]["original_ids_sha256"]
                            equal = pair[0]["original_ids_sha256"] == first_ids
                            row = dict(
                                id=record["id"],
                                method="deterministic" if temperature == 0 else method,
                                seed=seed,
                                temperature=temperature,
                                coordinate=coordinate,
                                pair=pair,
                                first_equal=equal,
                                extra_reunions=book.extra_reunions,
                                shared_nodes=book.shared,
                                prepare_wall=setup_wall,
                                prepare_cpu=setup_cpu,
                                verifier_wall=verifier_wall,
                                verifier_cpu=verifier_cpu,
                                forward_seconds=model.forward_wall,
                                head_digests=model.head_digests,
                                pass2=any(s["correct"] for s in pair),
                            )
                            row["peak_cuda_bytes"] = torch.cuda.max_memory_allocated()
                            model.clear()
                            row["full_wall"] = setup_wall + time.perf_counter() - pair_begin
                            row["full_cpu"] = setup_cpu + time.process_time() - pair_cpu
                            stream.write(json.dumps(row, ensure_ascii=False) + "\n")
                            stream.flush()
                            print(
                                json.dumps(
                                    {
                                        k: row[k]
                                        for k in (
                                            "id",
                                            "method",
                                            "temperature",
                                            "coordinate",
                                            "pass2",
                                            "extra_reunions",
                                            "first_equal",
                                        )
                                    }
                                ),
                                flush=True,
                            )


if __name__ == "__main__":
    main()
