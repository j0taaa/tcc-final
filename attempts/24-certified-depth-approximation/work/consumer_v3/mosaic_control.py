"""Language adapter for unchanged, pinned Mosaic sampling kernels (opt-in).

No model import, tokenizer replacement, numerical-exactness or speed claim.
The bounded-language argument is in consumer-v3-adapter-proof.md.
"""

import hashlib
import importlib
import subprocess
import sys
import types
from pathlib import Path

import numpy as np

from ..lexer import finish
from ..stack_control import consume

MOSAIC_COMMIT = "36945e4b3c64913e23962e0924a8b40a84c58807"
KERNEL_FILES = (
    "mosaic/__init__.py",
    "mosaic/sampling/__init__.py",
    "mosaic/sampling/automaton.py",
    "mosaic/sampling/layers.py",
    "mosaic/sampling/parallel.py",
    "mosaic/sampling/sequential.py",
)


def load(source):
    """Check every imported source against the pinned Git object, then import.

    Restore the caller's matmul precision after upstream's import side effect.
    Callers select and record a precision policy when running native kernels.
    """
    import torch

    source = Path(source).resolve()
    origin = {}
    for name in KERNEL_FILES:
        pinned = subprocess.run(
            ["git", "-C", str(source), "show", f"{MOSAIC_COMMIT}:{name}"],
            check=True,
            capture_output=True,
        ).stdout
        actual = (source / name).read_bytes()
        if actual != pinned:
            raise ValueError(f"Mosaic source differs from pinned object: {name}")
        origin[name] = hashlib.sha256(actual).hexdigest()
    namespace = "_a24_mosaic_" + MOSAIC_COMMIT[:12]
    if namespace not in sys.modules:
        package = types.ModuleType(namespace)
        package.__path__ = [str(source / "mosaic")]
        sys.modules[namespace] = package
    precision = torch.get_float32_matmul_precision()
    try:
        module = importlib.import_module(namespace + ".sampling")
    finally:
        torch.set_float32_matmul_precision(precision)
    return module, dict(commit=MOSAIC_COMMIT, sha256=origin)


def sparse_graph(prepared, *, symbolic=False):
    """Merge equal sufficient descriptors; retain ORIGINAL group IDs/tokens.

    The graph is valid only under the initial canvas or a further fixation of
    it. A different canvas requires recompilation. Zero-mass languages remain
    zero-mass; this function never adds a positive fallback edge.
    """
    states = dict.fromkeys(s for layer in prepared.layers for s in layer)
    state_ids = {s: i for i, s in enumerate(states)}
    pairs, targets = {}, {}
    for p, layer in enumerate(prepared.arcs):
        for a, outgoing in enumerate(layer):
            u = state_ids[prepared.layers[p][a]]
            for b, gids in outgoing:
                v = state_ids[prepared.layers[p + 1][b]]
                for gid in gids:
                    old = targets.setdefault((u, gid), v)
                    if old != v:
                        raise RuntimeError("descriptor merge is not deterministic")
                    pairs.setdefault((u, v), set()).add(gid)
    edges = []
    for (u, v), gids in sorted(pairs.items()):
        ids = tuple(
            sorted(
                {
                    t
                    for g in gids
                    for t in (
                        prepared.table.local_to_class[g]
                        if symbolic
                        else prepared.table.groups[g][3]
                    )
                }
            )
        )
        edges.append((u, v, ids))
    outgoing = {u for u, _, _ in edges}
    edges.extend((u, u, ()) for u in state_ids.values() if u not in outgoing)
    accepting = []
    for (q, stack), u in state_ids.items():
        tail = finish(q)
        if tail is not None and consume(stack, tail) == ():
            accepting.append(u)
    return dict(
        edges=edges,
        initial_state=state_ids[prepared.layers[0][0]],
        accept_states=accepting,
        num_nodes=len(state_ids),
        vocabulary_size=(
            len(prepared.table.classes) if symbolic else prepared.table.adapter.vocabulary_size
        ),
        alphabet="global_class" if symbolic else "original_id",
        canvas=prepared.canvas,
        depth=prepared.max_depth,
    )


def accepts(graph, tokens):
    """Direct finite-graph recognizer for language checks, no tensor arithmetic."""
    state = graph["initial_state"]
    for token in tokens:
        targets = [v for u, v, ids in graph["edges"] if u == state and token in ids]
        if len(targets) > 1:
            raise RuntimeError("multiple original-token paths")
        if not targets:
            return False
        state = targets[0]
    return state in graph["accept_states"]


def minimize(graph, table):
    """Classical Hopcroft minimization over the existing global lexer classes.

    Every global class lies wholly inside/outside each edge token mask. Giving
    it one alphabet symbol therefore preserves every ORIGINAL word. No token
    probability is merged here. Native emission tensors still have V columns.
    """
    from automata.fa.dfa import DFA

    transitions = {u: {} for u in range(graph["num_nodes"])}
    for u, v, ids in graph["edges"]:
        symbolic = graph.get("alphabet") == "global_class"
        cids = set(ids) if symbolic else {table.class_of[t] for t in ids}
        if not symbolic and sum(len(table.classes[c]) for c in cids) != len(ids):
            raise ValueError("edge splits a global original-token class")
        for cid in cids:
            previous = transitions[u].setdefault(str(cid), v)
            if previous != v:
                raise ValueError("class projection is nondeterministic")
    dfa = DFA(
        states=set(transitions),
        input_symbols={str(cid) for cid in range(len(table.classes))},
        transitions=transitions,
        initial_state=graph["initial_state"],
        final_states=set(graph["accept_states"]),
        allow_partial=True,
    ).minify()
    states = {s: i for i, s in enumerate(sorted(dfa.states))}
    edges = []
    for s in sorted(dfa.states):
        targets = {}
        for cid, target in dfa.transitions[s].items():
            targets.setdefault(states[target], []).extend(table.classes[int(cid)])
        edges.extend((states[s], v, tuple(sorted(ids))) for v, ids in sorted(targets.items()))
        if not targets:
            edges.append((states[s], states[s], ()))
    return dict(
        graph,
        edges=edges,
        initial_state=states[dfa.initial_state],
        accept_states=sorted(states[s] for s in dfa.final_states),
        num_nodes=len(states),
        alphabet="original_id",
        vocabulary_size=table.adapter.vocabulary_size,
        minimizer="automata-lib==9.2.0 Hopcroft, global lexer alphabet",
    )


def materialize(graph, module, *, kind, device="cpu", dtype=None, max_bytes=2**28):
    """Pay for native dense masks and both upstream constructor temporaries.

    This conservative allocation guard is not a measured peak or a benchmark
    resource refusal. Query temporaries need their own admission protocol.
    """
    import torch

    if kind not in ("sequential", "parallel"):
        raise ValueError("unknown native sampler")
    dtype = torch.float32 if dtype is None else dtype
    if dtype not in (torch.float32, torch.float64):
        raise ValueError("native preflight supports fp32/fp64 only")
    n, e, v = graph["num_nodes"], len(graph["edges"]), graph["vocabulary_size"]
    # NumPy mask list/stack, initial fp32 CPU/device buffers, dtype conversion,
    # transposes in sequential, and integer indices/lookup all coexist at times.
    estimate = 40 * (n * e + e * v) + 24 * n * n + 32 * (n + e)
    if estimate > max_bytes:
        raise MemoryError(f"native constructor allocation guard: {estimate}>{max_bytes}")
    edges = []
    for u, w, ids in graph["edges"]:
        mask = np.zeros(v, dtype=np.bool_)
        mask[list(ids)] = True
        edges.append((u, w, mask))
    cls = module.SequentialSampler if kind == "sequential" else module.ParallelSampler
    sampler = cls.from_graph(
        dict(
            edges=edges, initial_state=graph["initial_state"], accept_states=graph["accept_states"]
        ),
        device=device,
    ).to(dtype=dtype)
    return sampler, dict(
        nodes=n,
        edges=e,
        vocabulary_size=v,
        constructor_guard_bytes=estimate,
        buffer_bytes=sum(t.numel() * t.element_size() for t in sampler.buffers()),
    )


def fixed_logits(logits, canvas):
    """Condition fixed slots explicitly, preserving original IDs and all free rows.

    Native Mosaic uses forced slots as unit indicators internally. Setting the
    same rows to point masses also makes their returned *fixed-slot* confidence
    one; otherwise upstream multiplies that confidence by the old LM weight.
    Its decoding loop consumes only free-slot confidences.
    """
    if len(canvas) != logits.shape[-2]:
        raise ValueError("canvas length mismatch")
    result = logits.clone()
    for p, token in enumerate(canvas):
        if token is not None:
            result[..., p, :] = float("-inf")
            result[..., p, token] = 0
    return result
