"""Opt-in full-generation evaluation; no mutable imports from another attempt."""

import argparse
import gc
import hashlib
import json
import os
import platform
import signal
import subprocess
from pathlib import Path
from random import Random
from time import perf_counter, process_time

from enumeration import Enumeration
from grammar_selectors import CachedPrefix, Recompute
from monotone import Monotone
from native_sat import SatPrefix

from mwpc_exact.cfg_posterior import CompilationLimit, compile_cfg_sampler
from mwpc_exact.eos_policy import EOSMode, EOSPolicy
from mwpc_exact.reference.json_grammar import json_source_grammar
from mwpc_exact.reference.normalization import normalize_to_cnf
from mwpc_exact.state import SelectionInput
from mwpc_exact.support import SupportPolicy, build_per_position_support
from mwpc_exact.tokenizer_bytes import CompositionalByteLevelAdapter
from mwpc_exact.types import SupportKind

WORK = Path(__file__).resolve().parent
ROOT = WORK.parents[2]


def digest(data):
    return hashlib.sha256(data).hexdigest()


def select_documents(folder, tokenizer, protocol):
    found = {}
    low, high = protocol["external"]["eligible_tokens"]
    for path in sorted((folder / "tests/draft2020-12").glob("*.json")):
        for group in json.loads(path.read_text()):
            for test in group["tests"]:
                if not isinstance(test["data"], (dict, list)):
                    continue
                text = json.dumps(
                    test["data"], sort_keys=True, separators=(",", ":"), ensure_ascii=True
                )
                tokens = tokenizer.encode(text, add_special_tokens=False)
                if low <= len(tokens) <= high:
                    key = digest(f"{protocol['seed']}/{text}".encode())
                    found.setdefault(
                        key,
                        dict(
                            key=key,
                            text=text,
                            tokens=tokens,
                            file=path.name,
                            description=test["description"],
                        ),
                    )
    ordered = [found[k] for k in sorted(found)]
    if len(ordered) < 18:
        raise ValueError("fewer than predeclared external documents")
    return ordered[:6], ordered[6:18]


def deadline(signum, frame):
    raise TimeoutError("generation_total_deadline")


def run_case(model, adapter, source, grammar, example, size, method, config, protocol):
    import torch

    device = next(model.parameters()).device
    cuda = device.type == "cuda"
    if cuda:
        torch.cuda.synchronize()
        torch.cuda.reset_peak_memory_stats()
    original = example["tokens"]
    positions = sorted(
        Random(protocol["seed"] + int(example["key"][:12], 16) + size).sample(
            range(len(original)), size
        )
    )
    canvas = [None if i in positions else t for i, t in enumerate(original)]
    trace, clocks, engine = [], {}, None
    started, cpu_started = perf_counter(), process_time()
    result = dict(
        case=example["key"],
        mask_count=size,
        method=method,
        mask_positions=positions,
        status="error",
        trace=trace,
    )
    signal.signal(signal.SIGALRM, deadline)
    signal.setitimer(signal.ITIMER_REAL, protocol["measurement"]["total_seconds"])

    def clock(name, function):
        if cuda:
            torch.cuda.synchronize()
        wall, cpu = perf_counter(), process_time()
        value = function()
        if cuda:
            torch.cuda.synchronize()
        old = clocks.setdefault(name, dict(wall=0.0, cpu=0.0))
        old["wall"] += perf_counter() - wall
        old["cpu"] += process_time() - cpu
        return value

    def forward():
        ids = [config["mask_token_id"] if t is None else t for t in canvas]
        with torch.inference_mode():
            return model(
                input_ids=torch.tensor([ids], device=device),
                timesteps=torch.zeros(1, device=device),
            )[0]

    def predictions(logits):
        values = logits.to(device="cpu", dtype=torch.float64).clone()
        values[:, config["mask_token_id"]] = float("-inf")
        return values.softmax(-1)

    try:
        initial = clock("forward", forward)
        probabilities = clock("probabilities", lambda: predictions(initial))

        def state_from_top():
            rows = {}
            for p, token in enumerate(canvas):
                rows[p] = (
                    (token,)
                    if token is not None
                    else tuple(
                        sorted(probabilities[p].argsort(descending=True, stable=True)[:16].tolist())
                    )
                )
            support = build_per_position_support(
                canvas=tuple(canvas),
                policy=SupportPolicy(
                    kind=SupportKind.EXPLICIT,
                    vocabulary_size=adapter.vocabulary_size,
                    pruning_description="initial top16, no answer injection",
                ),
                explicit_support=rows,
            )
            return SelectionInput(
                grammar, tuple(canvas), (), support, adapter, EOSPolicy(EOSMode.ABSENT)
            )

        state = clock("support", state_from_top)
        result["support_rows"] = state.support.rows
        result["support_sha256"] = state.support.fingerprint
        if method == "enumeration":
            engine = clock("prepare", lambda: Enumeration(state))
        else:
            limits = protocol["measurement"]["compilation_limits"]
            plan = clock(
                "compile",
                lambda: compile_cfg_sampler(
                    source,
                    state,
                    timeout_seconds=limits["seconds"],
                    max_chart_cells=limits["cells"],
                    max_alternatives=limits["alternatives"],
                ),
            )
            result["forest"] = dict(nodes=len(plan.terms), alternatives=plan.alternatives)
            factories = {
                "monotone": Monotone,
                "greedy_witness": Recompute,
                "lex_integer": lambda p: Recompute(p, lex=True),
                "greedy_cached_prefix": CachedPrefix,
                "sat_cached_prefix": SatPrefix,
            }
            engine = clock("prepare", lambda: factories[method](plan))
        for step in range(protocol["operation"]["max_forwards"]):
            if step:
                logits = clock("forward", forward)
                probabilities = clock("probabilities", lambda values=logits: predictions(values))

            def propose(probs=probabilities):
                proposals = []
                for p, row in enumerate(state.support.rows):
                    if canvas[p] is not None:
                        continue
                    token = min(row, key=lambda t: (-float(probs[p, t]), t))
                    proposals.append((p, token, float(probs[p, token])))
                return sorted(proposals, key=lambda p: (-p[2], p[0], p[1]))

            proposals = clock("proposals", propose)
            updates = clock(
                "select",
                lambda candidates=proposals: engine.transition(
                    candidates,
                    threshold=protocol["operation"]["threshold"],
                    cap=protocol["operation"]["commit_cap"],
                ),
            )
            before = list(canvas)

            def apply(changes=updates):
                for p, token in changes:
                    if canvas[p] is not None or token not in state.support.rows[p]:
                        raise RuntimeError("invalid observable commitment")
                    canvas[p] = token

            clock("update", apply)
            trace.append(dict(canvas=before, proposals=proposals, updates=updates))
            if None not in canvas:
                break
        if None in canvas:
            result["status"] = "forward_limit"
        else:

            def validate():
                text = adapter.detokenize_bytes(tuple(canvas)).decode()
                json.loads(text, parse_constant=Enumeration.reject_constant)
                for p, token in enumerate(original):
                    if p not in positions and canvas[p] != token:
                        raise RuntimeError("changed original fixed position")
                return text

            result.update(status="complete", output=clock("output", validate), tokens=canvas)
        if hasattr(engine, "deactivated"):
            result["propagation"] = dict(
                deactivated=engine.deactivated, flow_removed=engine.flow_removed
            )
        if hasattr(engine, "calls"):
            result["oracle_calls"] = engine.calls
        if hasattr(engine, "valid_paths"):
            result["valid_paths"] = engine.valid_paths
    except OverflowError as exc:
        result.update(status="not_applicable", reason=str(exc))
    except (CompilationLimit, TimeoutError) as exc:
        result.update(status="unresolved", reason=str(exc))
    except ValueError as exc:
        result.update(
            status="infeasible_on_support" if str(exc) == "infeasible_on_support" else "error",
            reason=str(exc),
        )
    except (RuntimeError, TypeError, AttributeError) as exc:
        result.update(status="error", reason=f"{type(exc).__name__}: {exc}")
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        # Required cleanup belongs to total cost.
        if engine is not None and hasattr(engine, "close"):
            engine.close()
        if cuda:
            torch.cuda.synchronize()
            result["gpu_peak_allocated_bytes"] = torch.cuda.max_memory_allocated()
        result.update(
            wall=perf_counter() - started,
            cpu=process_time() - cpu_started,
            components=clocks,
            load_average=os.getloadavg(),
        )
    return result


def main():
    from importlib.metadata import version

    import torch
    from scripts.exact_commit.mdlm_cpu import load_cpu_model
    from transformers import AutoTokenizer

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--phase", choices=("development", "heldout"), required=True)
    parser.add_argument("--device", choices=("cpu", "cuda"), default="cpu")
    args = parser.parse_args()
    if subprocess.check_output(["git", "status", "--porcelain"], cwd=ROOT).strip():
        raise ValueError("commit source/protocol before measurement")
    protocol = json.loads((WORK / "protocol.json").read_text())
    config = json.loads((ROOT / protocol["model_config"]).read_text())
    torch.set_num_threads(config["torch_cpu_threads"])
    torch.manual_seed(protocol["seed"])
    if args.device == "cuda":
        torch.backends.cuda.matmul.allow_tf32 = False
        torch.backends.cudnn.allow_tf32 = False
    tokenizer = AutoTokenizer.from_pretrained(
        config["tokenizer_id"],
        revision=config["tokenizer_revision"],
        cache_dir=str(ROOT / ".cache/mdlm"),
        local_files_only=True,
    )
    dev, heldout = select_documents(args.source, tokenizer, protocol)
    selected = dev if args.phase == "development" else heldout
    model, hashes, adapted = load_cpu_model(config, ROOT / ".cache/mdlm")
    model.to(args.device)
    for parameter in model.parameters():
        parameter.requires_grad_(False)
    adapter = CompositionalByteLevelAdapter.from_token_pieces(
        (
            *(
                tokenizer.convert_ids_to_tokens(i) if i not in tokenizer.all_special_ids else None
                for i in range(len(tokenizer))
            ),
            None,
        )
    )
    source = json_source_grammar()
    grammar = normalize_to_cnf(source).grammar
    args.output.mkdir(parents=True, exist_ok=False)
    metadata = dict(
        commit=subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        phase=args.phase,
        protocol_sha256=digest((WORK / "protocol.json").read_bytes()),
        model_config=config,
        model_hashes=hashes,
        adapted_model_sha256=adapted,
        grammar_sha256=digest(json.dumps(grammar.to_dict(), sort_keys=True).encode()),
        tokenizer=config["tokenizer_revision"],
        adapter_sha256=digest(
            json.dumps([None if b is None else b.hex() for b in adapter.emissions]).encode()
        ),
        selected=selected,
        development_keys=[x["key"] for x in dev],
        heldout_keys=[x["key"] for x in heldout],
        device=args.device,
        gpu_addendum_sha256=digest((WORK / "gpu-addendum.json").read_bytes())
        if args.device == "cuda"
        else None,
        gpu=torch.cuda.get_device_name() if args.device == "cuda" else None,
        cuda_version=torch.version.cuda if args.device == "cuda" else None,
        python=platform.python_version(),
        platform=platform.platform(),
        versions={n: version(n) for n in ("torch", "numpy", "transformers", "python-sat")},
        cpu=next(
            line.split(":", 1)[1].strip()
            for line in Path("/proc/cpuinfo").read_text().splitlines()
            if line.startswith("model name")
        ),
        threads=torch.get_num_threads(),
        load_average=os.getloadavg(),
    )
    (args.output / "metadata.json").write_text(json.dumps(metadata, indent=2) + "\n")
    with torch.inference_mode():
        model(
            input_ids=torch.full(
                (1, 32), config["mask_token_id"], dtype=torch.long, device=args.device
            ),
            timesteps=torch.zeros(1, device=args.device),
        )
    if args.device == "cuda":
        torch.cuda.synchronize()
    with (args.output / "rows.jsonl").open("x") as output:
        for repetition in range(protocol["measurement"]["repetitions"]):
            for i, example in enumerate(selected):
                for size in protocol["operation"]["mask_counts"]:
                    methods = protocol["methods"]
                    shift = (i + repetition) % len(methods)
                    for method in methods[shift:] + methods[:shift]:
                        gc.collect()
                        row = run_case(
                            model, adapter, source, grammar, example, size, method, config, protocol
                        )
                        row["repetition"] = repetition
                        output.write(json.dumps(row) + "\n")
                        output.flush()
                        print(
                            json.dumps(
                                {
                                    k: row[k]
                                    for k in (
                                        "case",
                                        "mask_count",
                                        "method",
                                        "repetition",
                                        "status",
                                        "wall",
                                    )
                                }
                            ),
                            flush=True,
                        )
                        if row["status"] == "error":
                            raise RuntimeError(f"recorded harness/algorithm error: {row['reason']}")


if __name__ == "__main__":
    main()
