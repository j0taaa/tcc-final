"""A79 offline binary circuit. No maintained solver or model code is changed.

Only a checked CfgSampler is accepted as the source of determinism. The verifier
certifies position decomposition and exclusive, globally ordered noise groups;
it is not a general decision procedure for determinism of arbitrary circuits.
Its temporary bitsets require O(N*(G+n)) bits in the worst case (quadratic when
G=Theta(N)); they are discarded and are not resident arithmetic messages.
"""

from __future__ import annotations

import importlib.util
import sys
from dataclasses import dataclass, fields, is_dataclass, replace
from fractions import Fraction
from functools import lru_cache
from pathlib import Path
from random import Random

from mwpc_exact.cfg_posterior import CfgSampler
from mwpc_exact.eos_policy import EOSMode


class CircuitRefusal(ValueError):
    status = "unsupported_structure"


class ResourceRefusal(CircuitRefusal):
    status = "resource_refusal_unresolved"


class ZeroMass(CircuitRefusal):
    status = "zero_mass_on_support"


@dataclass(frozen=True, slots=True)
class Gate:
    op: str
    left: int = -1
    right: int = -1
    choice: tuple[int, int] | None = None
    value: int = 0
    group: int = -1


def deep_bytes(value, seen=None):
    """Deduplicated Python sizes; excludes allocator and function environments."""
    seen = set() if seen is None else seen
    if id(value) in seen:
        return 0
    seen.add(id(value))
    size = sys.getsizeof(value)
    if is_dataclass(value):
        return size + sum(deep_bytes(getattr(value, f.name), seen) for f in fields(value))
    if isinstance(value, dict):
        return size + sum(deep_bytes(k, seen) + deep_bytes(v, seen) for k, v in value.items())
    if isinstance(value, (tuple, list, set, frozenset)):
        return size + sum(deep_bytes(v, seen) for v in value)
    if isinstance(value, Fraction):
        return size + deep_bytes(value.numerator, seen) + deep_bytes(value.denominator, seen)
    if hasattr(value, "__dict__"):
        return size + deep_bytes(vars(value), seen)
    return size


def verify(gates, root, positions, *, max_workspace_bytes=256 * 1024**2):
    """Sufficient structural certificate, with an explicit unresolved safety cap."""
    if root is None:
        if gates:
            raise CircuitRefusal("zero-root circuit must contain no unreachable gates")
        return dict(N=0, S=0, Sa=0, Sm=0, inputs=0, K=0, E=None, verifier_workspace_bytes=0)
    if not 0 <= root < len(gates):
        raise CircuitRefusal("invalid root")
    count = max((g.group for g in gates), default=-1) + 1
    digit_bits, digit_bytes = sys.int_info.bits_per_digit, sys.int_info.sizeof_digit
    estimate = len(gates) * (
        160
        + digit_bytes
        * sum(
            (bits + digit_bits - 1) // digit_bits
            for bits in (count, positions, len(gates).bit_length())
        )
    )
    if estimate > max_workspace_bytes:
        raise ResourceRefusal("verifier bitset workspace cap; structure remains unresolved")
    masks, scopes, paths = [], [], []
    reachable, pending = set(), [root]
    while pending:
        node = pending.pop()
        if node in reachable:
            continue
        if not 0 <= node < len(gates):
            raise CircuitRefusal("invalid child")
        reachable.add(node)
        if gates[node].op in ("add", "mul"):
            pending.extend((gates[node].left, gates[node].right))
    if len(reachable) != len(gates):
        raise CircuitRefusal("unreachable gates")
    for node, gate in enumerate(gates):
        mask = scope = cost = 0
        if gate.op == "input":
            if gate.choice is None or not 0 <= gate.choice[0] < positions or gate.choice[1] < 0:
                raise CircuitRefusal("invalid original choice")
            scope = 1 << gate.choice[0]
        elif gate.op == "const":
            if type(gate.value) is not int or gate.value < 0 or gate.value.bit_length() > 4096:
                raise CircuitRefusal("unsupported exact structural constant")
        elif gate.op in ("add", "mul"):
            a, b = gate.left, gate.right
            if not (0 <= a < node and 0 <= b < node):
                raise CircuitRefusal("gates must be topologically ordered")
            mask = masks[a] | masks[b]
            if gate.op == "mul":
                if scopes[a] & scopes[b] or masks[a] & masks[b]:
                    raise CircuitRefusal("coexisting positions or rounded groups")
                scope, cost = scopes[a] | scopes[b], paths[a] + paths[b]
            else:
                if scopes[a] != scopes[b]:
                    raise CircuitRefusal("sum alternatives must have identical position scopes")
                scope, cost = scopes[a], max(paths[a], paths[b])
        else:
            raise CircuitRefusal("unknown operation")
        if gate.op != "const":
            if not scope or gate.group < 0 or mask.bit_length() > gate.group:
                raise CircuitRefusal("non-global group order, repeated group or empty scope")
            mask |= 1 << gate.group
            cost += 1
        elif gate.group != -1:
            raise CircuitRefusal("structural constants must remain exact")
        masks.append(mask)
        scopes.append(scope)
        paths.append(cost)
    if scopes[root] != (1 << positions) - 1:
        raise CircuitRefusal("root must consume every physical position exactly once")
    return dict(
        N=len(gates),
        S=sum(g.group >= 0 for g in gates),
        inputs=sum(g.op == "input" for g in gates),
        Sa=sum(g.op == "add" for g in gates),
        Sm=sum(g.op == "mul" for g in gates),
        K=paths[root],
        E=None,
        verifier_workspace_bytes=deep_bytes((masks, scopes, paths)),
        verifier_workspace_bound_bytes=estimate,
    )


def _numeric():
    name = "a79_numeric"
    if name not in sys.modules:
        spec = importlib.util.spec_from_file_location(name, Path(__file__).with_name("numeric.py"))
        module = importlib.util.module_from_spec(spec)
        sys.modules[name] = module
        try:
            spec.loader.exec_module(module)
        except BaseException:
            del sys.modules[name]
            raise
    return sys.modules[name]


@dataclass(slots=True)
class Evaluation:
    circuit: Circuit
    values: tuple
    method: str
    arithmetic: object
    stats: dict
    row_scales: tuple[int, ...] = ()

    def measure(self, rows):
        """Diagnostic object sizes outside query timers; these are not RSS."""
        arith, stored, circuit = self.arithmetic, self.values, self.circuit
        width = max((abs(v.exponent).bit_length() + 1 for v in stored), default=1) if arith else 0
        seen = set()
        self.stats.update(
            E=width,
            message_bytes=deep_bytes(stored, seen),
            message_payload_bits=(
                sum(v.bit_length() for v in stored)
                if arith is None
                else len(stored) * (arith.p + width)
            ),
        )
        self.stats.update(
            head_bytes=deep_bytes(rows, seen),
            graph_bytes=deep_bytes((circuit.gates, circuit.token_rows, circuit.canvas), seen),
            group_bytes=deep_bytes(circuit.groups, seen),
            scale_bytes=deep_bytes(self.row_scales, seen),
            arithmetic_state_bytes=deep_bytes(arith, seen),
        )
        return self.stats


@dataclass(frozen=True, slots=True)
class Circuit:
    root: int | None
    gates: tuple[Gate, ...]
    groups: tuple[tuple[int, ...], ...]
    token_rows: tuple[tuple[int, ...], ...]
    canvas: tuple[int | None, ...]
    stats: dict
    kind: str = "checked_ll1_original_ids_absent_eos"

    @property
    def positionmaps(self):
        return {g.choice: i for i, g in enumerate(self.gates) if g.op == "input"}

    def evaluate(self, rows, method="exact", precision=9, seed=0, *, measure=True):
        if method not in ("exact", "nearest", "sr_singleton", "sr_shared"):
            raise ValueError("unknown arithmetic method")
        rows = tuple(tuple(Fraction(x) for x in row) for row in rows)
        if len(rows) != len(self.token_rows):
            raise ValueError("one aligned row per physical position is required")
        for row, ids, fixed in zip(rows, self.token_rows, self.canvas, strict=True):
            if len(row) != len(ids) or min(row, default=0) < 0 or sum(row) > 1:
                raise ValueError("invalid probabilities or original-row alignment")
            if any(x.denominator & (x.denominator - 1) for x in row):
                raise ValueError("offline V1 requires dyadic inputs")
            if fixed is not None and (ids != (fixed,) or row != (Fraction(1),)):
                raise ValueError("pins must remain delta distributions")
        if self.root is None:
            raise ZeroMass("no valid structural derivation")
        arith, scales = None, ()
        if method == "exact":
            scales = tuple(max((x.denominator for x in row), default=1) for row in rows)
            weights = tuple(
                tuple(x.numerator * (s // x.denominator) for x in row)
                for s, row in zip(scales, rows, strict=True)
            )
        else:
            arith = _numeric().BinaryArithmetic(
                precision,
                mode=("nearest" if method == "nearest" else "stochastic"),
                rng=Random(seed),
            )
            weights = rows
        values = [None] * len(self.gates)
        batches = self.groups if method == "sr_shared" else (range(len(self.gates)),)
        for i, g in enumerate(self.gates):
            if g.op == "const":
                odd = g.value // (g.value & -g.value) if g.value else 0
                if arith is not None and odd.bit_length() > precision:
                    raise CircuitRefusal("exact structural constant does not fit the format")
                values[i] = g.value if arith is None else arith.convert(Fraction(g.value))
        for batch in batches:
            if method == "sr_shared":
                arith.start_group()
            for i in batch:
                g = self.gates[i]
                if g.op == "const":
                    continue
                if method == "sr_singleton":
                    arith.start_group()
                if g.op == "input":
                    value = weights[g.choice[0]][g.choice[1]]
                    values[i] = value if arith is None else arith.convert(value)
                else:
                    a, b = values[g.left], values[g.right]
                    values[i] = (
                        (a + b if g.op == "add" else a * b)
                        if arith is None
                        else (arith.add(a, b) if g.op == "add" else arith.mul(a, b))
                    )
        stored = tuple(values)
        if not (stored[self.root] if arith is None else stored[self.root].mantissa):
            raise ZeroMass("zero valid probability on the supplied support")
        evaluation = Evaluation(
            self, stored, method, arith, dict(arithmetic=getattr(arith, "stats", {})), scales
        )
        if measure:
            evaluation.measure(rows)
        return evaluation

    def sample(self, evaluation, rng):
        if evaluation.circuit is not self or not isinstance(rng, Random):
            raise ValueError("matching evaluation and explicit independent Random are required")
        if rng is getattr(evaluation.arithmetic, "rng", None):
            raise ValueError("reconstruction must use a separate random stream")
        output, pending = [None] * len(self.token_rows), [self.root]
        if self.root is None:
            raise ZeroMass("no conditional sample")
        while pending:
            node = pending.pop()
            g = self.gates[node]
            if g.op == "input":
                pos, index = g.choice
                if output[pos] is not None:
                    raise RuntimeError("repeated physical position")
                output[pos] = self.token_rows[pos][index]
            elif g.op == "mul":
                pending.extend((g.right, g.left))
            elif g.op == "add":
                a, b = evaluation.values[g.left], evaluation.values[g.right]
                side = (
                    (0 if rng.randrange(a + b) < a else 1)
                    if evaluation.arithmetic is None
                    else evaluation.arithmetic.choose(a, b, rng)
                )
                pending.append((g.left, g.right)[side])
        if any(t is None for t in output):
            raise RuntimeError("sample omitted a physical position")
        return tuple(output)


def build(plan: CfgSampler) -> Circuit:
    if not isinstance(plan, CfgSampler) or plan.state.eos_policy.mode is not EOSMode.ABSENT:
        raise CircuitRefusal("a checked LL(1) sampler with ABSENT EOS is required")
    cells, pending = set(), [] if plan.root is None else [plan.root]
    while pending:
        node = pending.pop()
        if node not in cells:
            cells.add(node)
            pending.extend(c for t in plan.terms[node] for c in t.children)
    gates, groups, mapped, choices, constants = [], [], {}, {}, {}

    def emit(gate):
        if len(gates) >= 200_000:
            raise ResourceRefusal("200000 circuit gate cap; feasibility remains unresolved")
        gates.append(gate)
        return len(gates) - 1

    def constant(value):
        if value not in constants:
            if value.bit_length() > 4096:
                raise CircuitRefusal("exact structural constant exceeds 4096 bits")
            constants[value] = emit(Gate("const", value=value))
        return constants[value]

    def combine(op, a, b, group):
        ga, gb = gates[a], gates[b]
        if ga.op == gb.op == "const":
            return constant(ga.value + gb.value if op == "add" else ga.value * gb.value)
        if op == "mul" and (ga.op == "const" or gb.op == "const"):
            c, other = (ga, b) if ga.op == "const" else (gb, a)
            if c.value in (0, 1):
                return constant(0) if not c.value else other
        return emit(Gate(op, a, b, group=group))

    needed = sorted({t.choice for c in cells for t in plan.terms[c] if t.choice is not None})
    for pos in range(len(plan.state.canvas)):
        batch = [emit(Gate("input", choice=c, group=len(groups))) for c in needed if c[0] == pos]
        choices.update((gates[i].choice, i) for i in batch)
        if batch:
            groups.append(tuple(batch))
    for cell in plan.order:
        if cell not in cells:
            continue
        terms, before = [], len(gates)
        for term in plan.terms[cell]:
            if term.choice is not None and not term.children:
                terms.append(choices[term.choice])
            elif len(term.children) == 2 and term.choice is None:
                a, b = (mapped[c] for c in term.children)
                terms.append(combine("mul", a, b, len(groups)))
            elif not term.children and term.choice is None:
                terms.append(constant(1))
            else:
                raise CircuitRefusal("unsupported term arity")
        batch = tuple(i for i in range(before, len(gates)) if gates[i].group >= 0)
        if batch:
            groups.append(batch)
        while len(terms) > 1:
            before = len(gates)
            terms = [
                combine("add", terms[j], terms[j + 1], len(groups))
                if j + 1 < len(terms)
                else terms[j]
                for j in range(0, len(terms), 2)
            ]
            batch = tuple(i for i in range(before, len(gates)) if gates[i].group >= 0)
            if batch:
                groups.append(batch)
        mapped[cell] = terms[0] if terms else constant(0)
    root = None if plan.root is None else mapped[plan.root]
    keep, pending = set(), [] if root is None else [root]
    while pending:
        i = pending.pop()
        if i not in keep:
            keep.add(i)
            if gates[i].op in ("add", "mul"):
                pending.extend((gates[i].left, gates[i].right))
    indices = {old: new for new, old in enumerate(sorted(keep))}
    groups = tuple(tuple(indices[i] for i in batch if i in keep) for batch in groups)
    groups = tuple(batch for batch in groups if batch)
    group_ids = {i: g for g, batch in enumerate(groups) for i in batch}
    final = tuple(
        replace(
            gates[i],
            left=indices.get(gates[i].left, -1),
            right=indices.get(gates[i].right, -1),
            group=group_ids.get(indices[i], -1),
        )
        for i in sorted(keep)
    )
    root = indices.get(root)
    stats = verify(final, root, len(plan.state.canvas))
    stats.update(
        cells=len(cells),
        alternatives=sum(len(plan.terms[c]) for c in cells),
        groups=len(groups),
        group_sizes=tuple(map(len, groups)),
    )
    return Circuit(root, final, groups, plan.state.support.rows, plan.state.canvas, stats)


@lru_cache(maxsize=128)
def precision_for(K, epsilon=Fraction(1, 100), control="sr"):
    """Smallest p>=2 certified by exact rational powers of the frozen envelope.

    Preparation is cached, never free: charge the first call outside query timing.
    SR: (1+c)^K <= (1+eps)/(1-eps). Nearest squares that RHS;
    moments compares v*w <= eps^2; moments_improved compares v*w <= 4*eps^2.
    No floating approximation sets the budget.
    """
    epsilon = Fraction(epsilon)
    if type(K) is not int or K < 0 or not 0 < epsilon < 1:
        raise ValueError("nonnegative K and 0<epsilon<1 are required")
    if control not in ("sr", "nearest", "moments", "moments_improved"):
        raise ValueError("unknown precision control")
    target = (1 + epsilon) / (1 - epsilon)
    for p in range(2, 4097):
        u = Fraction(1, 2 ** (p - 1))
        if control == "sr":
            certified = (1 + u * u / (4 * (1 + u))) ** K <= target
        elif control == "nearest":
            certified = (1 + u) ** K <= target**2
        else:
            factor = 4 if control == "moments_improved" else 1
            certified = ((1 + u * u / 4) ** K - 1) * (
                (1 + 3 * (1 + u) ** 4 * u * u / 4) ** K - 1
            ) <= factor * epsilon**2
        if certified:
            return p
    raise ResourceRefusal("precision search cap; numerical budget remains unresolved")
