"""Single-row native terminal snapshot/readout; no model or vLLM import."""

from __future__ import annotations

import ast
import hashlib
import importlib
import json
import random
import sys
from contextlib import contextmanager
from dataclasses import dataclass
from decimal import Decimal
from fractions import Fraction as F
from pathlib import Path

import numpy as np
import torch
from reference import normalized, rounded_simplex, terminal_mean

PIN = "36945e4b3c64913e23962e0924a8b40a84c58807"


def load_native():
    root = Path(__file__).parent / "native_source_v3"
    manifest = json.loads((root / "manifest.json").read_text())
    assert manifest["commit"] == PIN
    for row in manifest["files"]:
        assert hashlib.sha256((root / row["file"]).read_bytes()).hexdigest() == row["sha256"]
    if "mosaic" in sys.modules:
        assert Path(sys.modules["mosaic"].__file__).resolve().is_relative_to(root.resolve())
    precision = torch.get_float32_matmul_precision()
    sys.path.insert(0, str(root))
    try:
        matcher = importlib.import_module("mosaic.matcher")
    finally:
        sys.path.pop(0)
        torch.set_float32_matmul_precision(precision)
    source = root / "integrations/vllm/mosaic_vllm.py"
    tree = ast.parse(source.read_text())
    names = {"_constrained_step", "_offset_groups", "_propose", "_marginals"}
    functions = [
        node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name in names
    ]
    free = next(
        node.value
        for node in tree.body
        if isinstance(node, ast.Assign)
        and any(isinstance(t, ast.Name) and t.id == "FREE" for t in node.targets)
    )
    assert ast.literal_eval(free) == -1 and {node.name for node in functions} == names
    namespace = {"torch": torch, "FREE": -1}
    exec(compile(ast.Module(body=functions, type_ignores=[]), str(source), "exec"), namespace)
    return {"matcher": matcher, "functions": namespace, "origin": manifest}


def rng_state() -> dict:
    return {
        "python": random.getstate(),
        "numpy": np.random.get_state(),
        "cpu": torch.get_rng_state().clone(),
        "cuda": [s.clone() for s in torch.cuda.get_rng_state_all()],
    }


def restore_rng(state: dict) -> None:
    random.setstate(state["python"])
    np.random.set_state(state["numpy"])
    torch.set_rng_state(state["cpu"])
    torch.cuda.set_rng_state_all(state["cuda"])


def rng_digest(state: dict | None = None) -> str:
    state = rng_state() if state is None else state
    out = hashlib.sha256(repr(state["python"]).encode())
    n = state["numpy"]
    out.update(str(n[0]).encode())
    out.update(n[1].tobytes())
    out.update(repr(n[2:]).encode())
    for tensor in [state["cpu"], *state["cuda"]]:
        out.update(tensor.cpu().numpy().tobytes())
    return out.hexdigest()


@contextmanager
def local_rng(seed: int):
    state = rng_state()
    before = rng_digest(state)
    try:
        random.seed(seed)
        np.random.seed(seed % (2**32))
        torch.manual_seed(seed)
        yield
    finally:
        restore_rng(state)
        assert rng_digest() == before, "caller RNG was not restored"


def tensor_digest(tensor) -> str:
    return hashlib.sha256(tensor.detach().contiguous().cpu().numpy().tobytes()).hexdigest()


def compiled_digest(compiled) -> str:
    h = hashlib.sha256(str(compiled.sampler.initial_node_id).encode())
    for name, value in sorted(compiled.sampler.state_dict().items()):
        h.update(name.encode())
        h.update(tensor_digest(value).encode())
    return h.hexdigest()


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("Duplicate field")
        result[key] = value
    return result


def render(point: tuple, labels: tuple) -> str:
    values = rounded_simplex(point, 8)
    fields = []
    for label, value in zip(labels, values, strict=True):
        units = int(value * 10**8)
        fields.append(json.dumps(label) + f":{units // 10**8}.{units % 10**8:08d}")
    return '{"probabilities":{' + ",".join(fields) + "}}"


@dataclass
class TerminalSnapshot:
    runtime: dict
    compiled: object
    scores: object
    tokens: object
    offset: int
    node: int
    accepted: int
    maximum: int | None
    prefix: tuple
    tokenizer: object
    labels: tuple

    @classmethod
    def capture(cls, runtime, matcher, scores, tokens, offset, prefix, tokenizer, labels):
        assert scores.ndim == 3 and tokens.ndim == 2 and scores.shape[:2] == tokens.shape
        assert tokens.shape[0] == 1 and 0 <= offset < tokens.shape[1]
        return cls(
            runtime,
            matcher.compiled,
            scores.detach().clone(),
            tokens.detach().clone(),
            offset,
            matcher.node,
            matcher.num_accepted,
            matcher.max_new_tokens,
            tuple(prefix),
            tokenizer,
            tuple(labels),
        )

    def new_matcher(self):
        matcher = self.runtime["matcher"].ConstraintMatcher(self.compiled, self.maximum)
        matcher.accept(self.node, self.accepted)
        return matcher

    def draw(self) -> tuple:
        batch = self.runtime["matcher"].BatchConstraintMatcher(across_constraints=False)
        ids = self.runtime["functions"]["_propose"](
            batch, [self.new_matcher()], [self.offset], self.scores, self.tokens, 0.0
        )
        return tuple(ids[0].tolist())

    def observe(self, ids: tuple) -> tuple | None:
        eot = self.tokenizer.convert_tokens_to_ids("<eot>")
        pad = self.tokenizer.convert_tokens_to_ids("<pad>")
        body = self.prefix + tuple(ids[self.offset :])
        if eot not in body:
            return None
        stop = body.index(eot)
        if any(token != pad for token in body[stop + 1 :]):
            return None
        text = "".join(self.tokenizer.decode(token) for token in body[:stop])
        try:
            obj = json.loads(
                text, parse_float=Decimal, parse_int=Decimal, object_pairs_hook=unique_object
            )
            if not isinstance(obj, dict) or set(obj) != {"probabilities"}:
                return None
            probs = obj["probabilities"]
            if not isinstance(probs, dict) or set(probs) != set(self.labels):
                return None
            values = tuple(probs[k] for k in self.labels)
            if any(
                not isinstance(v, Decimal) or not v.is_finite() or not 0 <= v <= 1 for v in values
            ):
                return None
            return tuple(map(F, values))
        except (ValueError, TypeError, KeyError, ArithmeticError):
            return None

    def readout(self, first: tuple, budget: int, seed: int) -> dict:
        if not isinstance(budget, int) or budget < 0:
            raise ValueError("A finite nonnegative helper budget is required")
        first = tuple(first)
        raw = self.observe(first)
        if raw is None:
            return {
                "status": "INELIGIBLE",
                "original_ids": first,
                "helpers_called": 0,
                "completed_helpers": 0,
                "samples": [],
                "mean": None,
                "rendered": None,
            }
        samples = []
        before = rng_digest()
        with local_rng(seed):

            def draw():
                state = rng_digest()
                ids = self.draw()
                value = self.observe(ids)
                samples.append(
                    {
                        "ids": ids,
                        "raw": None if value is None else list(map(str, value)),
                        "rng_before": state,
                        "rng_after": rng_digest(),
                    }
                )
                return value

            mean, completed = terminal_mean(raw, draw, budget)
        assert rng_digest() == before and len(samples) == budget
        return {
            "status": "COMPLETE",
            "original_ids": first,
            "helpers_called": len(samples),
            "completed_helpers": completed,
            "samples": samples,
            "normalized_original": list(map(str, normalized(raw))),
            "mean": list(map(str, mean)),
            "rendered": render(mean, self.labels),
        }
