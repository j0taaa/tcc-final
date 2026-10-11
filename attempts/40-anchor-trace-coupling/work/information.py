"""Opt-in OLD-input functional/information audit; no quality or victory gate."""

import argparse
import hashlib
import json
import os
import random
import subprocess
import time
from collections import Counter
from pathlib import Path

import torch
from constrained_diffusion.constrain_utils import compile_lex_map, preprocessed_generate_stuff
from constrained_diffusion.eval.dllm.models.llada import generate_constrained as native
from rustformlang.cfg import CFG

from .frontier_key import snapshot_key
from .native_state import Candidate
from .native_task import GRAMMAR, LEXICAL, PREFIX, instruction
from .source import Source
from .trace import CachedCandidate, Trace, yield_sites

HERE = Path(__file__).parent
MASK = 126336


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def stamp():
    torch.cuda.synchronize()
    return time.perf_counter(), time.process_time()


def elapsed(start):
    end = stamp()
    return {"wall": end[0] - start[0], "cpu": end[1] - start[1]}


class MeasuredModel:
    def __init__(self, model):
        self.model, self.device, self.calls = model, model.device, 0

    def __call__(self, ids):
        self.calls += 1
        return self.model(ids)


def main():
    from transformers import AutoModel, AutoTokenizer, BitsAndBytesConfig

    parser = argparse.ArgumentParser()
    parser.add_argument("--source-commit", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    metadata_path = args.output.with_suffix(".metadata.json")
    if args.output.exists() or metadata_path.exists():
        raise SystemExit("refuse evidence overwrite")
    names = (
        "information.py",
        "trace.py",
        "frontier_key.py",
        "native_state.py",
        "native_task.py",
        "source.py",
        "native-inputs-v3.json",
        "native-protocol-v3.json",
        "README-information-v2.md",
        "anchor-theory-v1.md",
        "origin-v2.json",
        "evidence/native-v4.jsonl",
        "evidence/native-v4.metadata.json",
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
    original = json.loads((HERE / "evidence/native-v4.metadata.json").read_text())
    if digest(Path(native.__file__)) != original["upstream_sha256"]:
        raise ValueError("native upstream changed")
    sites = yield_sites(native.generate)
    records = json.loads((HERE / "native-inputs-v3.json").read_text())["records"]
    old = [json.loads(x) for x in (HERE / "evidence/native-v4.jsonl").read_text().splitlines()]
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
        scope=(
            "OLD-input functional information only; anchor reuses first old source; "
            "NOT a coupling/quality/performance experiment"
        ),
        hardware=torch.cuda.get_device_name(),
        torch=torch.__version__,
        load=load,
        grammar_setup=elapsed(begin),
        native_sha256=digest(Path(native.__file__)),
        sites=sites,
        frames=[],
    )
    metadata_path.write_text(json.dumps(metadata, indent=2) + "\n")
    with torch.no_grad(), args.output.open("x") as output:
        for record in records:
            originals = {}
            for row in (r for r in old if r["id"] == record["id"]):
                for index in row["selected"]:
                    item = row["draws"][index]
                    assert originals.setdefault(item["seed"], (item["ids"], item["status"])) == (
                        item["ids"],
                        item["status"],
                    )
            chat = tokenizer.apply_chat_template(
                [{"role": "user", "content": instruction(record["question"])}],
                tokenize=True,
                add_generation_prompt=True,
            )
            ids = chat + tokenizer.encode(PREFIX, add_special_tokens=False)
            prompt = torch.tensor([ids], device=actual.device)
            chat_length = len(chat)
            for rep in range(cfg["replicates"]):
                ranks = random.Random(
                    cfg["seed"] + int(record["selection_sha256"][:12], 16) + rep * 100003
                )
                draw = Source(cfg["source_size"], lambda s: s, ranks.randrange)
                tape = [draw() for _ in range(4)]
                assert all(s in originals for s in tape[:2])
                measured = MeasuredModel(actual)
                trace = Trace(measured)

                def factory(trace=trace, prompt=prompt, chat_length=chat_length):
                    return native.generate(
                        trace,
                        prompt,
                        tokenizer,
                        grammar,
                        lex,
                        prompt_len=chat_length,
                        gen_length=cfg["gen_length"],
                        block_length=cfg["block_length"],
                        steps=cfg["steps"],
                        temperature=cfg["temperature"],
                        max_resamples=cfg["max_resamples"],
                        mask_id=MASK,
                        constrain=True,
                        additional_stuff=additional,
                    )

                torch.cuda.reset_peak_memory_stats()
                start = stamp()
                anchor = Candidate(factory, tape[0], actual.device)
                anchor.finish()
                anchor_ids = anchor.current[0][0, chat_length:].tolist()
                anchor_status = "COMPLETE" if anchor.current[2] else "INCOMPLETE"
                assert (anchor_ids, anchor_status) == originals[tape[0]]
                trace.frozen = True
                frame = dict(
                    id=record["id"],
                    rep=rep,
                    anchor_seed=tape[0],
                    anchor_ids=anchor_ids,
                    anchor_status=anchor_status,
                    anchor_cost=elapsed(start),
                    anchor_forwards=trace.forwards,
                    cache_heads=len(trace.heads),
                    cache_bytes=trace.bytes,
                    status="IN_PROGRESS",
                )
                metadata["frames"].append(frame)
                metadata_path.write_text(json.dumps(metadata, indent=2) + "\n")
                counts = Counter()
                for index, seed in enumerate(tape):
                    start = stamp()
                    before = trace.queries, trace.hits, trace.forwards
                    candidate = CachedCandidate(factory, seed, actual.device, sites, trace)
                    row = dict(id=record["id"], rep=rep, index=index, seed=seed, status="PENDING")
                    try:
                        snapshot = candidate.pause()
                        raw_key = snapshot_key(snapshot, tokenizer, chat_length)
                        failure = (
                            candidate.boundary is not None
                            and candidate.boundary["line"] in sites["failures"]
                        )
                        key = ("ORIGINAL_FAILURE", *raw_key) if failure else raw_key
                        row.update(
                            key=key,
                            boundary=candidate.boundary,
                            stage_cost=elapsed(start),
                            stage_queries=trace.queries - before[0],
                            stage_hits=trace.hits - before[1],
                            stage_forwards=trace.forwards - before[2],
                            stage_ids=snapshot[0][0, chat_length:].tolist(),
                            ended=candidate.ended,
                        )
                        assert row["stage_forwards"] == 0
                        counts[key] += 1
                        if index < 2:
                            begin = stamp()
                            candidate.finish()
                            final_ids = candidate.current[0][0, chat_length:].tolist()
                            final_status = "COMPLETE" if candidate.current[2] else "INCOMPLETE"
                            assert (final_ids, final_status) == originals[seed]
                            row.update(
                                original_full_ids_preserved=True,
                                final_ids=final_ids,
                                final_status=final_status,
                                continuation_cost=elapsed(begin),
                            )
                        row["status"] = "OK"
                    except Exception as exc:
                        row.update(
                            status="ERROR",
                            error_type=type(exc).__name__,
                            error=str(exc),
                            attempt_cost=elapsed(start),
                        )
                    finally:
                        candidate.close()
                    row.update(
                        total_queries=trace.queries - before[0],
                        total_hits=trace.hits - before[1],
                        total_forwards=trace.forwards - before[2],
                    )
                    output.write(json.dumps(row, separators=(",", ":")) + "\n")
                    output.flush()
                    print(
                        record["id"],
                        rep,
                        seed,
                        row["status"],
                        row.get("key"),
                        row.get("stage_hits"),
                        flush=True,
                    )
                    if row["status"] != "OK":
                        raise RuntimeError("trace audit failed; original evidence retained")
                frame.update(
                    status="COMPLETE",
                    classes=[dict(key=k, count=n) for k, n in counts.items()],
                    new_forwards=trace.forwards,
                    peak_allocated=torch.cuda.max_memory_allocated(),
                    peak_reserved=torch.cuda.max_memory_reserved(),
                )
                metadata_path.write_text(json.dumps(metadata, indent=2) + "\n")
                anchor.close()
                trace.heads.clear()


if __name__ == "__main__":
    main()
