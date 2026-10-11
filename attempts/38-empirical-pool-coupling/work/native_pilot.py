"""Opt-in frozen-protocol full native calls; never imports golds."""

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

from . import controls, couple
from .native_state import Candidate, InitialHeadCache
from .native_task import GRAMMAR, LEXICAL, PREFIX, instruction

HERE = Path(__file__).parent
MASK, SPECIAL = 126336, (126081, 126348)


def stamp():
    torch.cuda.synchronize()
    return time.perf_counter(), time.process_time()


def elapsed(start):
    end = stamp()
    return {"wall": end[0] - start[0], "cpu": end[1] - start[1]}


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


class MeasuredModel:
    def __init__(self, model):
        self.model, self.device, self.costs = model, model.device, []

    def __call__(self, ids):
        begin = stamp()
        result = self.model(ids)
        self.costs.append(elapsed(begin))
        return result


def main():
    from transformers import AutoModel, AutoTokenizer, BitsAndBytesConfig

    parser = argparse.ArgumentParser()
    parser.add_argument("--source-commit", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    meta_path = args.output.with_suffix(".metadata.json")
    if args.output.exists() or meta_path.exists():
        raise SystemExit("refuse to overwrite evidence")
    paths = [
        *(
            HERE / name
            for name in (
                "native_pilot.py",
                "native_state.py",
                "native_task.py",
                "controls.py",
                "couple.py",
            )
        ),
        HERE / "native-inputs-v5.json",
        HERE / "native-protocol-v5.json",
        HERE / "native-protocol-v5.md",
    ]
    sources = {}
    for path in paths:
        relative = path.relative_to(Path.cwd())
        if (
            subprocess.check_output(["git", "show", f"{args.source_commit}:{relative}"])
            != path.read_bytes()
        ):
            raise ValueError(f"producer not frozen: {path.name}")
        sources[path.name] = digest(path)
    cfg = json.loads((HERE / "native-protocol-v5.json").read_text())
    if digest(HERE / "native-inputs-v5.json") != cfg["inputs_sha256"]:
        raise ValueError("inputs changed")
    records = json.loads((HERE / "native-inputs-v5.json").read_text())["records"]
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
    load_wall = time.perf_counter() - begin
    if actual.config._commit_hash != cfg["revision"]:
        raise ValueError("wrong model revision")
    begin = stamp()
    grammar = CFG.from_text(GRAMMAR, "S").to_normal_form().to_normal_form()
    lex = compile_lex_map(LEXICAL)
    additional = preprocessed_generate_stuff(tokenizer, grammar, lex)
    setup = elapsed(begin)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    metadata = dict(
        source_commit=args.source_commit,
        sources=sources,
        config=cfg,
        hardware=torch.cuda.get_device_name(),
        torch=torch.__version__,
        load_wall_excluded_common=load_wall,
        grammar_setup=setup,
        upstream_sha256=digest(Path(native.__file__)),
        frames=[],
        scope="FULL live calls; small functional/cost pilot, NO statistical win",
        randomness=(
            "separate seeded pseudorandom streams; "
            "theorem assumes iid oracle and independent exact coins"
        ),
    )
    meta_path.write_text(json.dumps(metadata, indent=2) + "\n")
    with torch.no_grad(), args.output.open("x") as output:
        for record in records:
            begin = stamp()
            chat = tokenizer.apply_chat_template(
                [{"role": "user", "content": instruction(record["question"])}],
                add_generation_prompt=True,
                tokenize=True,
            )
            all_ids = chat + tokenizer.encode(PREFIX, add_special_tokens=False)
            if len(all_ids) > cfg["max_prompt_tokens"]:
                raise ValueError("frozen input exceeds declared prompt budget")
            ids = torch.tensor([all_ids], device=actual.device)
            measured = MeasuredModel(actual)
            model = InitialHeadCache(measured)
            initial = torch.full(
                (1, len(all_ids) + cfg["gen_length"]), MASK, dtype=torch.long, device=actual.device
            )
            initial[:, : len(all_ids)] = ids
            model(initial)  # Charged common preparation, available to EVERY method.
            frame_setup = elapsed(begin)
            metadata["frames"].append(
                dict(id=record["id"], setup=frame_setup, prompt_tokens=len(all_ids))
            )
            meta_path.write_text(json.dumps(metadata, indent=2) + "\n")

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

            for rep in range(cfg["replicates"]):
                seed = cfg["seed"] + int(record["selection_sha256"][:12], 16) + rep * 100003
                methods = cfg["methods"][rep:] + cfg["methods"][:rep]
                first_ids = None
                for method in methods:
                    draws, coins = random.Random(seed), random.Random(seed ^ 0x38A38)
                    seen = []

                    def draw(
                        seed=None,
                        draws=draws,
                        model=model,
                        seen=seen,
                        factory=factory,
                        chat_len=chat_len,
                    ):
                        seed = draws.getrandbits(32) if seed is None else seed
                        start, queries, forwards = stamp(), model.queries, model.forwards
                        candidate = Candidate(factory, seed, actual.device)
                        payload = {"seed": seed, "status": "INCOMPLETE", "ids": [], "text": ""}
                        try:
                            while candidate.advance() is not None:
                                pass
                            if candidate.current is not None:
                                payload["ids"] = candidate.current[0][0, chat_len:].tolist()
                                cut = next(
                                    (
                                        i
                                        for i, t in enumerate(payload["ids"])
                                        if t in (MASK, *SPECIAL)
                                    ),
                                    len(payload["ids"]),
                                )
                                payload["text"] = tokenizer.decode(
                                    payload["ids"][:cut], skip_special_tokens=True
                                )
                                payload["status"] = (
                                    "COMPLETE" if candidate.current[2] else "INCOMPLETE"
                                )
                                payload["rejections"] = len(candidate.current[1])
                        except Exception as exc:
                            payload.update(
                                status="ERROR", error_type=type(exc).__name__, error=str(exc)
                            )
                        finally:
                            candidate.close()
                        payload.update(
                            elapsed(start),
                            queries=model.queries - queries,
                            forwards=model.forwards - forwards,
                        )
                        seen.append(payload)
                        return payload

                    def key(payload):
                        if "key" not in payload:
                            payload["key"] = controls.canonical(payload)
                        return payload["key"]

                    begin = stamp()
                    if method == "adaptive4":
                        x, y, count = couple.pair(draw, key, coins.randrange)
                    elif method == "mean3":
                        x, y, count = couple.pair_mean_three(draw, key, coins.randrange)
                    elif method in ("pool4", "early_pool"):
                        x, y, count = controls.pool(
                            draw, key, coins.randrange, early=method == "early_pool"
                        )
                    elif method == "novelty3":
                        x, y, count = controls.novelty_three(draw, key, coins.randrange)
                    else:
                        x = draw()
                        y = draw((x["seed"] + 2**31) % 2**32) if method == "seed_half" else draw()
                        count = 2
                    cost = elapsed(begin)
                    for payload in seen:
                        key(payload)  # Untimed diagnostics when unneeded by the method.
                    assert x is seen[0] and count == len(seen)
                    if first_ids is None:
                        first_ids = x["ids"]
                    preserved = first_ids == x["ids"]
                    row = dict(
                        id=record["id"],
                        rep=rep,
                        method=method,
                        calls=count,
                        first_preserved=preserved,
                        selected=[
                            next(i for i, p in enumerate(seen) if p is item) for item in (x, y)
                        ],
                        draws=seen,
                        warm=cost,
                        cold={u: cost[u] + setup[u] + frame_setup[u] for u in cost},
                        forwards=sum(p["forwards"] for p in seen),
                        queries=sum(p["queries"] for p in seen),
                    )
                    output.write(json.dumps(row, separators=(",", ":")) + "\n")
                    output.flush()
                    print(
                        record["id"],
                        rep,
                        method,
                        count,
                        row["forwards"],
                        round(cost["wall"], 3),
                        flush=True,
                    )
                    if not preserved:
                        raise RuntimeError(
                            "original first IDs diverged across same-seed controls; "
                            "evidence retained"
                        )


if __name__ == "__main__":
    main()
