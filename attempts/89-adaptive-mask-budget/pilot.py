"""Frozen prospective A89 pilot. No training, external writes or vendor edits."""
from __future__ import annotations

import argparse
import hashlib
import importlib
import inspect
import json
import math
import os
import platform
import resource
import subprocess
import sys
import time
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / "vendor/EPIC-Decoding"))
os.environ["RAYON_NUM_THREADS"] = "4"
os.environ["CONSTRAINED_DIFFUSION_REGULAR_COVER_BATCH"] = "1"
os.environ["CONSTRAINED_DIFFUSION_REGULAR_COVER_EXACT"] = "1"
os.environ["CONSTRAINED_DIFFUSION_DFA_FREE_CHECKER"] = "1"
os.environ["TOKENIZERS_PARALLELISM"] = "false"

import torch
from transformers import AutoModel, AutoTokenizer, BitsAndBytesConfig

from verifier import EOS, EOT, MASK, Verifier, compile_library, compile_tables, insert_masks

MODEL = Path.home() / ".cache/huggingface/hub/models--GSAI-ML--LLaDA-8B-Instruct/snapshots/08b83a6feb34df1a6011b80c3c00c7563e963b07"


def sha(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def sync():
    torch.cuda.synchronize()


class Timings:
    def __init__(self):
        self.seconds, self.counts = defaultdict(float), defaultdict(int)

    def call(self, key, fn, *args, **kwargs):
        sync()
        start = time.perf_counter()
        try:
            return fn(*args, **kwargs)
        finally:
            sync()
            self.seconds[key] += time.perf_counter() - start
            self.counts[key] += 1


def prompt_tensor(tokenizer, case, device):
    text = tokenizer.apply_chat_template(
        [{"role":"user", "content":case["prompt"]}],
        tokenize=False, add_generation_prompt=True,
    )
    return tokenizer(text, return_tensors="pt").input_ids.to(device)


def evaluate(tokenizer, ids, expected):
    terminated = EOS in ids or EOT in ids
    end = next((i for i, v in enumerate(ids) if v in (EOS, EOT)), len(ids))
    text = tokenizer.decode(ids[:end], clean_up_tokenization_spaces=False)
    complete = terminated and MASK not in ids
    try:
        value = json.loads(text)
        valid_json = True
    except (ValueError, TypeError):
        value, valid_json = None, False
    # Validate the declared subset independently, rather than only the parser.
    def shape(x):
        return isinstance(x, list) and all(
            shape(v) if isinstance(v, list) else isinstance(v, str) and
            all(c.isascii() and c.isalpha() for c in v) for v in x)
    subset = valid_json and shape(value) and not any(c.isspace() for c in text)
    suffix_valid = all(v in (EOS, EOT) for v in ids[end:]) if terminated else False
    return dict(text=text, effective_tokens=end, terminated=terminated,
                complete=complete, json_valid=valid_json,
                valid=bool(complete and subset and suffix_valid),
                correct=bool(complete and subset and suffix_valid and value==expected))


def custom_decode(model, tokenizer, tables, verifier, case, mode, capacity, steps):
    timing = Timings()
    trace, events, expansions = [], [], []
    canvas_ids = [MASK] * capacity
    canvas = [-1] * capacity
    started = time.perf_counter()
    status, low = "budget", None
    inputs_sum, queries = 0, 0
    torch.cuda.reset_peak_memory_stats()
    torch.manual_seed(89001)
    try:
        prompt = timing.call("prompt", prompt_tensor, tokenizer, case, model.device)
        assert timing.call("verify_update", verifier.prepare, canvas)
        for step in range(steps):
            if time.perf_counter()-started > 60:
                raise TimeoutError("cooperative decode deadline 60s")
            free = [p for p, x in enumerate(canvas) if x < 0]
            if not free:
                status = "complete"
                break
            if mode == "simple_cpu" and step > 0 and low and low[0] < .1 and len(canvas)<96:
                gap = min(free, key=lambda p:(abs(p-low[1]),p))
                count = min(4,96-len(canvas))
                trial = canvas[:gap]+[-1]*count+canvas[gap:]
                if timing.call("verify_update", verifier.prepare, trial):
                    canvas, canvas_ids = trial, canvas_ids[:gap]+[MASK]*count+canvas_ids[gap:]
                    expansions.append(dict(step=step, inserted=count, gaps={str(gap):count},reason="low_confidence"))
                else:
                    timing.call("verify_update", verifier.prepare, canvas)
                free = [p for p, x in enumerate(canvas) if x < 0]
            tensor = timing.call("tensor", lambda:torch.cat([
                prompt,torch.tensor([canvas_ids],device=model.device,dtype=torch.long)],dim=1))
            inputs_sum += tensor.shape[1]
            logits = timing.call("model", lambda:model(tensor, use_cache=False).logits[0, prompt.shape[1]:])
            def ranked():
                free_t = torch.tensor(free, device=model.device)
                full = logits[free_t].float()
                normalizer = full.logsumexp(-1)
                allowed = torch.as_tensor(tables["admitted"], device=model.device)
                values, which = full[:,allowed].topk(8, dim=-1, sorted=True)
                ids = allowed[which]
                probabilities = (values[:,0]-normalizer).exp()
                return values.cpu().tolist(), ids.cpu().tolist(), probabilities.cpu().tolist()
            values, ids, probabilities = timing.call("ranking", ranked)
            low = min(zip(probabilities,free))
            candidates = sorted(
                ((-values[j][k],p,ids[j][k]) for j,p in enumerate(free) for k in range(8)),
                key=lambda x:(x[0],x[1],x[2]))
            quota = math.ceil(len(free)/(steps-step))
            remap = {p:p for p in free}
            committed, considered = set(), 0
            for score, original_pos, token in candidates:
                if len(committed) >= quota or considered>=256:
                    break
                if original_pos in committed:
                    continue
                pos = remap[original_pos]
                if canvas[pos] >= 0:
                    continue
                cls = int(tables["groups"][token])
                considered += 1
                queries += 1
                allowed = timing.call("verify_query", verifier.allows, pos, cls)
                required = 0
                if not allowed and mode.startswith("adaptive") and len(canvas)<96:
                    trial = list(canvas)
                    trial[pos] = cls
                    counts = timing.call("allocate", verifier.allocate, trial, 96-len(canvas))
                    if counts is not None:
                        required = sum(counts)
                        trial, shift = insert_masks(trial, counts)
                        canvas, _ = insert_masks(canvas, counts)
                        new_ids=[]
                        for i in range(len(canvas_ids)+1):
                            new_ids.extend([MASK]*counts[i])
                            if i<len(canvas_ids):
                                new_ids.append(canvas_ids[i])
                        canvas_ids = new_ids
                        remap = {p:shift[q] for p,q in remap.items()}
                        pos = remap[original_pos]
                        expansions.append(dict(step=step,inserted=required,
                            gaps={str(i):v for i,v in enumerate(counts) if v},reason="proposal_capacity"))
                        timing.call("verify_update", verifier.prepare, canvas)
                        assert timing.call("verify_query", verifier.allows, pos, cls)
                        allowed = True
                events.append([step,original_pos,pos,token,allowed,required])
                if not allowed:
                    continue
                canvas[pos], canvas_ids[pos] = cls, token
                committed.add(original_pos)
                # EOS's suffix consists only of EOS padding or unresolved slots.
                if token in (EOS,EOT):
                    for j in range(pos+1,len(canvas)):
                        assert canvas[j]<0 or canvas_ids[j] in (EOS,EOT)
                        canvas[j],canvas_ids[j] = cls,token
                    timing.call("verify_update", verifier.prepare, canvas)
                else:
                    assert timing.call("verify_update", verifier.prepare, canvas, pos)
            trace.append(list(canvas_ids))
        if MASK not in canvas_ids:
            status = "complete"
    except Exception as exc:
        status = type(exc).__name__+": "+str(exc)
    result = evaluate(tokenizer, canvas_ids, case["expected"])
    sync()
    result.update(seconds=time.perf_counter()-started,status=status,ids=canvas_ids,
                  trace=trace,events=events,expansions=expansions,
                  forwards=timing.counts["model"],input_tokens_sum=inputs_sum,
                  times=dict(timing.seconds),counts=dict(timing.counts),queries=queries,
                  final_capacity=len(canvas_ids),inserted=sum(e["inserted"] for e in expansions),
                  peak_allocated=torch.cuda.max_memory_allocated(),
                  peak_reserved=torch.cuda.max_memory_reserved(),
                  rss_peak_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024)
    return result


def prepare_epic(tokenizer, tables):
    from rustformlang.cfg import CFG
    from constrained_diffusion.constrain_utils import compile_lex_map, preprocessed_generate_stuff
    lg = importlib.import_module("constrained_diffusion.eval.dllm.models.llada.generate_constrained")
    cfg = CFG.from_text('''S -> left Items right
Items -> $ | Value Tail
Tail -> $ | comma Value Tail
Value -> string | S''',"S").to_normal_form()
    lexmap = compile_lex_map({"left":r"\[", "right":r"\]", "comma":",", "string":r'"[a-zA-Z]*"'})
    prepared = preprocessed_generate_stuff(tokenizer,cfg,lexmap,strip_chars="")
    source = inspect.getsource(lg.generate.__wrapped__)
    # Source-derived local function; preserved vendor files stay byte-identical.
    needle = "logits_with_noise = add_gumbel_noise(logits, temperature=temperature)"
    assert source.count(needle)==1
    source = source.replace(needle, needle+".clone()\n            logits_with_noise[..., _a89_invalid] = -torch.inf\n            _a89_probs = F.softmax(logits.to(torch.float64), dim=-1)")
    for lhs in ("p_batch", "p"):
        needle = f"{lhs} = F.softmax(logits.to(torch.float64), dim=-1)"
        assert source.count(needle)==1
        source = source.replace(needle, f"{lhs} = _a89_probs")
    needle = "for i in range(steps):"
    assert source.count(needle)==1
    source=source.replace(needle,needle+"\n            if not bool((x[:, prompt.shape[1]:] == mask_id).any()):\n                break")
    valid = torch.zeros(126464,dtype=torch.bool,device="cuda")
    valid[torch.as_tensor(tables["admitted"],device="cuda")]=True
    scope = dict(lg.__dict__)
    scope["_a89_invalid"] = ~valid
    exec(compile(source,str(HERE/"epic-common-optimizations"),"exec"),scope)
    return scope["generate"],dict(constraint_lang=cfg,lex_map=lexmap,
                                  additional_stuff=prepared,strip_chars=""),{
        "source_sha256":hashlib.sha256(source.encode()).hexdigest(),
        "vendor_source_sha256":sha(Path(lg.__file__)),
        "optimizations":["common lexical filter without renormalizing full-head confidence",
                         "one full softmax per forward", "omit empty forwards", "reuse lexical preparation"],
    }


def epic_decode(model,tokenizer,case,steps,epic_fn,epic_kw):
    from constrained_diffusion.constrain_utils import start_fast_enfa_instance
    from rustformlang.constraining import reset_lex_cache
    timing=Timings()
    started=time.perf_counter()
    torch.manual_seed(89001)
    torch.cuda.reset_peak_memory_stats()
    states,inputs_sum=[],0
    status="budget"
    final=[MASK]*96
    try:
        prompt=timing.call("prompt",prompt_tensor,tokenizer,case,model.device)
        start_fast_enfa_instance((case["id"],steps,started))
        reset_lex_cache()
        class Model:
            device=model.device
            def __call__(self,x):
                nonlocal inputs_sum
                if time.perf_counter()-started>60:
                    raise TimeoutError("cooperative EPIC deadline 60s")
                inputs_sum+=x.shape[1]
                return timing.call("model",lambda:model(x,use_cache=False))
        for last,resamples,complete in epic_fn(
            Model(),prompt,tokenizer,prompt_len=prompt.shape[1],
            steps=steps,gen_length=96,block_length=96,temperature=0.,
            max_resamples=100,trace=False,**epic_kw):
            final=last[0,prompt.shape[1]:].tolist()
            states.append(final)
            if time.perf_counter()-started>60:
                raise TimeoutError("cooperative EPIC deadline 60s")
        status="complete" if MASK not in final else "budget"
    except Exception as exc:
        status=type(exc).__name__+": "+str(exc)
    result=evaluate(tokenizer,final,case["expected"])
    sync()
    result.update(seconds=time.perf_counter()-started,status=status,ids=final,trace=states,
                  expansions=[],inserted=0,events=[],forwards=timing.counts["model"],
                  input_tokens_sum=inputs_sum,times=dict(timing.seconds),
                  counts=dict(timing.counts),final_capacity=96,
                  peak_allocated=torch.cuda.max_memory_allocated(),
                  peak_reserved=torch.cuda.max_memory_reserved(),
                  rss_peak_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024)
    return result


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--phase",choices=["val","test"],required=True)
    parser.add_argument("--output",type=Path,required=True)
    parser.add_argument("--selection",type=Path)
    args=parser.parse_args()
    if args.output.exists():
        raise SystemExit("Refusing to overwrite evidence")
    def record(data):
        with args.output.open("a") as stream:
            stream.write(json.dumps(data,ensure_ascii=False)+"\n")
        print(json.dumps({k:v for k,v in data.items() if k not in ("trace","events","ids")},ensure_ascii=False),flush=True)
    torch.set_num_threads(4)
    torch.manual_seed(89001)
    cases=json.loads((HERE/"evidence/inputs.json").read_text())
    sources={p.name:sha(p) for p in HERE.iterdir() if p.suffix in (".py",".cpp",".md")}
    record(dict(type="source",phase=args.phase,commit=subprocess.check_output(["git","rev-parse","HEAD"],text=True).strip(),
        sources=sources,inputs_sha256=sha(HERE/"evidence/inputs.json"),
        python=sys.version,platform=platform.platform(),torch=torch.__version__,
        gpu=torch.cuda.get_device_name(0),model_snapshot=MODEL.name,
        gpu_state=subprocess.check_output(["nvidia-smi"],text=True),
        model_metadata={p.name:sha(p) for p in MODEL.iterdir() if p.suffix in (".json",".py")},
        environment_reused="/home/jota/projects/tcc-final/.venv-live; only installed packages/weights reused"))
    if torch.cuda.mem_get_info()[0]<6.5*2**30:
        record(dict(type="refusal",reason="free GPU memory <6.5 GiB"))
        return
    started=time.perf_counter()
    tokenizer=AutoTokenizer.from_pretrained(MODEL,local_files_only=True,trust_remote_code=True)
    tables=compile_tables(tokenizer)
    lib,build=compile_library(ROOT/".cache/a89")
    cpu_start=time.perf_counter()
    cpu=Verifier(tables["table"],lib)
    cpu_seconds=time.perf_counter()-cpu_start
    gpu_start=time.perf_counter()
    gpu=Verifier(tables["table"],lib,"cuda")
    sync()
    record(dict(type="verifier_prepare",seconds=time.perf_counter()-started,
                compiler=build,tokenize_compile_s=tables["seconds"],states=cpu.s,
                cpu_init_seconds=cpu_seconds,gpu_init_seconds=time.perf_counter()-gpu_start,
                classes=len(tables["table"]),admitted_ids=len(tables["admitted"]),
                depth_bound=tables["depth"],table_bytes=tables["table"].nbytes,
                gpu_allocated=torch.cuda.memory_allocated(),vocab_sha256=tables["vocab_sha256"]))
    started=time.perf_counter()
    epic_fn,epic_kw,epic_info=prepare_epic(tokenizer,tables)
    sync()
    record(dict(type="epic_prepare",seconds=time.perf_counter()-started,**epic_info))
    started=time.perf_counter()
    model=AutoModel.from_pretrained(MODEL,local_files_only=True,trust_remote_code=True,
        device_map={"":0},torch_dtype=torch.bfloat16,low_cpu_mem_usage=True,
        quantization_config=BitsAndBytesConfig(load_in_4bit=True,bnb_4bit_quant_type="nf4",
            bnb_4bit_use_double_quant=True,bnb_4bit_compute_dtype=torch.bfloat16)).eval()
    sync()
    record(dict(type="model_load",seconds=time.perf_counter()-started,allocated=torch.cuda.memory_allocated()))
    with torch.inference_mode():
        start=time.perf_counter()
        model(torch.tensor([[EOS,MASK]],device=model.device),use_cache=False)
        sync()
        record(dict(type="warmup",seconds=time.perf_counter()-start))
        selected=json.loads(args.selection.read_text()) if args.selection else None
        index=0
        for case in cases:
            if case["split"]!=args.phase.upper():
                continue
            for steps in (8,16):
                if args.phase=="val":
                    base=[("fixed_cpu",32),("fixed_cpu",64),("fixed_cpu",96),
                          ("adaptive_cpu",32),("simple_cpu",32),("epic",96)]
                    repetitions=1
                else:
                    cap=selected[case["family"]]["capacity"]
                    base=[("fixed_cpu",cap),("fixed_gpu",cap),("adaptive_cpu",32),
                          ("adaptive_gpu",32),("simple_cpu",32),("reserve_cpu",96),("epic",96)]
                    repetitions=3
                for rep in range(repetitions):
                    shift=(index+rep)%len(base)
                    order=base[shift:]+base[:shift]
                    for mode,cap in order:
                        backend=gpu if mode.endswith("gpu") else cpu
                        result=(epic_decode(model,tokenizer,case,steps,epic_fn,epic_kw) if mode=="epic"
                                else custom_decode(model,tokenizer,tables,backend,case,mode,cap,steps))
                        record(dict(type="decode",case=case["id"],family=case["family"],split=case["split"],
                                    mode=mode,initial_capacity=cap,steps=steps,rep=rep,**result))
                    index+=1
    record(dict(type="end",phase=args.phase,gpu_allocated=torch.cuda.memory_allocated()))


if __name__=="__main__":
    main()
