"""Opt-in resource screen; actual native prefixes, NO labels/quality claim."""

import argparse
import hashlib
import json
import os
import random
import subprocess
import time
from pathlib import Path

import torch
from constrained_diffusion.constrain_utils import compile_lex_map, preprocessed_generate_stuff
from constrained_diffusion.eval.dllm.models.llada import generate_constrained as native
from rustformlang.cfg import CFG

from .arithmetic_task_v6 import GRAMMAR, LEXICAL, PREFIX, evaluate, instruction, root_operator
from .native_transition_v4 import Candidate, InitialHeadCache
from .number_checkpoint_v8 import number_checkpoint

HERE = Path(__file__).parent
MASK = 126336


def stamp():
    torch.cuda.synchronize()
    return time.perf_counter(), time.process_time()


def elapsed(start):
    end = stamp()
    return dict(wall=end[0] - start[0], cpu=end[1] - start[1])


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def frozen(commit, protocol):
    paths = [
        *HERE.glob("*.py"),
        HERE / "arithmetic-inputs-v7.json",
        HERE / f"{protocol}.json",
        HERE / f"{protocol}.md",
    ]
    sources = {}
    for path in paths:
        relative = path.relative_to(Path.cwd()) if path.is_absolute() else path
        if subprocess.check_output(["git", "show", f"{commit}:{relative}"]) != path.read_bytes():
            raise ValueError(f"producer not frozen at supplied commit: {path.name}")
        sources[path.name] = digest(path)
    return sources


class MeasuredModel:
    def __init__(self, model, limit):
        self.model, self.device, self.limit = model, model.device, limit
        self.costs = []

    def __call__(self, ids):
        if len(self.costs) >= self.limit:
            raise RuntimeError("per-question new-forward budget")
        start = stamp()
        result = self.model(ids)
        self.costs.append(elapsed(start))
        return result


def text_prefix(candidate, tokenizer, chat_len):
    if candidate.current is None:
        return "", []
    ids = candidate.current[0][0, chat_len:].tolist()
    cut = next((i for i, t in enumerate(ids) if t in (MASK, 126081, 126348)), len(ids))
    return tokenizer.decode(ids[:cut], skip_special_tokens=True), ids


def main():
    from transformers import AutoModel, AutoTokenizer, BitsAndBytesConfig

    parser = argparse.ArgumentParser()
    parser.add_argument("--source-commit", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument(
        "--protocol",
        choices=("arithmetic-protocol-v7", "arithmetic-protocol-v8"),
        default="arithmetic-protocol-v7",
    )
    args = parser.parse_args()
    metadata = args.output.with_suffix(".metadata.json")
    if args.output.exists() or metadata.exists():
        raise SystemExit("refuse to overwrite evidence")
    sources = frozen(args.source_commit, args.protocol)
    cfg = json.loads((HERE / f"{args.protocol}.json").read_text())
    checkpoint = cfg.get("checkpoint", "root")
    if checkpoint not in ("root", "first_new_number"):
        raise ValueError("unsupported checkpoint")
    manifest = json.loads((HERE / "arithmetic-inputs-v7.json").read_text())
    if digest(HERE / "arithmetic-inputs-v7.json") != cfg["inputs_sha256"]:
        raise ValueError("frozen inputs changed")
    os.environ.update(cfg["native_env"])
    torch.set_num_threads(cfg["cpu_threads"])
    start = time.perf_counter()
    tokenizer = AutoTokenizer.from_pretrained(
        cfg["model_id"], revision=cfg["revision"], local_files_only=True
    )
    actual = AutoModel.from_pretrained(
        cfg["model_id"],
        revision=cfg["revision"],
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
    torch.cuda.synchronize()
    load_wall = time.perf_counter() - start
    if actual.config._commit_hash != cfg["revision"]:
        raise ValueError("wrong model revision")
    start = stamp()
    grammar = CFG.from_text(GRAMMAR, "S").to_normal_form().to_normal_form()
    lex = compile_lex_map(LEXICAL)
    additional = preprocessed_generate_stuff(tokenizer, grammar, lex)
    setup = elapsed(start)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    metadata.write_text(
        json.dumps(
            dict(
                source_commit=args.source_commit,
                sources=sources,
                config=cfg,
                hardware=torch.cuda.get_device_name(),
                torch=torch.__version__,
                load_wall_excluded_common=load_wall,
                grammar_setup=setup,
                grammar_sha256=hashlib.sha256(GRAMMAR.encode()).hexdigest(),
                lexical_sha256=hashlib.sha256(
                    json.dumps(LEXICAL, sort_keys=True).encode()
                ).hexdigest(),
                upstream_sha256=digest(Path(native.__file__)),
                scope="resource screen, NO gold/accuracy/competitive timing claim",
            ),
            indent=2,
        )
        + "\n"
    )
    with torch.no_grad(), args.output.open("x") as output:
        for record in manifest["records"]:
            row = dict(id=record["id"], prefixes=[], screen_pass=False)
            first = current = None
            start = stamp()
            model = InitialHeadCache(MeasuredModel(actual, cfg["max_forwards_per_question"]))
            try:
                chat = tokenizer.apply_chat_template(
                    [{"role": "user", "content": instruction(record["question"])}],
                    add_generation_prompt=True,
                    tokenize=True,
                )
                all_ids = chat + tokenizer.encode(PREFIX, add_special_tokens=False)
                if len(all_ids) > cfg["max_prompt_tokens"]:
                    raise ValueError("prompt-token resource refusal")
                ids = torch.tensor([all_ids], device=actual.device)
                row["prompt_setup"] = elapsed(start)
                chat_len = len(chat)

                def factory(model=model, ids=ids, chat_len=chat_len):
                    return native.generate(
                        model,
                        ids,
                        tokenizer,
                        grammar,
                        lex,
                        prompt_len=chat_len,
                        gen_length=cfg["gen_length"],
                        block_length=cfg["block_length"],
                        steps=cfg["steps"],
                        temperature=cfg["temperature"],
                        max_resamples=cfg["max_resamples"],
                        mask_id=MASK,
                        constrain=True,
                        additional_stuff=additional,
                    )

                rng = random.Random(cfg["seed"] + int(record["selection_sha256"][:12], 16))
                for index in range(cfg["draws_per_question"]):
                    seed = rng.randrange(2**32)
                    begin, queries, forwards = stamp(), model.queries, model.forwards
                    current = Candidate(factory, seed, actual.device)
                    events, first_event_root, op, number, first_event_number = (
                        0,
                        None,
                        None,
                        None,
                        None,
                    )
                    previous = all_ids + [MASK] * cfg["gen_length"]
                    while (event := current.advance()) is not None:
                        events += 1
                        text, tokens = text_prefix(current, tokenizer, len(chat))
                        op = root_operator(text)
                        accepted = event[0][0].tolist()
                        number = number_checkpoint(
                            previous,
                            accepted,
                            lambda token: tokenizer.decode([token], skip_special_tokens=True),
                            start=len(all_ids),
                            mask_id=MASK,
                            special_ids=(126081, 126348),
                        )
                        previous = accepted
                        if events == 1:
                            first_event_root = op
                            first_event_number = number
                        known = op is not None if checkpoint == "root" else number is not None
                        if known or event[2]:
                            break
                    text, tokens = text_prefix(current, tokenizer, len(chat))
                    prefix = dict(
                        seed=seed,
                        root=op,
                        checkpoint=checkpoint,
                        number=number,
                        class1=(
                            op in ("mul", "div")
                            if checkpoint == "root"
                            else number is not None and number["digit"] % 2 == 1
                        ),
                        first_event_root=first_event_root,
                        first_event_number=first_event_number,
                        events=events,
                        native_complete=bool(current.current and current.current[2]),
                        ended=current.ended,
                        accepted_prefix=text,
                        original_ids=tokens,
                        rejections=len(current.current[1]) if current.current else 0,
                        queries=model.queries - queries,
                        forwards=model.forwards - forwards,
                    )
                    if index == 0:
                        first, current = current, None
                    else:
                        current.close()
                        current = None
                    prefix.update(elapsed(begin))
                    row["prefixes"].append(prefix)
                begin, queries, forwards = stamp(), model.queries, model.forwards
                while first.advance() is not None:
                    pass
                text, tokens = text_prefix(first, tokenizer, len(chat))
                tail = dict(
                    queries=model.queries - queries,
                    forwards=model.forwards - forwards,
                    native_complete=bool(first.current and first.current[2]),
                    original_ids=tokens,
                    output=text,
                )
                try:
                    tail["execution"] = str(evaluate(text))
                    tail["execution_status"] = "executable"
                except (ValueError, TypeError, ZeroDivisionError, RecursionError) as exc:
                    tail["execution_status"] = type(exc).__name__
                    tail["execution_error"] = str(exc)
                first.close()
                first = None
                tail.update(elapsed(begin))
                row["tail"] = tail
                counts = [sum(p["class1"] == bit for p in row["prefixes"]) for bit in (False, True)]
                row["class_counts"] = counts
                common = model.model.costs[0]
                row["initial_forward"] = common
                row["mean_prefix_cold"] = {
                    unit: sum(p[unit] for p in row["prefixes"]) / len(row["prefixes"])
                    for unit in ("wall", "cpu")
                }
                row["mean_prefix_after_common"] = {
                    unit: row["mean_prefix_cold"][unit] - common[unit] / len(row["prefixes"])
                    for unit in ("wall", "cpu")
                }
                row["screen_pass"] = (
                    min(counts) >= cfg["screen"]["min_classes_each"]
                    and tail["forwards"] >= cfg["screen"]["min_tail_forwards"]
                    and all(row["mean_prefix_after_common"][u] <= tail[u] for u in ("wall", "cpu"))
                )
                row["status"] = "complete_diagnostic"
            except Exception as exc:
                row.update(status="error", error=dict(type=type(exc).__name__, message=str(exc)))
            finally:
                for candidate in (current, first):
                    if candidate is not None:
                        candidate.close()
            row["queries"], row["forwards"] = model.queries, model.forwards
            row["full_question"] = elapsed(start)
            output.write(json.dumps(row) + "\n")
            output.flush()
            print(
                json.dumps(
                    dict(
                        id=row["id"],
                        status=row["status"],
                        screen_pass=row["screen_pass"],
                        prefixes=len(row["prefixes"]),
                        forwards=model.forwards,
                    )
                ),
                flush=True,
            )


if __name__ == "__main__":
    main()
