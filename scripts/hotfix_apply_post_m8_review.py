#!/usr/bin/env python3
"""Correct the staged cleanup script before it is applied."""
from pathlib import Path

path = Path(__file__).with_name("apply_post_m8_review.py")
text = path.read_text(encoding="utf-8")
old = r'''    start = text.index("def apply_exact_commit_result(\n")
    end = text.index("\n\n__all__ =", start)
    function = text[start:end]
    function = re.sub(r"\bresult\b", "solver_result", function)
    function = function.replace(
        "def apply_exact_commit_result(\n    solver_result: ExactCommitResult,",
        "def apply_exact_commit_result(\n    result: ValidatedExactCommit | ExactCommitResult,",
        1,
    )
    old_validation = '''    if not isinstance(solver_result, ExactCommitResult):\n        raise TypeError("result must be an ExactCommitResult")\n'''
    new_validation = '''    if isinstance(result, ValidatedExactCommit):\n        solver_result = result.result\n    elif isinstance(result, ExactCommitResult):\n        solver_result = result\n    else:\n        raise TypeError("result must be a ValidatedExactCommit or ExactCommitResult")\n    if (\n        solver_result.status is SolveStatus.OPTIMAL\n        and not isinstance(result, ValidatedExactCommit)\n    ):\n        raise ValueError("OPTIMAL decoder input requires a ValidatedExactCommit")\n'''
    if old_validation not in function:
        raise RuntimeError("decoder result validation marker missing")
    function = function.replace(old_validation, new_validation, 1)
    text = text[:start] + function + text[end:]
'''
new = r'''    text = text.replace(
        "def apply_exact_commit_result(\n    result: ExactCommitResult,",
        "def apply_exact_commit_result(\n    result: ValidatedExactCommit | ExactCommitResult,",
        1,
    )
    old_validation = '''    if not isinstance(result, ExactCommitResult):\n        raise TypeError("result must be an ExactCommitResult")\n'''
    new_validation = '''    if isinstance(result, ValidatedExactCommit):\n        result = result.result\n    elif not isinstance(result, ExactCommitResult):\n        raise TypeError("result must be a ValidatedExactCommit or ExactCommitResult")\n    elif result.status is SolveStatus.OPTIMAL:\n        raise ValueError("OPTIMAL decoder input requires a ValidatedExactCommit")\n'''
    if old_validation not in text:
        raise RuntimeError("decoder result validation marker missing")
    text = text.replace(old_validation, new_validation, 1)
'''
if old not in text:
    raise RuntimeError("staged decoder patch block not found")
path.write_text(text.replace(old, new, 1), encoding="utf-8")
