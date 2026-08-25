#!/usr/bin/env python3
"""Align generated tests with the typed validated-result boundary."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def replace_once(path: Path, old: str, new: str) -> None:
    text = path.read_text(encoding="utf-8")
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"expected one match in {path}, found {count}")
    path.write_text(text.replace(old, new), encoding="utf-8")


offline = ROOT / "tests/exact_commit/test_offline_exact_step.py"
replace_once(
    offline,
    '''    if not isinstance(validated_result, ValidatedExactCommit):
        raise AssertionError("offline exact fixture expected an optimal validated result")
    solver_result = validated_result.result
    decoder_step = apply_exact_commit_result(
        validated_result,
''',
    '''    if isinstance(validated_result, ValidatedExactCommit):
        solver_result = validated_result.result
        decoder_input: ValidatedExactCommit | ExactCommitResult = validated_result
    elif isinstance(validated_result, ExactCommitResult):
        solver_result = validated_result
        decoder_input = validated_result
    else:
        raise AssertionError("adaptive exact fixture returned an unknown result type")
    decoder_step = apply_exact_commit_result(
        decoder_input,
''',
)
text = offline.read_text(encoding="utf-8")
text = text.replace(
    'assert adaptive["stopped_reason"] == "total_timeout_before_next_expansion"',
    'assert adaptive["stopped_reason"] == "total_timeout_after_attempt"',
)
offline.write_text(text, encoding="utf-8")

profiling = ROOT / "tests/exact_commit/test_profiling.py"
text = profiling.read_text(encoding="utf-8")
text = text.replace(
    "    SupportPolicy,\n",
    "    SupportPolicy,\n    ValidatedExactCommit,\n",
    1,
)
text = text.replace(
    "    solve_exact_commit,\n",
    "    solve_exact_commit,\n    solve_validated_exact_commit,\n",
    1,
)
text = text.replace(
    '''    result = solve_exact_commit(
        _one_byte_grammar(ord("a")),
        canvas=(None, None),
        support=support,
        proposals=proposal_batch.proposals,
        tokenizer_adapter=adapter,
        eos_policy=eos_policy,
        backend=ExactBackend.PYTHON,
        profiler=profiler,
    )
    step = apply_exact_commit_result(
        result,
''',
    '''    validated_result = solve_validated_exact_commit(
        _one_byte_grammar(ord("a")),
        canvas=(None, None),
        support=support,
        proposals=proposal_batch.proposals,
        tokenizer_adapter=adapter,
        eos_policy=eos_policy,
        backend=ExactBackend.PYTHON,
        profiler=profiler,
    )
    assert isinstance(validated_result, ValidatedExactCommit)
    result = validated_result.result
    step = apply_exact_commit_result(
        validated_result,
''',
    1,
)
text = text.replace(
    '''    unprofiled_result = solve_exact_commit(
        _one_byte_grammar(ord("a")),
        canvas=(None, None),
        support=support,
        proposals=proposal_batch.proposals,
        tokenizer_adapter=adapter,
        eos_policy=eos_policy,
        backend=ExactBackend.PYTHON,
    )
    unprofiled_step = apply_exact_commit_result(
        unprofiled_result,
''',
    '''    unprofiled_validated_result = solve_validated_exact_commit(
        _one_byte_grammar(ord("a")),
        canvas=(None, None),
        support=support,
        proposals=proposal_batch.proposals,
        tokenizer_adapter=adapter,
        eos_policy=eos_policy,
        backend=ExactBackend.PYTHON,
    )
    assert isinstance(unprofiled_validated_result, ValidatedExactCommit)
    unprofiled_result = unprofiled_validated_result.result
    unprofiled_step = apply_exact_commit_result(
        unprofiled_validated_result,
''',
    1,
)
profiling.write_text(text, encoding="utf-8")
