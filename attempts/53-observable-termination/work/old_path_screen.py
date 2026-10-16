"""Frozen known-old-path observable-stopping screen, no head or label loading."""

import argparse
import hashlib
import importlib.metadata
import json
import platform
import resource
import signal
import subprocess
from pathlib import Path

from .flat_language import EMPTY
from .llada_tokenizer_v10 import EOS, emissions, verify_files
from .terminal_compiler import NumericSuffix, TerminalCompiler, encode, project

HERE = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def cheap_prefix(fixed, table, grammar):
    chunks, i, state = [], 0, 0
    while i in fixed and fixed[i] != EOS:
        v = fixed[i]
        chunks.append(table[v])
        state = grammar.step(state, v)
        if state < 0:
            raise ValueError("inviable fixed contiguous prefix")
        i += 1
    if state in (19, 20):
        return project(b"".join(chunks), True) + (b"}" if state == 19 else b"")
    return None


def complete(fixed):
    stops = [i for i, v in fixed.items() if v == EOS]
    return bool(stops) and all(i in fixed for i in range(min(stops) + 1))


def run(model_dir, capture, protocol_path, output):
    output.mkdir(parents=True, exist_ok=False)
    report = {
        "status": "RUNNING",
        "new_model_forwards": 0,
        "new_auxiliary_words": 0,
        "new_decoder_paths": 0,
        "labels_loaded": False,
        "updates": 0,
        "known_development_paths": True,
    }
    stream = (output / "states.jsonl").open("x", buffering=1)
    try:
        p = json.loads(protocol_path.read_text())
        assert {
            "python": platform.python_version(),
            "tokenizers": importlib.metadata.version("tokenizers"),
        } == p["runtime"]
        assert all(sha(HERE / name) == h for name, h in p["source_sha256"].items())
        assert sha(capture / "rows.jsonl") == p["input_sha256"]["rows"]
        (output / "protocol.json").write_text(json.dumps(p, indent=2) + "\n")
        (output / "provenance.json").write_text(
            json.dumps(
                {
                    "producer_commit": subprocess.check_output(
                        ["git", "rev-parse", "HEAD"], text=True
                    ).strip()
                },
                indent=2,
            )
            + "\n"
        )

        def timeout(signum, frame):
            raise TimeoutError("600s whole screen cap")

        signal.signal(signal.SIGALRM, timeout)
        signal.alarm(600)
        verify_files(model_dir)
        table = emissions(model_dir)
        grammar = NumericSuffix(table, EOS, EOS)
        compilers = [TerminalCompiler(grammar, erase) for erase in (False, True)]
        rows = [json.loads(s) for s in (capture / "rows.jsonl").read_text().splitlines()]
        assert len(rows) == 16 and {r["case"] for r in rows} == set(range(8))
        methods = ("original", "cheap_prefix", "raw_singleton", "projected_singleton")
        path_reports = []
        logical = {m: 0 for m in methods}
        heads = {m: set() for m in methods}
        for row in rows:
            assert row["status"] == "COMPLETE"
            states = [dict(t["fixed_before"]) for t in row["transitions"]] + [
                dict(row["fixed_terminal"])
            ]
            witness = None
            first = {m: None for m in methods}
            for step, fixed in enumerate(states):
                values = []
                for compiler in compilers:
                    v = compiler.classify(64, fixed)
                    assert v == compiler.generic_graph_control(64, fixed)
                    assert v is not EMPTY
                    if isinstance(v, bytes):
                        assert v == compiler.witness_projection(tuple(row["terminal_ids"]))
                        if witness is not None:
                            assert all(
                                i < len(witness) and witness[i] == token
                                for i, token in fixed.items()
                            )
                            assert v == compiler.witness_projection(witness)
                    values.append(v)
                flags = [
                    complete(fixed),
                    cheap_prefix(fixed, table, grammar) is not None,
                    isinstance(values[0], bytes),
                    isinstance(values[1], bytes),
                ]
                if flags[1]:
                    assert values[1] == cheap_prefix(fixed, table, grammar)
                available = witness is not None
                for m, flag in zip(methods, flags, strict=True):
                    if flag and available and first[m] is None:
                        first[m] = step
                record = {
                    "case": row["case"],
                    "replica": row["replica"],
                    "step": step,
                    "terminal_pre_state": step == len(states) - 1,
                    "fixed": sorted(fixed.items()),
                    "available_previous_witness": witness,
                    "flags": dict(zip(methods, flags, strict=True)),
                    "results": list(map(encode, values)),
                    "status": "PASS",
                }
                stream.write(json.dumps(record) + "\n")
                if step < len(row["transitions"]):
                    witness = tuple(row["transitions"][step]["proposal_prefix"])
            assert all(v is not None for v in first.values())
            for m, stop in first.items():
                logical[m] += stop
                heads[m].update(t["head"] for t in row["transitions"][:stop])
            path_reports.append(
                {
                    "case": row["case"],
                    "replica": row["replica"],
                    "first_stop": first,
                    "original_steps": len(row["transitions"]),
                }
            )
            if resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * 1024 > 1024**3:
                raise MemoryError("1GiB whole-process RSS cap")
        unique = {m: len(h) + 1 for m, h in heads.items()}  # common warmup is retained
        strongest = min(unique[m] for m in methods[:-1])
        strict = [
            q
            for q in range(8)
            if sum(r["first_stop"]["projected_singleton"] for r in path_reports if r["case"] == q)
            < sum(r["first_stop"]["cheap_prefix"] for r in path_reports if r["case"] == q)
        ]
        ratio = unique["projected_singleton"] / strongest
        report.update(
            {
                "status": "NECESSITY_PASS"
                if ratio <= 0.8 and len(strict) >= 2
                else "NECESSITY_NEGATIVE",
                "paths": 16,
                "pre_states": 70,
                "terminal_states": 16,
                "logical_forward_requests": logical,
                "unique_heads_plus_common_warmup": unique,
                "ratio_to_strongest_control": ratio,
                "strict_questions_vs_cheap_prefix": strict,
                "path_results": path_reports,
                "hypothetical_old_trace_removals_only": True,
                "measured_new_speedup": False,
                "peak_CPU_process_RSS_bytes": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
                * 1024,
            }
        )
    except Exception as error:
        report.update({"status": "SCREEN_ERROR_OR_REFUSAL", "exception": repr(error)})
        raise
    finally:
        signal.alarm(0)
        stream.close()
        (output / "summary.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    for name in ("model-dir", "capture", "protocol", "output"):
        p.add_argument("--" + name, type=Path, required=True)
    a = p.parse_args()
    run(a.model_dir, a.capture, a.protocol, a.output)
