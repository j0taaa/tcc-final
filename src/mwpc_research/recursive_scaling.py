"""Recursive branching lattices with explicit fixed nesting and token widths."""

from mwpc_exact import (
    BenchmarkGrammar,
    BenchmarkInstance,
    CompositionalByteLevelAdapter,
    EOSMode,
    EOSPolicy,
    Proposal,
    SelectionInput,
    SupportKind,
    SupportPolicy,
    build_per_position_support,
)
from mwpc_research.recursive_tasks import recursive_grammar


def scaling_instance(slots: int, width: int, fixed_depth: int) -> BenchmarkInstance:
    if slots < 2 or slots % 2 or width not in (2, 4, 8) or not 0 <= 2 * fixed_depth < slots:
        raise ValueError("require even slots, width 2/4/8 and a nonempty unfixed middle")
    vocabulary = (b"(", b")", b"[", b"]", b"()", b"[]", b"(())", b"[[]]")[:width]
    canvas = (0,) * fixed_depth + (None,) * (slots - 2 * fixed_depth) + (1,) * fixed_depth
    proposals = tuple(Proposal(i, i, 0, 1.0) for i, token in enumerate(canvas) if token is None)
    support = build_per_position_support(
        canvas=canvas,
        proposals=proposals,
        policy=SupportPolicy(kind=SupportKind.EXPLICIT, vocabulary_size=width),
        explicit_support={
            i: (token,) if token is not None else tuple(range(width))
            for i, token in enumerate(canvas)
        },
    )
    grammar = recursive_grammar("brackets")
    return BenchmarkInstance(
        instance_id=f"recursive-n{slots}-k{width}-d{fixed_depth}",
        grammar=BenchmarkGrammar("brackets", grammar),
        selection_input=SelectionInput(
            grammar,
            canvas,
            proposals,
            support,
            CompositionalByteLevelAdapter(vocabulary),
            EOSPolicy(EOSMode.ABSENT),
        ),
        metadata={
            "family": "brackets",
            "slots": slots,
            "width": width,
            "fixed_depth": fixed_depth,
            "origin": "synthetic_branching_recursive",
            "model_logits": False,
        },
    )
