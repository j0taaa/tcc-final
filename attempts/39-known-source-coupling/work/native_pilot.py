"""Opt-in first-yield coordination; unchanged native generator, no gold import."""

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

from . import controls, kernel
from .native_state import Candidate, InitialHeadCache
from .native_task import GRAMMAR, LEXICAL, PREFIX, instruction
from .source import Source

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


def first_key(snapshot, input_length):
    if snapshot is None:
        return ("NO_YIELD",)
    ids = snapshot[0][0, input_length:].tolist()
    return next(((i, t) for i, t in enumerate(ids) if t != MASK), ("NO_PROGRESS",))


def main():
    from transformers import AutoModel, AutoTokenizer, BitsAndBytesConfig

    parser = argparse.ArgumentParser()
    parser.add_argument("--source-commit", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    meta_path = args.output.with_suffix(".metadata.json")
    if args.output.exists() or meta_path.exists():
        raise SystemExit("refuse to overwrite evidence")
    names = (
        "native_pilot.py",
        "native_state.py",
        "native_task.py",
        "controls.py",
        "kernel.py",
        "source.py",
        "native-origin-v4.json",
        "native-inputs-v3.json",
        "native-protocol-v3.json",
        "native-protocol-v3.md",
    )
    sources = {}
    for name in names:
        path = HERE / name
        relative = path.relative_to(Path.cwd())
        if (
            subprocess.check_output(["git", "show", f"{args.source_commit}:{relative}"])
            != path.read_bytes()
        ):
            raise ValueError(f"producer not frozen: {name}")
        sources[name] = digest(path)
    cfg = json.loads((HERE / "native-protocol-v3.json").read_text())
    if digest(HERE / "native-inputs-v3.json") != cfg["inputs_sha256"]:
        raise ValueError("inputs changed")
    records = json.loads((HERE / "native-inputs-v3.json").read_text())["records"]
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
        scope="FULL native original continuations; developmental pilot, NO statistical win",
        randomness=(
            "known finite32-bit seeds; distinct-source rank draws and separate selection "
            "coins; measured tapes pseudorandom"
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
            model(initial)
            frame_setup = elapsed(begin)
            metadata["frames"].append(
                dict(
                    id=record["id"],
                    setup=frame_setup,
                    prompt_tokens=len(all_ids),
                    prefix_tokens=len(all_ids) - len(chat),
                    head_forward=measured.costs[0],
                )
            )
            meta_path.write_text(json.dumps(metadata, indent=2) + "\n")
            chat_len = len(chat)
            input_length = len(all_ids)

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
                    ranks, coins = random.Random(seed), random.Random(seed ^ 0x39A39)
                    seen = []
                    whole = method in ("iid2", "derange2", "seed_half", "iid3")

                    def query(
                        source_seed,
                        model=model,
                        factory=factory,
                        seen=seen,
                        whole=whole,
                        input_length=input_length,
                        chat_len=chat_len,
                    ):
                        start, queries, forwards = stamp(), model.queries, model.forwards
                        candidate = Candidate(factory, source_seed, actual.device)
                        payload = dict(
                            seed=source_seed, status="PREFIX", ids=[], text="", _candidate=candidate
                        )

                        def on_first(snapshot):
                            payload.update(
                                prefix=elapsed(start),
                                prefix_queries=model.queries - queries,
                                prefix_forwards=model.forwards - forwards,
                                key=first_key(snapshot, input_length),
                                first_ids=[]
                                if snapshot is None
                                else snapshot[0][0, chat_len:].tolist(),
                                first_complete=False if snapshot is None else snapshot[2],
                            )

                        try:
                            if whole:
                                candidate.finish(on_first)
                            else:
                                snapshot = candidate.advance()
                                on_first(snapshot)
                        except Exception as exc:
                            payload.update(
                                status="ERROR",
                                error_type=type(exc).__name__,
                                error=str(exc),
                                key=payload.get("key", ("ERROR", type(exc).__name__)),
                            )
                        payload.update(
                            query=elapsed(start),
                            query_queries=model.queries - queries,
                            query_forwards=model.forwards - forwards,
                        )
                        seen.append(payload)
                        return payload

                    distinct = Source(cfg["source_size"], query, ranks.randrange)

                    def independent_draw(query=query, ranks=ranks):
                        return query(ranks.randrange(cfg["source_size"]))

                    draw = independent_draw if whole else distinct

                    def key(payload):
                        return payload["key"]

                    torch.cuda.reset_peak_memory_stats()
                    base_memory = dict(
                        allocated=torch.cuda.memory_allocated(),
                        reserved=torch.cuda.memory_reserved(),
                    )
                    begin = stamp()
                    neural_begin = len(measured.costs)
                    if method == "adaptive4":
                        x, y, count = kernel.pair(draw, key, coins.randrange)
                        selected = [x, y]
                    elif method == "mean3":
                        x, y, count = kernel.pair_mean_three(draw, key, coins.randrange)
                        selected = [x, y]
                    elif method in ("pool4", "early_pool"):
                        x, y, count = controls.pool(
                            draw, key, coins.randrange, early=method == "early_pool"
                        )
                        selected = [x, y]
                    elif method == "novelty3":
                        x, y, count = controls.novelty_three(draw, key, coins.randrange)
                        selected = [x, y]
                    elif method == "derange2":
                        selected, count = [distinct(), distinct()], 2
                    elif method == "seed_half":
                        x = draw()
                        selected, count = [x, query((x["seed"] + 2**31) % cfg["source_size"])], 2
                    else:
                        count = 3 if method == "iid3" else 2
                        selected = [draw() for _ in range(count)]
                    for payload in seen:
                        if not any(payload is item for item in selected):
                            payload.pop("_candidate").close()
                            if payload["status"] != "ERROR":
                                payload["status"] = "DISCARDED"
                    for payload in selected:
                        candidate = payload.pop("_candidate")
                        start, queries, forwards = stamp(), model.queries, model.forwards
                        try:
                            if payload["status"] != "ERROR":
                                candidate.finish()
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
                                else:
                                    payload["status"] = "NO_YIELD"
                        except Exception as exc:
                            payload.update(
                                status="ERROR", error_type=type(exc).__name__, error=str(exc)
                            )
                        finally:
                            candidate.close()
                        payload.update(
                            continuation=elapsed(start),
                            continuation_queries=model.queries - queries,
                            continuation_forwards=model.forwards - forwards,
                        )
                    cost = elapsed(begin)
                    memory = dict(
                        base=base_memory,
                        peak_allocated=torch.cuda.max_memory_allocated(),
                        peak_reserved=torch.cuda.max_memory_reserved(),
                    )
                    assert selected[0] is seen[0] and count == len(seen)
                    if first_ids is None:
                        first_ids = selected[0]["ids"]
                    preserved = first_ids == selected[0]["ids"]
                    prefix_ok = all(p.get("prefix_forwards") == 0 for p in seen)
                    row = dict(
                        id=record["id"],
                        rep=rep,
                        method=method,
                        calls=count,
                        first_preserved=preserved,
                        prefix_zero_forward=prefix_ok,
                        selected=[
                            next(i for i, p in enumerate(seen) if p is item) for item in selected
                        ],
                        draws=seen,
                        warm=cost,
                        cold={u: cost[u] + setup[u] + frame_setup[u] for u in cost},
                        memory=memory,
                        forwards=sum(
                            p["query_forwards"] + p.get("continuation_forwards", 0) for p in seen
                        ),
                        queries=sum(
                            p["query_queries"] + p.get("continuation_queries", 0) for p in seen
                        ),
                        cold_forwards=1
                        + sum(
                            p["query_forwards"] + p.get("continuation_forwards", 0) for p in seen
                        ),
                        neural={u: sum(c[u] for c in measured.costs[neural_begin:]) for u in cost},
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
                        prefix_ok,
                        flush=True,
                    )
                    if not preserved or not prefix_ok:
                        raise RuntimeError(
                            "native boundary/first trajectory invariant failed; evidence retained"
                        )


if __name__ == "__main__":
    main()
