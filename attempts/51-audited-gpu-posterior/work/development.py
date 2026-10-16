"""Frozen first90 negative-only complete-query cost records on ALL15 OLD heads."""

import argparse
import gc
import hashlib
import importlib
import json
import resource
import signal
import subprocess
from fractions import Fraction as F
from pathlib import Path
from random import Random
from time import perf_counter, process_time

import numpy as np
import torch

from mwpc_exact.tokenizer_bytes import CompositionalByteLevelAdapter

from .cost_audit import METHODS, audit
from .exact_control import ExactDAG
from .frozen_compiler import load
from .interval_sampler import IntervalSampler
from .ticket_sampler import TicketSampler


def now():
    return perf_counter(), process_time()


def elapsed(start):
    return dict(wall=perf_counter() - start[0], cpu=process_time() - start[1])


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def encode(value):
    if isinstance(value, F):
        return str(value)
    raise TypeError(type(value).__name__)


def alarm(_a, _b):
    raise TimeoutError("declared operation deadline")


class API:
    def __init__(self, method, classes, layers, accepting, canvas, seed, protocol):
        self.method, self.protocol = method, protocol
        self.sampler = (TicketSampler if method == "ticket_scalar" else IntervalSampler)(
            classes, layers, accepting
        )
        self.free = torch.tensor([t is None for t in canvas], dtype=torch.bool, device="cuda")
        self.generator = torch.Generator(device="cuda").manual_seed(seed)
        self.rng = Random(seed)
        self.length = len(canvas)

    def query(self, weights):
        info = {}
        if self.method == "ticket_scalar":
            p = self.sampler.prepare(
                weights, minimum_acceptance=F(self.protocol["candidate_minimum_acceptance"])
            )
            r = self.sampler.sample_prepared(
                p,
                1,
                self.rng,
                generator=self.generator,
                max_trials=self.protocol["candidate_fixed_trial_cap"],
            )
            if r["statuses"] != ["COMPLETE"]:
                raise ValueError("explicit finite-budget FAIL; no output credit")
            info = dict(
                acceptance_lower=p["acceptance_lower"],
                envelope=p["envelope"],
                mass_lower=p["frontend"]["lower"],
                mass_upper=p["frontend"]["upper"],
                proposals=r["proposals"],
                fail_bound=r["fail_bound"],
            )
        else:
            source = torch.randint(
                0,
                1 << 32,
                (1, self.length, 3),
                dtype=torch.long,
                device="cuda",
                generator=self.generator,
            )
            r = self.sampler.sample(weights, source, [self.rng])
            info = dict(
                exact_fallbacks=r["fallback_count"],
                mass_lower=r["mass_lower"],
                mass_upper=r["mass_upper"],
            )
        word = r["tokens"][0]
        confidence = weights.gather(1, word[:, None]).squeeze(1)
        commit = self.free & (confidence >= 0.95)
        if not bool(commit.any()):
            chosen = confidence.masked_fill(~self.free, -1).argmax()
            commit[chosen] = True
        return dict(tokens=word, confidence=confidence, commit_mask=commit, info=info)


def validate(result, canvas, dense, adapter, exact_mass):
    word = tuple(result["tokens"].cpu().tolist())
    if any(t is not None and word[p] != t for p, t in enumerate(canvas)):
        raise AssertionError("fixed original ID changed")
    stop = word.index(50256)
    if any(t != 50256 for t in word[stop + 1 :]):
        raise AssertionError("EOT/PAD changed")
    json.loads(
        adapter.detokenize_bytes(word[:stop]).decode("utf8"),
        parse_constant=lambda _: (_ for _ in ()).throw(ValueError()),
    )
    expected = [dense[p, t] for p, t in enumerate(word)]
    if result["confidence"].cpu().tolist() != expected:
        raise AssertionError("given model confidence changed")
    free = [p for p, t in enumerate(canvas) if t is None]
    committed = [p for p in free if expected[p] >= 0.95]
    if not committed:
        committed = [min(free, key=lambda p: (-expected[p], p))]
    actual = result["commit_mask"].nonzero().flatten().cpu().tolist()
    if actual != committed:
        raise AssertionError("common model-confidence policy changed")
    info = result["info"]
    lo, hi = F(info["mass_lower"]), F(info["mass_upper"])
    if not lo <= exact_mass <= hi:
        raise AssertionError("mass interval failed independent exact oracle")
    if "envelope" in info and F(info["envelope"]) < exact_mass:
        raise AssertionError("rejection envelope below target mass")
    return dict(correctness=True, original_ids=word, selected=actual, **info)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    subprocess.run(["git", "diff", "--quiet", "HEAD", "--"], check=True)
    work = Path(__file__).parent
    protocol = json.loads((work / "development-protocol-v9.json").read_text())
    args.output.mkdir(parents=True, exist_ok=False)
    signal.signal(signal.SIGALRM, alarm)
    torch.set_num_threads(1)
    torch.set_flush_denormal(False)
    startup = now()
    frozen = load()
    term = frozen["termination"]
    # Reuse the previously corrected timer cancellation boundary, immutable source.
    service = importlib.import_module(term.__package__.rsplit(".", 1)[0] + ".consumer_v2.service")
    adapter = CompositionalByteLevelAdapter.from_token_pieces(
        json.loads((args.input / "vocabulary.json").read_text())
    )
    table = term.surrogate_table(adapter.emissions, 50256, 50256)
    torch.empty(1, device="cuda")
    torch.cuda.synchronize()
    paths = sorted(p for p in args.input.glob("*.json") if p.with_suffix(".npy").exists())
    if len(paths) != 15:
        raise ValueError("ALL15 original cases required")
    metadata = dict(
        commit=subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
        protocol_sha256=digest(work / "development-protocol-v9.json"),
        input_metadata_sha256=digest(args.input / "metadata.json"),
        vocabulary_sha256=digest(args.input / "vocabulary.json"),
        compiler_producer=frozen["producer"],
        compiler_archive_sha256=frozen["archive_sha256"],
        torch=torch.__version__,
        cuda=torch.version.cuda,
        gpu=torch.cuda.get_device_name(),
        common_startup=elapsed(startup),
        sources={p.name: digest(p) for p in work.glob("*.py")},
        new_model_forwards=0,
        positive_claim_permitted=False,
    )
    (args.output / "metadata.json").write_text(
        json.dumps(metadata, indent=2, sort_keys=True) + "\n"
    )
    limits = {k: protocol["resources"][k] for k in ("max_cells", "max_edges", "max_terms")}
    limits["timeout_seconds"] = protocol["resources"]["seconds_per_operation"]
    rows = []
    setups = []
    for case_index, path in enumerate(paths):
        case = json.loads(path.read_text())
        head = np.load(path.with_suffix(".npy"), allow_pickle=False)
        if digest(path.with_suffix(".npy")) != case["probabilities_sha256"]:
            raise ValueError("old real head changed")
        canvas = (*case["canvas"], 50256)
        free = [p for p, t in enumerate(canvas) if t is None]
        dense = np.zeros((len(canvas), table.adapter.vocabulary_size), dtype=np.float64)
        dense[free] = head
        for p, t in enumerate(canvas):
            if t is not None:
                dense[p, t] = 1
        weights = torch.from_numpy(dense).cuda()
        torch.cuda.synchronize()
        start = now()
        graph = term.terminated_graph(table, canvas, None, 50256, 50256, symbolic=True, **limits)
        prepared = term.prepare_graph(graph, table, canvas, **limits)
        layers = tuple(
            tuple(
                tuple(
                    (
                        dst,
                        tuple(sorted({c for g in gids for c in prepared.table.local_to_class[g]})),
                    )
                    for dst, gids in outgoing
                )
                for outgoing in layer
            )
            for layer in prepared.arcs
        )
        compilation = elapsed(start)
        # Independent exact oracle excluded from EVERY method timer.
        gold = ExactDAG(table.classes, layers, prepared.accepting, dense)
        exact_mass = gold.beta[0][0]
        setup = dict(case=path.stem, common_constraint_compilation=compilation, jit={})
        for method in METHODS:
            start = now()
            jit = API(
                method,
                table.classes,
                layers,
                prepared.accepting,
                canvas,
                protocol["seed"] + case_index + 9000,
                protocol,
            )
            result = jit.query(weights)
            torch.cuda.synchronize()
            validate(result, canvas, dense, adapter, exact_mass)
            setup["jit"][method] = elapsed(start)
            del jit, result
        setups.append(setup)
        (args.output / "setup.json").write_text(json.dumps(setups, indent=2, sort_keys=True) + "\n")
        for rep in range(protocol["repetitions"]):
            order = METHODS[rep % 2 :] + METHODS[: rep % 2]
            for method in order:
                gc.collect()
                torch.cuda.empty_cache()
                cache = {}
                record = dict(
                    case=path.stem,
                    rep=rep,
                    method=method,
                    old_model_softmax=case["forward_and_softmax"],
                    common_compilation=compilation,
                )
                for stage in ("cold", "warm"):

                    def call(
                        stage=stage,
                        method=method,
                        cache=cache,
                        layers=layers,
                        accepting=prepared.accepting,
                        canvas=canvas,
                        weights=weights,
                        seed=protocol["seed"] + case_index * 100 + rep,
                    ):
                        torch.cuda.synchronize()
                        torch.cuda.reset_peak_memory_stats()
                        start = now()
                        if stage == "cold":
                            cache["api"] = API(
                                method,
                                table.classes,
                                layers,
                                accepting,
                                canvas,
                                seed,
                                protocol,
                            )
                        if "api" not in cache:
                            raise RuntimeError("no compiled method after failed first query")
                        result = cache["api"].query(weights)
                        torch.cuda.synchronize()
                        timing = elapsed(start)
                        if torch.cuda.max_memory_allocated() > protocol["resources"]["gpu_bytes"]:
                            raise MemoryError("declared GPU memory guard")
                        return dict(
                            status="complete",
                            result=result,
                            timing=timing,
                            gpu_peak_bytes=torch.cuda.max_memory_allocated(),
                        )

                    measured = service.run_timed(
                        call, protocol["resources"]["seconds_per_operation"]
                    )
                    result = measured.pop("result", None)
                    if measured["status"] == "complete":
                        try:
                            measured.update(validate(result, canvas, dense, adapter, exact_mass))
                        except Exception as error:
                            measured.update(status="error", correctness=False, reason=repr(error))
                        measured["projected"] = {
                            clock: measured["timing"][clock] + case["forward_and_softmax"][clock]
                            for clock in ("wall", "cpu")
                        }
                        if stage == "cold":
                            measured["decomposed_first_query"] = {
                                clock: measured["projected"][clock] + compilation[clock]
                                for clock in ("wall", "cpu")
                            }
                    record[stage] = measured
                    del result
                record["peak_rss_bytes"] = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * 1024
                if record["peak_rss_bytes"] > protocol["resources"]["cpu_rss_bytes"]:
                    raise MemoryError("campaign CPU RSS guard")
                with (args.output / "rows.jsonl").open("a") as stream:
                    stream.write(json.dumps(record, sort_keys=True, default=encode) + "\n")
                rows.append(record)
                print(
                    json.dumps(
                        dict(
                            case=path.stem,
                            rep=rep,
                            method=method,
                            cold=record["cold"]["status"],
                            warm=record["warm"]["status"],
                            wall=record["warm"].get("timing", {}).get("wall"),
                        )
                    ),
                    flush=True,
                )
                del call, cache
        del gold, weights, dense, head, graph, prepared, layers
        gc.collect()
        torch.cuda.empty_cache()
    decision = audit(rows, [p.stem for p in paths], protocol)
    (args.output / "decision.json").write_text(
        json.dumps(decision, indent=2, sort_keys=True) + "\n"
    )
    print(json.dumps(decision), flush=True)


if __name__ == "__main__":
    main()
