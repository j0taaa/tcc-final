"""Opt-in existing-input information audit; no golds or competitive timing claim."""

import argparse
import hashlib
import json
import os
import random
import subprocess
from collections import Counter
from pathlib import Path

import torch
from constrained_diffusion.constrain_utils import compile_lex_map, preprocessed_generate_stuff
from constrained_diffusion.eval.dllm.models.llada import generate_constrained as native
from rustformlang.cfg import CFG

from .native_pilot import MeasuredModel, elapsed, stamp
from .native_stage import StageCandidate, body_key
from .native_state import InitialHeadCache
from .native_task import GRAMMAR, LEXICAL, PREFIX, instruction
from .source import Source

HERE = Path(__file__).parent
MASK = 126336


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    from transformers import AutoModel, AutoTokenizer, BitsAndBytesConfig

    parser = argparse.ArgumentParser()
    parser.add_argument("--source-commit", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    meta_path = args.output.with_suffix(".metadata.json")
    if args.output.exists() or meta_path.exists():
        raise SystemExit("refuse evidence overwrite")
    names = (
        "phase_info.py",
        "native_stage.py",
        "native_state.py",
        "native_pilot.py",
        "native_task.py",
        "source.py",
        "first-step-contract-v6.md",
        "native-inputs-v3.json",
        "native-protocol-v3.json",
        "evidence/native-v4.jsonl",
    )
    sources = {}
    for name in names:
        path = HERE / name
        relative = path.relative_to(Path.cwd())
        if (
            subprocess.check_output(["git", "show", f"{args.source_commit}:{relative}"])
            != path.read_bytes()
        ):
            raise ValueError(f"producer/input not frozen: {name}")
        sources[name] = digest(path)
    cfg = json.loads((HERE / "native-protocol-v3.json").read_text())
    inputs = json.loads((HERE / "native-inputs-v3.json").read_text())["records"]
    archived = [
        json.loads(line) for line in (HERE / "evidence/native-v4.jsonl").read_text().splitlines()
    ]
    os.environ.update(cfg["native_env"])
    torch.set_num_threads(cfg["cpu_threads"])
    begin = stamp()
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
    load = elapsed(begin)
    if actual.config._commit_hash != cfg["revision"]:
        raise ValueError("wrong model revision")
    begin = stamp()
    grammar = CFG.from_text(GRAMMAR, "S").to_normal_form().to_normal_form()
    lex = compile_lex_map(LEXICAL)
    additional = preprocessed_generate_stuff(tokenizer, grammar, lex)
    metadata = dict(
        source_commit=args.source_commit,
        sources=sources,
        config=cfg,
        scope="Existing-input information/functional audit, NO performance/semantic gate",
        hardware=torch.cuda.get_device_name(),
        torch=torch.__version__,
        load=load,
        grammar_setup=elapsed(begin),
        native_sha256=digest(Path(native.__file__)),
        frames=[],
    )
    meta_path.write_text(json.dumps(metadata, indent=2) + "\n")
    with torch.no_grad(), args.output.open("x") as output:
        for record in inputs:
            rows = [r for r in archived if r["id"] == record["id"]]
            seeds = {d["seed"] for r in rows for d in r["draws"]}
            validate = set()
            for rep in range(cfg["replicates"]):
                seed = cfg["seed"] + int(record["selection_sha256"][:12], 16) + rep * 100003
                ranks = random.Random(seed)
                draw = Source(cfg["source_size"], lambda s: s, ranks.randrange)
                tape = [draw() for _ in range(4)]
                validate.add(tape[0])
                seeds.update(tape)
            originals = {}
            for row in rows:
                for index in row["selected"]:
                    d = row["draws"][index]
                    assert originals.setdefault(d["seed"], (d["ids"], d["status"])) == (
                        d["ids"],
                        d["status"],
                    )
            begin = stamp()
            chat = tokenizer.apply_chat_template(
                [{"role": "user", "content": instruction(record["question"])}],
                tokenize=True,
                add_generation_prompt=True,
            )
            all_ids = chat + tokenizer.encode(PREFIX, add_special_tokens=False)
            prompt = torch.tensor([all_ids], device=actual.device)
            measured = MeasuredModel(actual)
            model = InitialHeadCache(measured)
            initial = torch.full(
                (1, len(all_ids) + cfg["gen_length"]), MASK, dtype=torch.long, device=actual.device
            )
            initial[:, : len(all_ids)] = prompt
            model(initial)
            setup = elapsed(begin)
            counts = Counter()
            chat_len = len(chat)

            def factory(model=model, prompt=prompt, chat_len=chat_len):
                return native.generate(
                    model,
                    prompt,
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

            for seed in sorted(seeds):
                candidate = StageCandidate(factory, seed, actual.device)
                begin, queries, forwards = stamp(), model.queries, model.forwards
                row = dict(id=record["id"], seed=seed, status="PENDING")
                try:
                    snapshot = candidate.pause()
                    row.update(
                        key=body_key(snapshot, len(all_ids)),
                        stage=elapsed(begin),
                        stage_queries=model.queries - queries,
                        stage_forwards=model.forwards - forwards,
                        first_ids=candidate.first[0][0, len(chat) :].tolist(),
                        stage_ids=snapshot[0][0, len(chat) :].tolist(),
                        ended=candidate.ended,
                    )
                    if row["stage_forwards"] != 0:
                        raise ValueError("first-step helper crossed new-forward boundary")
                    counts[row["key"]] += 1
                    if seed in validate:
                        start = stamp()
                        candidate.finish()
                        final = candidate.current[0][0, len(chat) :].tolist()
                        status = "COMPLETE" if candidate.current[2] else "INCOMPLETE"
                        expected = originals[seed]
                        assert (final, status) == expected
                        row.update(
                            original_full_ids_preserved=True,
                            final_ids=final,
                            final_status=status,
                            continuation=elapsed(start),
                        )
                    row["status"] = "OK"
                except Exception as exc:
                    row.update(status="ERROR", error_type=type(exc).__name__, error=str(exc))
                finally:
                    candidate.close()
                row.update(
                    total_queries=model.queries - queries, total_forwards=model.forwards - forwards
                )
                output.write(json.dumps(row, separators=(",", ":")) + "\n")
                output.flush()
                print(
                    record["id"],
                    seed,
                    row["status"],
                    row.get("key"),
                    row.get("stage_forwards"),
                    flush=True,
                )
                if row["status"] != "OK":
                    raise RuntimeError("first-step audit failed; original evidence retained")
            metadata["frames"].append(
                dict(
                    id=record["id"],
                    setup=setup,
                    queries=len(seeds),
                    classes=[dict(key=k, count=n) for k, n in counts.items()],
                    original_full_validations=len(validate),
                    new_forwards=model.forwards,
                )
            )
            meta_path.write_text(json.dumps(metadata, indent=2) + "\n")


if __name__ == "__main__":
    main()
