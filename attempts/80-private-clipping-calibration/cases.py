"""A80's frozen finite sources; integer inside sampling, without outside.

These are conditioned product laws on original IDs, not model trajectories.
The PRNG is supplied by the caller; reproducibility does not certify IID noise
or an executable privacy guarantee. All CDF preparation is paid by ``prepare``.
"""

from __future__ import annotations

import hashlib
from bisect import bisect_right
from collections.abc import Callable, Iterator, Sequence
from dataclasses import dataclass, field
from fractions import Fraction
from math import prod
from random import Random
from time import perf_counter

from mwpc_exact.cfg_posterior import CfgSampler, compile_cfg_sampler
from mwpc_exact.eos_policy import EOSMode, EOSPolicy
from mwpc_exact.reference.byte_grammars import _SourceGrammarBuilder
from mwpc_exact.reference.limits import WorkBudget
from mwpc_exact.reference.normalization import SourceGrammar, normalize_to_cnf
from mwpc_exact.state import SelectionInput
from mwpc_exact.support import SupportPolicy, build_per_position_support
from mwpc_exact.tokenizer_bytes import CompositionalByteLevelAdapter
from mwpc_exact.types import SupportKind

MAX_CHART_CELLS = 200_000
MAX_ALTERNATIVES = 1_000_000
MAX_PREPROCESSING_WORK = 5_000_000
ENUMERATION_LIMIT = 65_536


class ResourceRefusal(ValueError):
    """Enumeration exceeds its public cap; feasibility is not in question."""


class ZeroMassOnSupport(ValueError):
    """A declared source cannot be normalized (distinct from resource refusal)."""


@dataclass(frozen=True)
class Case:
    family: str
    n: int

    def __post_init__(self) -> None:
        if self.family not in ("dyck", "expr"):
            raise ValueError("family must be dyck or expr")
        if type(self.n) is not int or self.n <= 0:
            raise ValueError("n must be a positive integer")


def cases() -> tuple[Case, ...]:
    """The six protocol cases, in their frozen lexicographic order."""
    return tuple(Case(family, n) for family in ("dyck", "expr") for n in (8, 16, 32))


def raw_weight(family: str, n: int, position: int, token_id: int) -> int:
    """Literal ASCII tag and big-endian SHA256 rule from the frozen README."""
    Case(family, n)
    if type(position) is not int or not 0 <= position < n:
        raise ValueError("position must be an integer in the canvas")
    vocabulary_size = 5 if family == "dyck" else 4
    if type(token_id) is not int or not 0 <= token_id < vocabulary_size:
        raise ValueError("token_id must be an original family ID")
    tag = f"A80-v1|{family}|{n}|{position}|{token_id}".encode("ascii")
    z = int.from_bytes(hashlib.sha256(tag).digest(), "big") % ((1 << 38) + 1)
    return (1 << 39) - (1 << 37) + z


def _source(family: str) -> tuple[SourceGrammar, tuple[bytes, ...]]:
    b = _SourceGrammarBuilder(("S",), start="S")
    if family == "dyck":
        b.rule("S", b"(", "S", b")", "S")
        b.rule("S", b"[", "S", b"]", "S")
        b.rule("S")
        emissions = (b"(", b")", b"[", b"]", b"(")
    else:
        b.rule("S", b"a")
        b.rule("S", b"!", "S")
        b.rule("S", b"&", "S", "S")
        emissions = (b"a", b"!", b"&", b"a")
    return b.build(), emissions


def _dyck_bytes(word: bytes) -> bool:
    stack = []
    for byte in word:
        if byte in (40, 91):
            stack.append(byte)
        elif byte in (41, 93) and stack and stack.pop() == {41: 40, 93: 91}[byte]:
            continue
        else:
            return False
    return not stack


def _expr_bytes(word: bytes) -> bool:
    slots = 1
    for byte in word:
        if not slots:
            return False
        if byte == 97:
            slots -= 1
        elif byte == 38:
            slots += 1
        elif byte != 33:
            return False
    return slots == 0


def _compile(
    source: SourceGrammar,
    emissions: tuple[bytes | None, ...],
    rows: tuple[tuple[int, ...], ...],
    canvas: tuple[int | None, ...] | None = None,
) -> CfgSampler:
    """Also used by small fixtures; initial normalization shares the work cap."""
    canvas = (None,) * len(rows) if canvas is None else canvas
    support = build_per_position_support(
        canvas=canvas,
        policy=SupportPolicy(kind=SupportKind.EXPLICIT, vocabulary_size=len(emissions)),
        explicit_support=dict(enumerate(rows)),
    )
    budget = WorkBudget(max_work=MAX_PREPROCESSING_WORK)
    state = SelectionInput(
        normalize_to_cnf(source, budget=budget).grammar,
        canvas,
        (),
        support,
        CompositionalByteLevelAdapter(emissions),
        EOSPolicy(EOSMode.ABSENT),
    )
    return compile_cfg_sampler(
        source,
        state,
        max_chart_cells=MAX_CHART_CELLS,
        max_alternatives=MAX_ALTERNATIVES,
        max_preprocessing_work=MAX_PREPROCESSING_WORK - budget.used,
    )


@dataclass(frozen=True)
class IntegerSampler:
    """A normalized integer source, with CDFs prepared for every forest node.

    ``total`` is the raw inside root, not a row-normalized probability.
    Probability evaluation returns zero off the declared ID/byte language.
    """

    plan: CfgSampler = field(repr=False)
    weights: tuple[tuple[int, ...], ...] = field(repr=False)
    inside: tuple[int, ...] = field(repr=False)
    cdfs: tuple[tuple[int, ...], ...] = field(repr=False)
    total: int
    _recognizes: Callable[[bytes], bool] = field(repr=False)
    _lookup: tuple[dict[int, int], ...] = field(repr=False)

    def validate(self, word: Sequence[int]) -> None:
        """Check original rows, pins, exact byte emissions and independent syntax."""
        state = self.plan.state
        if len(word) != len(state.canvas):
            raise ValueError("word must consume exactly the physical slots")
        for position, token in enumerate(word):
            if type(token) is not int or token not in self._lookup[position]:
                raise ValueError("word contains an ID outside its original support row")
            if state.canvas[position] is not None and token != state.canvas[position]:
                raise ValueError("word changed a public pin")
        data = state.tokenizer_adapter.detokenize_bytes(word)
        if not self._recognizes(data):
            raise ValueError("word bytes are not in the independently recognized grammar")

    def _product(self, word: Sequence[int]) -> int:
        return prod(row[token] for row, token in zip(self._lookup, word, strict=True))

    def probability(self, word: Sequence[int]) -> Fraction:
        try:
            self.validate(word)
        except ValueError:
            return Fraction(0)
        return Fraction(self._product(word), self.total)

    def draw(self, rng: Random) -> tuple[int, ...]:
        if not isinstance(rng, Random):
            raise TypeError("rng must be an explicitly supplied Random instance")
        if not self.total or self.plan.root is None:
            raise ZeroMassOnSupport("zero_valid_probability_on_support")
        pending = [self.plan.root]
        output = []
        while pending:
            node = pending.pop()
            cdf = self.cdfs[node]
            index = 0 if len(cdf) == 1 else bisect_right(cdf, rng.randrange(cdf[-1]))
            term = self.plan.terms[node][index]
            if term.choice is not None:
                position, column = term.choice
                if position != len(output):
                    raise RuntimeError("sample changed physical token order")
                output.append(self.plan.state.support.rows[position][column])
            pending.extend(reversed(term.children))
        if len(output) != len(self.plan.state.canvas):
            raise RuntimeError("sample did not consume the physical slots")
        return tuple(output)


@dataclass(frozen=True)
class Prepared:
    """Prepared source state and its paid preparation costs.

    max_work_bits covers preparation integers, including the evaluated bound
    max_ratio_product * valid_count on observation numerators. With the positive
    integer official weights this also bounds product-evaluation intermediates.
    It is not a measurement of operands actually used by a production run.
    """

    case: Case | None
    private: IntegerSampler
    reference: IntegerSampler
    valid_count: int
    compile_seconds: float
    prepare_seconds: float
    min_ratio_product: int
    max_ratio_product: int
    max_work_bits: int
    exactness_scope: str = "exact_on_support"
    omitted_mass: Fraction = Fraction(0)

    def validate(self, word: Sequence[int]) -> None:
        self.private.validate(word)

    def observations(self, rng: Random) -> Iterator[tuple[int, int]]:
        """Fresh equal mixture draws, then one target product evaluation per word.

        Both evaluators refer to that same word: P=product/Zp and mu=1/Zmu.
        The unit reference needs no row products. Returning unreduced U,V avoids
        an unnecessary gcd. No words, ratios or probability history are retained.
        Generation, validation and evaluation happen when the iterator advances,
        and hence belong in the caller's collection timer.
        """
        while True:
            sampler = self.private if rng.randrange(2) == 0 else self.reference
            word = sampler.draw(rng)
            self.validate(word)
            weight = self.private._product(word)
            yield weight * self.reference.total, self.private.total

    def _enumerate_words(self, node: int) -> Iterator[tuple[int, ...]]:
        for term in self.private.plan.terms[node]:
            if term.choice is not None:
                position, column = term.choice
                yield (self.private.plan.state.support.rows[position][column],)
            elif term.children:
                left, right = term.children
                for prefix in self._enumerate_words(left):
                    for suffix in self._enumerate_words(right):
                        yield prefix + suffix
            else:
                yield ()

    def enumerate_law(
        self, limit: int = ENUMERATION_LIMIT
    ) -> tuple[tuple[tuple[int, ...], Fraction, Fraction], ...]:
        """Expand only the unambiguous root forest, after the exact count check."""
        if type(limit) is not int or limit < 0:
            raise ValueError("enumeration limit must be a non-negative integer")
        cap = min(limit, ENUMERATION_LIMIT)
        if self.valid_count > cap:
            raise ResourceRefusal(f"valid_count={self.valid_count} exceeds enumeration cap={cap}")
        root = self.private.plan.root
        if root is None:
            raise ZeroMassOnSupport("zero_valid_probability_on_support")
        result = []
        for word in self._enumerate_words(root):
            self.validate(word)
            result.append(
                (
                    word,
                    Fraction(self.private._product(word), self.private.total),
                    Fraction(1, self.valid_count),
                )
            )
        if len(result) != self.valid_count:
            raise RuntimeError("forest enumeration disagrees with the exact unit inside count")
        return tuple(result)


def _prepare(
    plan: CfgSampler,
    weights: tuple[tuple[int, ...], ...],
    recognizes: Callable[[bytes], bool],
    *,
    case: Case | None = None,
    compile_seconds: float = 0.0,
    started: float | None = None,
) -> Prepared:
    """Small-fixture entry point too; rows are aligned to plan.state.support.rows."""
    started = perf_counter() if started is None else started
    rows = plan.state.support.rows
    if len(weights) != len(rows) or any(
        len(w) != len(r) for w, r in zip(weights, rows, strict=True)
    ):
        raise ValueError("integer weights must align with the compiled original-ID rows")
    if any(type(w) is not int or w < 0 for row in weights for w in row):
        raise ValueError("raw weights must be non-negative integers")
    unit = tuple(tuple(1 for _ in row) for row in rows)
    samplers = []
    max_bits = 1
    for matrix in (weights, unit):
        inside = [0] * len(plan.terms)
        cdfs: list[tuple[int, ...]] = [()] * len(plan.terms)
        for node in plan.order:
            cumulative = []
            value = 0
            for term in plan.terms[node]:
                value += plan.term_mass(term, matrix, inside)
                cumulative.append(value)
            inside[node] = value
            cdfs[node] = tuple(cumulative)
            max_bits = max(max_bits, value.bit_length())
        total = inside[plan.root] if plan.root is not None else 0
        samplers.append(
            IntegerSampler(
                plan,
                matrix,
                tuple(inside),
                tuple(cdfs),
                total,
                recognizes,
                tuple(dict(zip(row, w, strict=True)) for row, w in zip(rows, matrix, strict=True)),
            )
        )
    private, reference = samplers
    if not reference.total:
        raise ZeroMassOnSupport("empty_public_language_on_support")
    if not private.total:
        raise ZeroMassOnSupport("zero_target_mass_on_nonempty_public_language")

    # Structural absence is None, whereas an attainable zero P weight is 0.
    minimum: list[int | None] = [None] * len(plan.terms)
    maximum = [0] * len(plan.terms)
    for node in plan.order:
        for term in plan.terms[node]:
            if term.choice is not None:
                position, column = term.choice
                low = high = weights[position][column]
            elif term.children:
                left, right = term.children
                if minimum[left] is None or minimum[right] is None:
                    continue
                low = minimum[left] * minimum[right]
                high = maximum[left] * maximum[right]
            else:
                low = high = 1
            minimum[node] = low if minimum[node] is None else min(minimum[node], low)
            maximum[node] = max(maximum[node], high)
            max_bits = max(max_bits, high.bit_length())
    root = plan.root
    if root is None or minimum[root] is None:
        raise RuntimeError("positive unit inside has no structural max/min witness")
    # Also accounts for unused/zero-weight rows and the largest source U,V.
    max_bits = max(
        max_bits,
        *(w.bit_length() for row in weights for w in row),
        (maximum[root] * reference.total).bit_length(),
    )
    return Prepared(
        case,
        private,
        reference,
        reference.total,
        compile_seconds,
        perf_counter() - started,
        minimum[root],
        maximum[root],
        max_bits,
    )


def prepare(case: Case) -> Prepared:
    """Compile/precheck and prepare both exact sources, including all integer CDFs.

    compile_seconds includes construction and all checked normalizations.
    prepare_seconds includes SHA weights, both insides/CDFs, evaluator lookups,
    max/min precheck, and bit-width diagnostics. No outside is computed.
    CompilationLimit propagates unchanged: a resource refusal is inconclusive.
    """
    if not isinstance(case, Case):
        raise TypeError("case must be a Case")
    started = perf_counter()
    source, emissions = _source(case.family)
    rows = (tuple(range(len(emissions))),) * case.n
    plan = _compile(source, emissions, rows)
    compile_seconds = perf_counter() - started
    started = perf_counter()
    weights = tuple(
        tuple(raw_weight(case.family, case.n, position, token) for token in row)
        for position, row in enumerate(plan.state.support.rows)
    )
    recognizes = _dyck_bytes if case.family == "dyck" else _expr_bytes
    return _prepare(
        plan, weights, recognizes, case=case, compile_seconds=compile_seconds, started=started
    )
