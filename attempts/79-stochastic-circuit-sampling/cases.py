"""Fixed A79 development inputs; no model observations or favorable case selection."""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from random import Random

from mwpc_exact.eos_policy import EOSMode, EOSPolicy
from mwpc_exact.mass_certificate import ProbabilityInput
from mwpc_exact.reference.byte_grammars import _SourceGrammarBuilder
from mwpc_exact.reference.normalization import SourceGrammar, normalize_to_cnf
from mwpc_exact.state import SelectionInput
from mwpc_exact.support import SupportPolicy, build_per_position_support
from mwpc_exact.tokenizer_bytes import CompositionalByteLevelAdapter
from mwpc_exact.types import SupportKind


@dataclass(frozen=True)
class Case:
    family: str
    length: int
    profile: str

    @property
    def name(self) -> str:
        return f"{self.family}-{self.length}-{self.profile}"


def cases() -> tuple[Case, ...]:
    return tuple(
        Case(family, length, profile)
        for family, lengths in (
            ("binary", (16, 64, 256)),
            ("modes", (16, 64, 256)),
            ("dyck", (8, 16, 24)),
        )
        for length in lengths
        for profile in ("uniform", "skewed", "near_uniform")
    )


def grammar(family: str) -> SourceGrammar:
    if family == "binary":
        builder = _SourceGrammarBuilder(("S",), start="S")
        builder.rule("S", b"0", "S")
        builder.rule("S", b"1", "S")
        builder.rule("S")
    elif family == "modes":
        builder = _SourceGrammarBuilder(("S", "A", "B"), start="S")
        builder.rule("S", b"0", "A")
        builder.rule("S", b"1", "B")
        builder.rule("A", b"0", "A")
        builder.rule("A")
        builder.rule("B", b"1", "B")
        builder.rule("B")
    elif family == "dyck":
        builder = _SourceGrammarBuilder(("S", "N"), start="S")
        builder.rule("S", "N", "S")
        builder.rule("S")
        builder.rule("N", b"(", "S", b")")
        builder.rule("N", b"[", "S", b"]")
    else:
        raise ValueError("unregistered development family")
    return builder.build()


def inputs(
    source: SourceGrammar,
    emissions: tuple[bytes, ...],
    rows: tuple[tuple[int, ...], ...],
    probabilities: tuple[tuple[Fraction, ...], ...],
    canvas: tuple[int | None, ...] | None = None,
) -> ProbabilityInput:
    canvas = (None,) * len(rows) if canvas is None else canvas
    support = build_per_position_support(
        canvas=canvas,
        policy=SupportPolicy(kind=SupportKind.EXPLICIT, vocabulary_size=len(emissions)),
        explicit_support=dict(enumerate(rows)),
    )
    state = SelectionInput(
        normalize_to_cnf(source).grammar,
        canvas,
        (),
        support,
        CompositionalByteLevelAdapter(emissions),
        EOSPolicy(EOSMode.ABSENT),
    )
    return ProbabilityInput(state, probabilities)


def head(case: Case, trial: int) -> tuple[SourceGrammar, ProbabilityInput]:
    """Each row uses an explicit power-of-two denominator, including five aliases."""
    if not 0 <= trial < 16:
        raise ValueError("query index outside the frozen protocol")
    source = grammar(case.family)
    emissions = (b"(", b")", b"[", b"]", b"(") if case.family == "dyck" else (b"0", b"1")
    row = tuple(range(len(emissions)))
    rng = Random(20261020 + trial)
    probabilities = []
    for _ in range(case.length):
        if case.profile == "uniform":
            raw = [1] * len(row)
        elif case.profile == "skewed":
            raw = [rng.randint(1, 31) for _ in row]
        elif case.profile == "near_uniform":
            base = 1 << ((case.length - 1).bit_length() + 4)
            raw = [base + (1 if rng.getrandbits(1) else -1) for _ in row]
        else:
            raise ValueError("unregistered head profile")
        denominator = 1 << (sum(raw) - 1).bit_length()
        probabilities.append(tuple(Fraction(weight, denominator) for weight in raw))
    return source, inputs(source, emissions, (row,) * case.length, tuple(probabilities))


def recognizes(family: str, word: bytes) -> bool:
    """Independent recognizers, without the grammar compiler or chart."""
    if family == "binary":
        return all(byte in b"01" for byte in word)
    if family == "modes":
        return bool(word) and (set(word) == {ord("0")} or set(word) == {ord("1")})
    if family != "dyck":
        raise ValueError("unknown recognizer")
    stack = []
    for byte in word:
        if byte in b"([":
            stack.append(byte)
        elif byte in b")]" and stack and stack[-1] == {41: 40, 93: 91}[byte]:
            stack.pop()
        else:
            return False
    return not stack


def validate(case: Case, data: ProbabilityInput, word: tuple[int, ...]) -> None:
    if len(word) != case.length:
        raise AssertionError("wrong number of original token slots")
    for token, row, fixed in zip(word, data.state.support.rows, data.state.canvas, strict=True):
        if token not in row or (fixed is not None and token != fixed):
            raise AssertionError("support or fixed original ID changed")
    raw = data.state.tokenizer_adapter.detokenize_bytes(word)
    if not recognizes(case.family, raw):
        raise AssertionError("independent byte recognizer rejected the output")
