"""Opt-in MDLM capture or offline semantic posterior replay; no model downloads."""

from __future__ import annotations

import argparse
import gzip
import hashlib
import itertools
import json
import platform
import subprocess
from fractions import Fraction
from pathlib import Path
from random import Random

from scripts.exact_commit.semantic_json import boolean_rule_grammar, evaluate_semantics

from mwpc_exact.cfg_posterior import compile_cfg_sampler
from mwpc_exact.conflict_proof import read_state, state_data
from mwpc_exact.eos_policy import EOSMode, EOSPolicy
from mwpc_exact.mass_certificate import ProbabilityInput
from mwpc_exact.reference.normalization import normalize_to_cnf
from mwpc_exact.state import SelectionInput
from mwpc_exact.support import SupportPolicy, build_per_position_support
from mwpc_exact.tokenizer_bytes import CompositionalByteLevelAdapter
from mwpc_exact.types import SupportKind

ROOT = Path(__file__).resolve().parents[2]
CONFIG = ROOT / "configs/experiments/m36_semantic_reference_v1.json"


def execute(rule, record):
    op, value = next(iter(rule.items()))
    if op == "var":
        return record[value]
    values = [execute(child, record) for child in value]
    return not values[0] if op == "!" else all(values) if op == "and" else any(values)


def capture(config, output):
    import numpy as np
    import torch
    from scripts.exact_commit.mdlm_cpu import load_cpu_model
    from transformers import AutoTokenizer

    if subprocess.check_output(["git", "status", "--porcelain"], cwd=ROOT).strip():
        raise ValueError("commit producing code/config before capture")
    model_config = json.loads((ROOT / config["model_config"]).read_text())
    cache = ROOT / ".cache/mdlm"
    tokenizer = AutoTokenizer.from_pretrained(
        model_config["tokenizer_id"],
        revision=model_config["tokenizer_revision"],
        cache_dir=str(cache),
        local_files_only=True,
    )
    domains = iter(config["domains"])
    canvas, rows = [], []
    for segment in config["segments"]:
        if segment is not None:
            tokens = tokenizer.encode(segment, add_special_tokens=False)
            canvas.extend(tokens)
            rows.extend((token,) for token in tokens)
        else:
            candidates = [
                tokenizer.encode(word, add_special_tokens=False) for word in next(domains)
            ]
            if any(len(ids) != 1 for ids in candidates):
                raise ValueError("the frozen template requires single-token lexical choices")
            canvas.append(None)
            rows.append(tuple(sorted(ids[0] for ids in candidates)))
    support = build_per_position_support(
        canvas=tuple(canvas),
        policy=SupportPolicy(
            kind=SupportKind.EXPLICIT,
            vocabulary_size=len(tokenizer) + 1,
            pruning_description=config["support_policy"],
        ),
        explicit_support=dict(enumerate(rows)),
    )
    represented = set(itertools.chain.from_iterable(rows))
    pieces = (
        *(
            tokenizer.convert_ids_to_tokens(t) if t in represented else None
            for t in range(len(tokenizer))
        ),
        None,
    )
    adapter = CompositionalByteLevelAdapter.from_token_pieces(pieces)
    torch.set_num_threads(model_config["torch_cpu_threads"])
    torch.manual_seed(config["seed"])
    model, hashes, adapted_hash = load_cpu_model(model_config, cache)
    tokens = [t if t is not None else model_config["mask_token_id"] for t in canvas]
    free = [i for i, t in enumerate(canvas) if t is None]
    with torch.inference_mode():
        logits = model(input_ids=torch.tensor([tokens]), timesteps=torch.zeros(1))[0, free]
        normalized = logits.to(torch.float64).clone()
        normalized[:, model_config["mask_token_id"]] = float("-inf")
        probabilities = normalized.softmax(-1)
    local = ROOT / ".cache/semantic-reference-v1.npz"
    np.savez_compressed(local, logits=logits.numpy(), probabilities=probabilities.numpy())
    distributions, normalization = [], []
    offset = 0
    for i, row in enumerate(rows):
        if canvas[i] is not None:
            distributions.append((Fraction(1),))
        else:
            full = tuple(Fraction(float(p)) for p in probabilities[offset])
            total = sum(full, Fraction())
            distributions.append(tuple(full[t] / total for t in row))
            normalization.append([total.numerator, total.denominator])
            offset += 1
    state = SelectionInput(
        normalize_to_cnf(boolean_rule_grammar(config["fields"])).grammar,
        tuple(canvas),
        (),
        support,
        adapter,
        EOSPolicy(EOSMode.ABSENT),
    )
    raw = {
        "input": state_data(state),
        "probabilities": [[[p.numerator, p.denominator] for p in row] for row in distributions],
        "normalization": normalization,
        "source_npz_sha256": hashlib.sha256(local.read_bytes()).hexdigest(),
        "metadata": {
            "git_commit": subprocess.check_output(
                ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
            ).strip(),
            "config_sha256": hashlib.sha256(CONFIG.read_bytes()).hexdigest(),
            "seed": config["seed"],
            "model_id": model_config["model_id"],
            "model_revision": model_config["model_revision"],
            "tokenizer_revision": model_config["tokenizer_revision"],
            "checkpoint_sha256": hashes,
            "adapted_model_sha256": adapted_hash,
            "grammar_sha256": hashlib.sha256(
                json.dumps(state.grammar.to_dict(), sort_keys=True).encode()
            ).hexdigest(),
            "numeric_reference": model_config["numeric_reference"],
            "support_policy": config["support_policy"],
            "exactness_scope": support.exactness_scope.to_dict(),
            "eos": "ABSENT",
            "hardware": next(
                line.split(":", 1)[1].strip()
                for line in Path("/proc/cpuinfo").read_text().splitlines()
                if line.startswith("model name")
            ),
            "platform": platform.platform(),
            "python": platform.python_version(),
            "torch": torch.__version__,
            "torch_cpu_threads": torch.get_num_threads(),
            "claim_scope": config["claim_scope"],
        },
    }
    output.mkdir(parents=True, exist_ok=False)
    (output / "config.json").write_bytes(CONFIG.read_bytes())
    with gzip.open(output / "input.json.gz", "wt") as stream:
        json.dump(raw, stream, sort_keys=True)


def replay(config, directory, consumer):
    if (directory / "SHA256SUMS").exists():
        for line in (directory / "SHA256SUMS").read_text().splitlines():
            digest, name = line.split()
            if hashlib.sha256((directory / name).read_bytes()).hexdigest() != digest:
                raise ValueError(f"archived input/result changed: {name}")
    with gzip.open(directory / "input.json.gz", "rt") as stream:
        raw = json.load(stream)
    if (directory / "config.json").read_bytes() != CONFIG.read_bytes() or (
        raw["metadata"]["config_sha256"] != hashlib.sha256(CONFIG.read_bytes()).hexdigest()
    ):
        raise ValueError("capture configuration changed")
    data = ProbabilityInput(
        read_state(raw["input"]),
        tuple(tuple(Fraction(*p) for p in row) for row in raw["probabilities"]),
    )
    plan = compile_cfg_sampler(
        boolean_rule_grammar(config["fields"]),
        data.state,
        timeout_seconds=config["compilation_timeout_seconds"],
    )
    posterior = evaluate_semantics(
        plan,
        data,
        config["records"],
        max_profile_entries=config["max_profile_entries"],
        max_work=config["max_work"],
    )
    expected = [Fraction()] * len(posterior.profile_masses)
    rules, profiles = [], []
    for path in itertools.product(*data.state.support.rows):
        rule = json.loads(data.state.tokenizer_adapter.detokenize_bytes(path))
        profile = sum(1 << i for i, row in enumerate(config["records"]) if execute(rule, row))
        weight = Fraction(1)
        for t, row, p in zip(path, data.state.support.rows, data.probabilities, strict=True):
            weight *= p[row.index(t)]
        expected[profile] += weight
        rules.append(rule)
        profiles.append(profile)
    if tuple(expected) != posterior.profile_masses:
        raise ValueError("independent program enumeration disagrees")
    if consumer is not None:
        if hashlib.sha256(consumer.read_bytes()).hexdigest() != config["consumer_sha256"]:
            raise ValueError("consumer changed")
        script = (
            "const f=require(process.argv[1]);let s='';process.stdin.on('data',d=>s+=d);"
            "process.stdin.on('end',()=>{let x=JSON.parse(s);console.log(JSON.stringify("
            "x.rules.map(r=>x.records.reduce((p,d,i)=>p+(f.apply(r,d)?2**i:0),0))))});"
        )
        result = subprocess.run(
            ["node", "-e", script, str(consumer.resolve())],
            check=True,
            input=json.dumps({"rules": rules, "records": config["records"]}),
            text=True,
            capture_output=True,
            timeout=30,
        )
        if json.loads(result.stdout) != profiles:
            raise ValueError("official JsonLogic consumer disagrees")
    results = []
    for target in config["targets"]:
        t, samples = target["profile"], []
        if posterior.profile_masses[t]:
            rng = Random(config["seed"])
            for _ in range(config["samples_per_positive_target"]):
                sample = posterior.sample(t, rng)
                rule = json.loads(data.state.tokenizer_adapter.detokenize_bytes(sample))
                if (
                    sum(1 << i for i, row in enumerate(config["records"]) if execute(rule, row))
                    != t
                ):
                    raise ValueError("sample violates requested examples")
                samples.append({"original_token_ids": sample, "rule": rule})
        results.append(
            {
                "id": target["id"],
                "profile": t,
                "status": "exact_on_support" if samples else "zero_valid_probability_on_support",
                "mass": str(posterior.profile_masses[t]),
                "samples": samples,
            }
        )
    result = {
        "verification": "PASS",
        "metadata": raw["metadata"],
        "independent_programs": len(rules),
        "records": len(config["records"]),
        "official_consumer": "PASS" if consumer is not None else "NOT_RUN",
        "syntax_mass": str(posterior.syntax_mass),
        "omitted_mass": str(data.omitted_mass),
        "results": results,
        "claim_scope": config["claim_scope"],
    }
    if (directory / "rows.jsonl").exists():
        recorded = json.loads((directory / "rows.jsonl").read_text())
        for key in ("metadata", "syntax_mass", "omitted_mass", "independent_programs", "records"):
            if result[key] != recorded[key]:
                raise ValueError(f"current recomputation disagrees with archive: {key}")
        for current, old in zip(results, recorded["results"], strict=True):
            if any(current[k] != old[k] for k in ("id", "profile", "status", "mass")):
                raise ValueError("current target mass/status disagrees with archive")
    return result


def check_full_capture(directory, path):
    """Independent NumPy softmax and original-token rational-row audit (opt-in)."""
    import numpy as np

    with gzip.open(directory / "input.json.gz", "rt") as stream:
        raw = json.load(stream)
    if hashlib.sha256(path.read_bytes()).hexdigest() != raw["source_npz_sha256"]:
        raise ValueError("full capture source changed")
    with np.load(path, allow_pickle=False) as arrays:
        logits, p = arrays["logits"].astype(np.float64), arrays["probabilities"]
    logits[:, 50257] = -np.inf
    logits -= logits.max(axis=1, keepdims=True)
    expected = np.exp(logits)
    expected /= expected.sum(axis=1, keepdims=True)
    if not np.allclose(p, expected, rtol=2e-14, atol=0):
        raise ValueError("full non-mask softmax mismatch")
    selection = raw["input"]["selection"]
    free = [i for i, token in enumerate(selection["canvas"]) if token is None]
    if p.shape != (len(free), 50258):
        raise ValueError("full vocabulary/slot shape mismatch")
    for offset, i in enumerate(free):
        full = tuple(Fraction(float(x)) for x in p[offset])
        total = sum(full, Fraction())
        if total != Fraction(*raw["normalization"][offset]) or (
            tuple(full[t] / total for t in selection["support"]["rows"][i])
            != tuple(Fraction(*q) for q in raw["probabilities"][i])
        ):
            raise ValueError("selected original-token probabilities changed")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--capture", action="store_true")
    parser.add_argument("--directory", required=True, type=Path)
    parser.add_argument("--consumer", type=Path)
    parser.add_argument("--full-capture", type=Path)
    parser.add_argument("--summary", action="store_true", help="derived Markdown; no timings")
    args = parser.parse_args()
    config = json.loads(CONFIG.read_text())
    if args.capture:
        capture(config, args.directory)
    result = replay(config, args.directory, args.consumer)
    if args.full_capture is not None:
        check_full_capture(args.directory, args.full_capture)
    result["full_logits_checked"] = args.full_capture is not None
    result["status_counts"] = {
        status: sum(r["status"] == status for r in result["results"])
        for status in sorted({r["status"] for r in result["results"]})
    }
    if args.capture:
        with (args.directory / "rows.jsonl").open("x") as stream:
            stream.write(json.dumps(result, sort_keys=True) + "\n")
    if args.summary:
        print("# M36: frozen MDLM / JsonLogic execution check\n")
        print(
            f"Capture code: `{result['metadata']['git_commit']}`. "
            f"Seed: `{result['metadata']['seed']}`.\n"
        )
        print(
            "Analysis script SHA-256: "
            f"`{hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}`.\n"
        )
        print(
            f"Independent enumeration: {result['independent_programs']} rules, "
            f"{result['records']} records.\n"
        )
        print(
            "| Target | Status | Samples | Probability given syntax | Expected rejection trials |"
        )
        print("|---|---|---:|---:|---:|")
        syntax = Fraction(result["syntax_mass"])
        for row in result["results"]:
            mass = Fraction(row["mass"])
            probability = f"{float(mass / syntax):.9g}" if syntax else "undefined"
            trials = f"{float(syntax / mass):.9g}" if mass else "never succeeds"
            print(
                f"| {row['id']} | {row['status']} | {len(row['samples'])} | "
                f"{probability} | {trials} |"
            )
        print(
            "\nProbabilities and trial counts are rounded displays computed from archived "
            "exact fractions, not measured performance. Rejection means independent "
            "draws from the same syntax-conditioned product law; it is not native EPIC. "
            "This is an illustrative consumer check, not an external benchmark or "
            "a guarantee on unseen records. The archived capture also records the "
            "optional pinned consumer and full-logit audits; ordinary offline replay "
            "does not rerun those checks.\n"
        )
        print(
            "Generate: `python -m scripts.exact_commit.capture_semantic_reference "
            "--directory docs/artifacts/raw/m36_semantic_reference_v1 --summary`."
        )
    else:
        print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
