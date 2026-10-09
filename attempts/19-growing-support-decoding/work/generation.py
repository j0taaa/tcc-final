"""Opt-in full-generation evaluation; no mutable imports from another attempt."""

import argparse
import gc
import hashlib
import json
import os
import platform
import signal
import subprocess
from dataclasses import replace
from pathlib import Path
from random import Random
from time import perf_counter, process_time

from mwpc_exact.cfg_posterior import CompilationLimit, _binarize_source, compile_cfg_sampler
from mwpc_exact.eos_policy import EOSMode, EOSPolicy
from mwpc_exact.reference.json_grammar import json_source_grammar
from mwpc_exact.reference.limits import WorkBudget
from mwpc_exact.reference.ll1 import check_ll1
from mwpc_exact.reference.normalization import normalize_to_cnf
from mwpc_exact.state import SelectionInput
from mwpc_exact.support import SupportPolicy, build_per_position_support
from mwpc_exact.tokenizer_bytes import CompositionalByteLevelAdapter
from mwpc_exact.types import SupportKind

from .adaptive_domains import union_rows
from .enumeration import Enumeration
from .grammar_selectors import CachedPrefix, Recompute
from .monotone import Monotone
from .native_queries import NativeCountWarm, NativeLex, NativePrefix, NativeSpeculative
from .native_sat import SatPrefix
from .relevant_forest import relevant_forest
from .reservoir_sat import ReserveSat
from .rooted_selectors import RootCountWarm, RootLex, RootPrefix, RootSpeculative, compile_rooted
from .shared_fastpath import complete_point, keep_engine, stable_topk

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
    if len(ordered) < 24:
        raise ValueError("fewer than predeclared external documents")
    return ordered[:6], ordered[6:18], ordered[18:24]


def deadline(signum, frame):
    raise TimeoutError("generation_total_deadline")


def run_case(
    model,
    adapter,
    source,
    grammar,
    example,
    size,
    method,
    config,
    protocol,
    trim=False,
    compressed=False,
    native_grammar=None,
    rooted=False,
    growing=False,
):
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
    trace, clocks, engine, reserve_rows = [], {}, None, None
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
                    else tuple(sorted(stable_topk(probabilities[p], 16)))
                )
            support = build_per_position_support(
                canvas=tuple(canvas),
                policy=SupportPolicy(
                    kind=SupportKind.EXPLICIT,
                    vocabulary_size=adapter.vocabulary_size,
                    pruning_description="model-driven top16 union, no answer injection",
                ),
                explicit_support=rows,
            )
            return SelectionInput(
                grammar, tuple(canvas), (), support, adapter, EOSPolicy(EOSMode.ABSENT)
            )

        state = clock("support", state_from_top)
        result["support_rows"] = state.support.rows
        result["support_sha256"] = state.support.fingerprint

        def prepare_engine():
            nonlocal engine, reserve_rows
            result["engine_preparations"] = result.get("engine_preparations", 0) + 1
            current_canvas = tuple(canvas)
            rows = tuple(
                (t,) if t is not None else row
                for t, row in zip(canvas, state.support.rows, strict=True)
            )
            restricted = replace(
                state.support,
                canvas=current_canvas,
                rows=rows,
                permitted_token_ids=tuple(sorted({t for row in rows for t in row})),
            )
            current_state = replace(state, canvas=current_canvas, support=restricted)
            if method.startswith("sat_reserve_"):
                width = int(method.rsplit("_", 1)[-1])

                def reserve():
                    basis = state.support.rows if reserve_rows is None else reserve_rows
                    tops = {
                        p: stable_topk(probabilities[p], width)
                        for p, t in enumerate(canvas)
                        if t is None
                    }
                    return union_rows(
                        basis,
                        canvas,
                        {
                            p: set(state.support.rows[p]).union(tops.get(p, ()))
                            for p in range(len(canvas))
                        },
                    )

                reserve_rows = clock("reserve_support", reserve)
                reserve_state = replace(
                    current_state,
                    support=replace(
                        restricted,
                        rows=reserve_rows,
                        permitted_token_ids=tuple(sorted({t for row in reserve_rows for t in row})),
                    ),
                )
                limits = protocol["measurement"]["reservoir_limits"]
                plan = clock(
                    "compile",
                    lambda: compile_rooted(
                        reserve_state,
                        native_grammar,
                        max_cells=limits["cells"],
                        max_terms=limits["alternatives"],
                        timeout_seconds=limits["seconds"],
                    ),
                )
                result.setdefault("reserve_preparations", []).append(
                    dict(
                        widths=list(map(len, reserve_rows)),
                        nodes=len(plan.terms),
                        alternatives=plan.alternatives,
                    )
                )
                plan = clock("root_pruning", lambda: relevant_forest(plan))
                engine = clock("prepare", lambda: ReserveSat(plan, state.support.rows))
            elif method.startswith("root_"):
                factories = {
                    "root_lex": RootLex,
                    "root_cached_prefix": RootPrefix,
                    "root_lazy_prefix": lambda s, **kw: RootPrefix(s, lazy=True, **kw),
                    "root_count_warm": RootCountWarm,
                    "root_speculative": RootSpeculative,
                }
                engine = clock(
                    "prepare", lambda: factories[method](current_state, grammar=native_grammar)
                )
            elif method.startswith("rust_"):
                native_kwargs = dict(compressed=compressed, grammar=native_grammar)
                factories = {
                    "rust_lex": lambda s: NativeLex(s, **native_kwargs),
                    "rust_cached_prefix": lambda s: NativePrefix(s, **native_kwargs),
                    "rust_lazy_prefix": lambda s: NativePrefix(s, lazy=True, **native_kwargs),
                    "rust_count_warm": lambda s: NativeCountWarm(s, **native_kwargs),
                    "rust_speculative": lambda s: NativeSpeculative(s, **native_kwargs),
                }
                engine = clock("prepare", lambda: factories[method](current_state))
            elif method == "enumeration":
                engine = clock("prepare", lambda: Enumeration(current_state))
            else:
                limits = protocol["measurement"]["compilation_limits"]
                if rooted:
                    plan = clock(
                        "compile",
                        lambda: compile_rooted(
                            current_state,
                            native_grammar,
                            max_cells=limits["cells"],
                            max_terms=limits["alternatives"],
                        ),
                    )
                else:
                    plan = clock(
                        "compile",
                        lambda: compile_cfg_sampler(
                            source,
                            current_state,
                            timeout_seconds=limits["seconds"],
                            max_chart_cells=limits["cells"],
                            max_alternatives=limits["alternatives"],
                        ),
                    )
                result["raw_forest"] = dict(nodes=len(plan.terms), alternatives=plan.alternatives)
                if trim:
                    plan = clock("root_pruning", lambda: relevant_forest(plan))
                result["forest"] = dict(nodes=len(plan.terms), alternatives=plan.alternatives)
                result.setdefault("forest_preparations", []).append(dict(result["forest"]))
                factories = {
                    "monotone": Monotone,
                    "greedy_witness": Recompute,
                    "lex_integer": lambda p: Recompute(p, lex=True),
                    "greedy_cached_prefix": CachedPrefix,
                    "sat_cached_prefix": SatPrefix,
                }
                engine = clock("prepare", lambda: factories[method](plan))

        for step in range(protocol["operation"]["max_forwards"]):
            additions = []
            if step:
                logits = clock("forward", forward)
                probabilities = clock("probabilities", lambda values=logits: predictions(values))
                if growing:

                    def expand(probs=probabilities, delta=additions):
                        nonlocal state, engine
                        tops = {
                            p: stable_topk(probs[p], 16) for p, t in enumerate(canvas) if t is None
                        }
                        rows = union_rows(state.support.rows, canvas, tops)
                        for p, top in tops.items():
                            new = sorted(set(top).difference(state.support.rows[p]))
                            if new:
                                delta.append((p, new))
                        state = replace(
                            state,
                            canvas=tuple(canvas),
                            support=replace(
                                state.support,
                                canvas=tuple(canvas),
                                rows=rows,
                                permitted_token_ids=tuple(sorted({t for row in rows for t in row})),
                            ),
                        )
                        if engine is not None:
                            covered = method.startswith("sat_reserve_") and all(
                                set(row).issubset(reserve_rows[p]) for p, row in enumerate(rows)
                            )
                            if covered:
                                engine.update_domains(rows)
                            elif delta:
                                if hasattr(engine, "close"):
                                    engine.close()
                                engine = None

                    clock("support_update", expand)

            def propose(probs=probabilities):
                proposals = []
                for p, row in enumerate(state.support.rows):
                    if canvas[p] is not None:
                        continue
                    token = min(row, key=lambda t: (-float(probs[p, t]), t))
                    proposals.append((p, token, float(probs[p, token])))
                return sorted(proposals, key=lambda p: (-p[2], p[0], p[1]))

            proposals = clock("proposals", propose)
            point = clock(
                "fastpath",
                lambda candidates=proposals: complete_point(
                    canvas,
                    state.support.rows,
                    adapter,
                    candidates,
                    threshold=protocol["operation"]["threshold"],
                    cap=protocol["operation"]["commit_cap"],
                ),
            )
            if point is not None:
                updates, witness = point
                result["fastpath_steps"] = result.get("fastpath_steps", 0) + 1
                if engine is not None:
                    clock(
                        "select",
                        lambda changes=updates, word=witness: keep_engine(engine, changes, word),
                    )
            else:
                if engine is None:
                    prepare_engine()
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
            trace.append(
                dict(
                    canvas=before, proposals=proposals, updates=updates, support_additions=additions
                )
            )
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
        if hasattr(engine, "speculative_successes"):
            result["speculative_successes"] = engine.speculative_successes
        if hasattr(engine, "valid_paths"):
            result["valid_paths"] = engine.valid_paths
    except OverflowError as exc:
        result.update(status="not_applicable", reason=str(exc))
    except (CompilationLimit, TimeoutError) as exc:
        result.update(status="unresolved", reason=str(exc))
    except NotImplementedError as exc:
        result.update(status="unsupported", reason=str(exc))
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
    parser.add_argument("--phase", choices=("development", "heldout", "fresh"), required=True)
    parser.add_argument("--device", choices=("cpu", "cuda"), default="cpu")
    parser.add_argument(
        "--trim", action="store_true", help="Shared classical root-dependency pruning"
    )
    parser.add_argument(
        "--native", action="store_true", help="Include exact native lex/prefix controls"
    )
    parser.add_argument(
        "--compressed", action="store_true", help="Common native trie and compact CNF"
    )
    parser.add_argument("--rooted", action="store_true", help="Rooted parser for all controls")
    parser.add_argument("--growing", action="store_true", help="Current top16 union and reserves")
    args = parser.parse_args()
    if subprocess.check_output(["git", "status", "--porcelain"], cwd=ROOT).strip():
        raise ValueError("commit source/protocol before measurement")
    protocol = json.loads((WORK / "protocol.json").read_text())
    if args.compressed and not args.native:
        raise ValueError("compression refinement requires all native controls")
    if args.rooted and not args.compressed:
        raise ValueError("rooted refinement requires all compressed native controls")
    if not args.growing or not args.rooted:
        raise ValueError("attempt19 requires --growing --rooted and all native controls")
    if args.phase == "fresh":
        protocol["measurement"]["repetitions"] = protocol["measurement"]["fresh_repetitions"]
    binding = None
    if args.native:
        if not args.trim:
            raise ValueError("native refinement requires strong root-pruned forest controls")
        import mwpc_parser_py

        binaries = list(Path(mwpc_parser_py.__file__).parent.glob("*.so"))
        if len(binaries) != 1:
            raise ValueError("expected one pinned native parser binding")
        binding = dict(filename=binaries[0].name, sha256=digest(binaries[0].read_bytes()))
        protocol["methods"] += ["rust_lex", "rust_cached_prefix", "rust_lazy_prefix"]
        if args.compressed:
            protocol["methods"].append("rust_count_warm")
    if args.rooted:
        protocol["methods"] += [
            "root_lex",
            "root_cached_prefix",
            "root_lazy_prefix",
            "root_count_warm",
            "root_speculative",
            "rust_speculative",
        ]
    if args.growing:
        protocol["methods"] += ["sat_reserve_32", "sat_reserve_64", "sat_reserve_128"]
    config = json.loads((ROOT / protocol["model_config"]).read_text())
    torch.set_num_threads(config["torch_cpu_threads"])
    torch.set_flush_denormal(False)
    torch.manual_seed(protocol["seed"])
    if args.device == "cuda":
        torch.backends.cuda.matmul.allow_tf32 = False
        torch.backends.cudnn.allow_tf32 = False
    startup_wall, startup_cpu = perf_counter(), process_time()
    tokenizer = AutoTokenizer.from_pretrained(
        config["tokenizer_id"],
        revision=config["tokenizer_revision"],
        cache_dir=str(ROOT / ".cache/mdlm"),
        local_files_only=True,
    )
    dev, heldout, fresh = select_documents(args.source, tokenizer, protocol)
    selected = {"development": dev, "heldout": heldout, "fresh": fresh}[args.phase]
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
    if args.rooted:
        check_ll1(source, budget=WorkBudget(max_work=1_000_000))
    grammar = normalize_to_cnf(source).grammar
    native_grammar = None
    if args.compressed:
        budget = WorkBudget(max_work=1_000_000)
        native_grammar = normalize_to_cnf(_binarize_source(source, budget), budget=budget).grammar
    if args.device == "cuda":
        torch.cuda.synchronize()
    args.output.mkdir(parents=True, exist_ok=False)
    metadata = dict(
        commit=subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        phase=args.phase,
        methods=protocol["methods"],
        repetitions=protocol["measurement"]["repetitions"],
        native_binding=binding,
        shared_work_addendum_sha256=digest((WORK / "shared-work-addendum.json").read_bytes()),
        native_compression=args.compressed,
        rooted_parser=args.rooted,
        growing_support=args.growing,
        rooted_addendum_sha256=digest((WORK / "rooted-addendum.json").read_bytes())
        if args.rooted
        else None,
        native_grammar_sha256=digest(json.dumps(native_grammar.to_dict(), sort_keys=True).encode())
        if native_grammar is not None
        else None,
        compression_addendum_sha256=digest((WORK / "compression-addendum.json").read_bytes())
        if args.compressed
        else None,
        ieee_subnormals="CPU flush_denormal explicitly false; rank transport decoded as exact bits",
        native_addendum_sha256=digest((WORK / "native-addendum.json").read_bytes())
        if args.native
        else None,
        common_startup=dict(
            wall=perf_counter() - startup_wall,
            cpu=process_time() - startup_cpu,
            scope="tokenizer, corpus tokenization/selection, model loading/device, byte adapter "
            "and shared fixed grammar; excluded from prepared-service decoder times",
        ),
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
        root_pruning=args.trim,
        relevance_addendum_sha256=digest((WORK / "relevance-addendum.json").read_bytes())
        if args.trim
        else None,
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
                            model,
                            adapter,
                            source,
                            grammar,
                            example,
                            size,
                            method,
                            config,
                            protocol,
                            trim=args.trim,
                            compressed=args.compressed,
                            native_grammar=native_grammar,
                            rooted=args.rooted,
                            growing=args.growing,
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
