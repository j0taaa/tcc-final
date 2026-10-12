"""Opt-in native EPIC source-boundary audit; no golds or coupling win claim."""

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

from .native_state_v11 import Candidate, InitialHeadCache
from .native_task_v11 import GRAMMAR, LEXICAL, PREFIX, evaluate, instruction, root_operator

HERE = Path(__file__).parent
MASK, SPECIAL = 126336, (126081, 126348)


def stamp():
    torch.cuda.synchronize()
    return time.perf_counter(), time.process_time()


def elapsed(start):
    end = stamp()
    return dict(wall=end[0] - start[0], cpu=end[1] - start[1])


def snapshot(candidate, tokenizer, chat_len):
    if candidate.current is None:
        return dict(ids=[], root=None, complete=False)
    tokens, _, complete = candidate.current
    ids = tokens[0, chat_len:].tolist()
    return dict(ids=ids, root=root_operator(tokenizer.decode(ids)), complete=complete)


def main():
    from transformers import AutoModel, AutoTokenizer, BitsAndBytesConfig

    parser = argparse.ArgumentParser()
    parser.add_argument("--source-commit", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise SystemExit("Refuse to overwrite observations")
    names = (
        "native_boundary_v11.py",
        "native_state_v11.py",
        "native_task_v11.py",
        "native-inputs-v11.json",
        "native-protocol-v11.json",
        "native-boundary-contract-v11.md",
        "native-copy-origin-v11.json",
    )
    hashes = {}
    for name in names:
        path = HERE / name
        if path.read_bytes() != subprocess.check_output(
            ["git", "show", f"{args.source_commit}:{path.relative_to(Path.cwd())}"]
        ):
            raise ValueError(f"Unfrozen source: {name}")
        hashes[name] = hashlib.sha256(path.read_bytes()).hexdigest()
    cfg = json.loads((HERE / "native-protocol-v11.json").read_text())
    if hashes["native-inputs-v11.json"] != cfg["inputs_sha256"]:
        raise ValueError("Changed public inputs")
    os.environ.update(cfg["native_env"])
    torch.set_num_threads(cfg["cpu_threads"])
    begin = time.perf_counter()
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
    load = time.perf_counter() - begin
    assert actual.config._commit_hash == cfg["revision"]
    begin = stamp()
    grammar = CFG.from_text(GRAMMAR, "S").to_normal_form().to_normal_form()
    lex = compile_lex_map(LEXICAL)
    additional = preprocessed_generate_stuff(tokenizer, grammar, lex)
    data = dict(
        source_commit=args.source_commit,
        hashes=hashes,
        config=cfg,
        native_sha256=hashlib.sha256(Path(native.__file__).read_bytes()).hexdigest(),
        hardware=torch.cuda.get_device_name(),
        torch=torch.__version__,
        load_wall_separate=load,
        grammar_setup=elapsed(begin),
        records=[],
        scope=cfg["scope"],
        randomness="Seeded private machine PRNGs, not an exact iid oracle",
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)

    def save():
        args.output.write_text(json.dumps(data, indent=2) + "\n")

    save()
    with torch.no_grad():
        for record in json.loads((HERE / "native-inputs-v11.json").read_text())["records"]:
            begin = stamp()
            chat = tokenizer.apply_chat_template(
                [{"role": "user", "content": instruction(record["question"])}],
                add_generation_prompt=True,
                tokenize=True,
            )
            prompt = chat + tokenizer.encode(PREFIX, add_special_tokens=False)
            assert len(prompt) <= cfg["max_prompt_tokens"]
            ids = torch.tensor([prompt], device=actual.device)
            model = InitialHeadCache(actual)
            initial = torch.full(
                (1, len(prompt) + cfg["gen_length"]), MASK, dtype=torch.long, device=actual.device
            )
            initial[:, : len(prompt)] = ids
            model(initial)
            entry = dict(
                id=record["id"], prompt_tokens=len(prompt), common_setup=elapsed(begin), sources=[]
            )
            data["records"].append(entry)
            draws = random.Random(cfg["seed"] ^ int(record["selection_sha256"][:16], 16))
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

            for ordinal in range(cfg["sources"]):
                begin, before_fw, before_q = stamp(), model.forwards, model.queries
                seed = draws.getrandbits(32)
                candidate = Candidate(factory, seed, actual.device)
                candidate.advance()
                state = snapshot(candidate, tokenizer, len(chat))
                row = dict(
                    seed=seed,
                    first_yield=state,
                    first_cost=elapsed(begin),
                    first_forwards=model.forwards - before_fw,
                    first_queries=model.queries - before_q,
                )
                entry["sources"].append(row)
                save()
                begin, before_fw = stamp(), model.forwards
                while state["root"] is None and not candidate.ended:
                    candidate.advance()
                    state = snapshot(candidate, tokenizer, len(chat))
                row.update(
                    root_boundary=state,
                    root_additional_cost=elapsed(begin),
                    root_additional_forwards=model.forwards - before_fw,
                )
                save()
                if ordinal < cfg["completed_sources"]:
                    begin, before_fw = stamp(), model.forwards
                    while candidate.advance() is not None:
                        pass
                    state = snapshot(candidate, tokenizer, len(chat))
                    cut = next(
                        (i for i, token in enumerate(state["ids"]) if token in (MASK, *SPECIAL)),
                        len(state["ids"]),
                    )
                    text = tokenizer.decode(state["ids"][:cut])
                    try:
                        evaluate(text)
                        valid = True
                    except (ValueError, ZeroDivisionError):
                        valid = False
                    row.update(
                        final=state,
                        text=text,
                        executable_json=valid,
                        continuation_cost=elapsed(begin),
                        continuation_forwards=model.forwards - before_fw,
                    )
                begin = stamp()
                candidate.close()
                row["disposal_cost"] = elapsed(begin)
                save()
            print(
                record["id"],
                "first roots",
                [r["first_yield"]["root"] for r in entry["sources"]],
                "root forwards",
                [r["root_additional_forwards"] for r in entry["sources"]],
                flush=True,
            )
            save()


if __name__ == "__main__":
    main()
