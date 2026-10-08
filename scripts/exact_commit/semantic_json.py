"""Research reference: exact Boolean JsonLogic conditioning on example records.

Not a production decoder. Uses the retained original-token CFG forest; adds
execution profiles with classical covering products (Björklund et al., §2.5).
Single ASCII-letter Boolean fields, binary and/or, unary !, no whitespace/EOS.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from fractions import Fraction
from random import Random

from mwpc_exact.cfg_posterior import CfgSampler, _binarize_source, _categorical
from mwpc_exact.mass_certificate import ProbabilityInput
from mwpc_exact.reference.byte_grammars import _SourceGrammarBuilder
from mwpc_exact.reference.limits import CompilationLimit, WorkBudget
from mwpc_exact.reference.normalization import NonterminalRef, SourceGrammar, normalize_to_cnf


def boolean_rule_grammar(fields: Sequence[str]) -> SourceGrammar:
    """Recursive rule syntax independent of records, labels and probabilities."""
    if (
        not fields
        or len(set(fields)) != len(fields)
        or any(
            not isinstance(f, str) or len(f) != 1 or not f.isascii() or not f.isalpha()
            for f in fields
        )
    ):
        raise ValueError("fields must be distinct single ASCII letters")
    fields = tuple(sorted(fields))
    b = _SourceGrammarBuilder(
        ("E", "Body", "And", "Or", "AndTail", "OrTail", "Close", "Not", "Var", "Field"),
        start="E",
    )
    b.rule("E", b'{"', "Body")
    b.rule("Body", b'and":[', "And")
    b.rule("Body", b'or":[', "Or")
    b.rule("Body", b'!":[', "Not")
    b.rule("Body", b'var":"', "Var")
    b.rule("And", "E", "AndTail")
    b.rule("Or", "E", "OrTail")
    b.rule("AndTail", b",", "Close")
    b.rule("OrTail", b",", "Close")
    b.rule("Close", "E", b"]}")
    b.rule("Not", "E", b"]}")
    b.rule("Var", "Field", b'"}')
    for field in fields:
        b.rule("Field", field.encode("ascii"))
    return b.build()


def _zeta(values: Sequence[int], budget: WorkBudget, *, inverse: bool = False) -> list[int]:
    result = list(values)
    bit = 1
    while bit < len(result):
        budget.consume(len(result))
        for mask in range(len(result)):
            if mask & bit:
                if inverse:
                    result[mask] -= result[mask ^ bit]
                else:
                    result[mask] += result[mask ^ bit]
        bit <<= 1
    return result


def covering_product(left: Sequence[int], right: Sequence[int], budget: WorkBudget) -> list[int]:
    """All union masses: at most 2**m products; sparse pairs or classical zeta."""
    if len(left) != len(right) or not left or len(left) & (len(left) - 1):
        raise ValueError("profiles must have the same positive power-of-two length")
    budget.consume(2 * len(left))
    if any(type(x) is not int or x < 0 for row in (left, right) for x in row):
        raise ValueError("profile weights must be non-negative integers")
    a_support = [(i, x) for i, x in enumerate(left) if x]
    b_support = [(j, y) for j, y in enumerate(right) if y]
    if len(a_support) * len(b_support) <= len(left):
        budget.consume(len(left) + len(a_support) * len(b_support))
        result = [0] * len(left)
        for i, x in a_support:
            for j, y in b_support:
                result[i | j] += x * y
        return result
    a, b = _zeta(left, budget), _zeta(right, budget)
    budget.consume(len(a))
    result = _zeta([x * y for x, y in zip(a, b, strict=True)], budget, inverse=True)
    if any(x < 0 for x in result):
        raise ValueError("non-negative profile weights required")
    return result


def _union_pair(a, b, target, rng, budget):
    """Conditional pair: sparse enumeration or superset zeta; at most O(m*2**m)."""
    full = len(a) - 1
    budget.consume(3 * len(a))
    sa = [(i, x) for i, x in enumerate(a) if x]
    sb = [(j, y) for j, y in enumerate(b) if y]
    if len(sa) * len(sb) <= len(a):
        budget.consume(len(sa) * len(sb))
        first_weights = [0] * len(a)
        for i, x in sa:
            for j, y in sb:
                if i | j == target:
                    first_weights[i] += x * y
        weights = tuple(first_weights)
    else:
        restricted = [b[t] if t | target == target else 0 for t in range(len(b))]
        sup = list(reversed(_zeta(list(reversed(restricted)), budget)))
        weights = tuple(
            a[t] * sup[target ^ t] if t | target == target else 0 for t in range(len(a))
        )
    first = _categorical(weights, rng)
    second = _categorical(tuple(b[t] if first | t == target else 0 for t in range(full + 1)), rng)
    return first, second


@dataclass(frozen=True)
class SemanticPosterior:
    """Mass of each execution profile; conditional samples retain original IDs."""

    inputs: ProbabilityInput
    profile_masses: tuple[Fraction, ...]
    syntax_mass: Fraction
    _plan: CfgSampler
    _inside: Sequence[tuple[int, ...]]
    _weights: tuple[tuple[int, ...], ...]
    _boolean: frozenset[int]
    _operators: Mapping[int, str]
    _constants: Mapping[int, int]
    _max_work: int

    def _term(self, node, term, budget):
        size = len(self.profile_masses)
        head = self._plan.cell_heads[node]
        if not term.children:
            budget.consume(size if head in self._boolean else 1)
            weight = self._weights[term.choice[0]][term.choice[1]] if term.choice else 1
            if head not in self._boolean:
                return [weight]
            result = [0] * size
            result[self._constants[term.production_id]] = weight
            return result
        left, right = term.children
        a, b = self._inside[left], self._inside[right]
        return _combine(head, a, b, self._boolean, self._operators, budget)

    def sample(self, target: int, rng: Random) -> tuple[int, ...]:
        if type(target) is not int or not 0 <= target < len(self.profile_masses):
            raise ValueError("target must be a represented Boolean profile")
        if not isinstance(rng, Random):
            raise TypeError("rng must be an explicitly supplied Random instance")
        if not self.profile_masses[target] or self._plan.root is None:
            raise ValueError("ZERO_MASS_ON_SUPPORT: no rule matching those examples")
        budget = WorkBudget(max_work=self._max_work)
        pending, output = [(self._plan.root, target)], []
        while pending:
            node, desired = pending.pop()
            budget.consume()
            terms = self._plan.terms[node]
            values = tuple(self._term(node, t, budget)[desired] for t in terms)
            term = terms[_categorical(values, rng)]
            if term.choice is not None:
                position, index = term.choice
                if position != len(output):
                    raise RuntimeError("sample changed physical token order")
                output.append(self._plan.state.support.rows[position][index])
            if not term.children:
                continue
            left, right = term.children
            boolean = tuple(self._plan.cell_heads[c] in self._boolean for c in term.children)
            op = self._operators.get(self._plan.cell_heads[node], "pass")
            if op in ("and", "or"):
                a, b = self._inside[left], self._inside[right]
                if op == "and":
                    x, y = _union_pair(a[::-1], b[::-1], desired ^ (len(a) - 1), rng, budget)
                    x, y = x ^ (len(a) - 1), y ^ (len(a) - 1)
                else:
                    x, y = _union_pair(a, b, desired, rng, budget)
            else:
                child_target = desired ^ (len(self.profile_masses) - 1) if op == "not" else desired
                x, y = child_target if boolean[0] else 0, child_target if boolean[1] else 0
            pending.extend(((right, y), (left, x)))
        if len(output) != len(self.inputs.state.canvas):
            raise RuntimeError("sample changed the finite slot count")
        return tuple(output)


def _combine(head, a, b, boolean, operators, budget):
    op = operators.get(head, "pass")
    budget.consume(len(a) + len(b))
    if op in ("and", "or"):
        if op == "and":
            return covering_product(a[::-1], b[::-1], budget)[::-1]
        return covering_product(a, b, budget)
    if head not in boolean:
        return [a[0] * b[0]]
    vector, scalar = (a, b[0]) if len(b) == 1 else (b, a[0])
    if op == "not":
        vector = vector[::-1]
    return [x * scalar for x in vector]


def evaluate_semantics(
    plan: CfgSampler,
    inputs: ProbabilityInput,
    records: Sequence[Mapping[str, bool]],
    *,
    max_profile_entries: int = 1_000_000,
    max_work: int = 10_000_000,
) -> SemanticPosterior:
    """Exact syntax/execution conditioning; finite work refusal is unresolved.

    Records may change without recompiling the syntax forest. Their fields must
    match this restricted grammar; all fields of every record must be Boolean.
    This is a local frozen-product distribution, not model trajectory inference.
    """
    if not records or len(records) > 12:
        raise ValueError("provide between 1 and 12 Boolean example records")
    if type(max_profile_entries) is not int or max_profile_entries < 0:
        raise ValueError("profile entry cap must be a non-negative integer")
    fields = tuple(sorted(records[0]))
    if any(set(r) != set(fields) or any(type(v) is not bool for v in r.values()) for r in records):
        raise ValueError("records must share exactly the same Boolean fields")
    budget = WorkBudget(max_work=max_work)
    source = boolean_rule_grammar(fields)
    binary = _binarize_source(source, budget)
    expected = normalize_to_cnf(binary, budget=budget).grammar
    if plan.grammar != expected or len(plan.cell_heads) != len(plan.terms):
        raise ValueError("plan does not represent this Boolean rule grammar")
    boolean = {n.symbol_id for n in source.nonterminals}
    for rule in reversed(binary.productions):
        if any(isinstance(s, NonterminalRef) and s.symbol_id in boolean for s in rule.body):
            boolean.add(rule.head_id)
    names = {n.name: n.symbol_id for n in source.nonterminals}
    operators = {names["And"]: "and", names["Or"]: "or", names["Not"]: "not"}
    size = 1 << len(records)
    entries = sum(size if head in boolean else 1 for head in plan.cell_heads)
    if entries > max_profile_entries:
        raise CompilationLimit("semantic profile memory cap; feasibility remains unresolved")
    budget.consume(entries)
    labels = {t.symbol_id: t.label for t in plan.grammar.terminals}
    constants = {
        r.production_id: sum(
            1 << i for i, row in enumerate(records) if row[chr(labels[r.terminal_id])]
        )
        for r in plan.grammar.terminal_productions
        if r.head_id == names["Field"]
    }
    syntax = plan.evaluate(inputs)  # also enforces fixed positions/reweighting compatibility
    inside: list[tuple[int, ...]] = [()] * len(plan.terms)
    posterior = SemanticPosterior(
        inputs,
        (Fraction(),) * size,
        syntax.valid_mass,
        plan,
        inside,
        syntax._weights,
        frozenset(boolean),
        operators,
        constants,
        max_work,
    )
    for node in plan.order:
        values = [0] * (size if plan.cell_heads[node] in boolean else 1)
        for term in plan.terms[node]:
            contribution = posterior._term(node, term, budget)
            budget.consume(len(values))
            for j, value in enumerate(contribution):
                values[j] += value
        budget.consume(len(values))
        if sum(values) != syntax._inside[node]:
            raise RuntimeError("execution profiles did not partition a syntax cell")
        inside[node] = tuple(values)
    root_values = inside[plan.root] if plan.root is not None else (0,) * size
    denominator = sum(root_values)
    masses = tuple(
        syntax.valid_mass * Fraction(v, denominator) if denominator else Fraction()
        for v in root_values
    )
    if sum(masses) != syntax.valid_mass:
        raise RuntimeError("execution profiles did not partition the syntax mass")
    return SemanticPosterior(
        inputs,
        masses,
        syntax.valid_mass,
        plan,
        tuple(inside),
        syntax._weights,
        frozenset(boolean),
        operators,
        constants,
        max_work,
    )
