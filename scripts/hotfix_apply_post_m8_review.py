#!/usr/bin/env python3
"""Correct the staged cleanup script before it is applied."""
from pathlib import Path

path = Path(__file__).with_name("apply_post_m8_review.py")
lines = path.read_text(encoding="utf-8").splitlines()
start = next(
    index
    for index, line in enumerate(lines)
    if line == '    start = text.index("def apply_exact_commit_result(\\n")'
)
end = next(
    index
    for index in range(start, len(lines))
    if lines[index] == "    write(path, text)"
)
replacement = [
    "    text = text.replace(",
    '        "def apply_exact_commit_result(\\n    result: ExactCommitResult,",',
    '        "def apply_exact_commit_result(\\n    result: ValidatedExactCommit | ExactCommitResult,",',
    "        1,",
    "    )",
    "    old_validation = '''    if not isinstance(result, ExactCommitResult):\\n        raise TypeError(\"result must be an ExactCommitResult\")\\n'''",
    "    new_validation = '''    if isinstance(result, ValidatedExactCommit):\\n        result = result.result\\n    elif not isinstance(result, ExactCommitResult):\\n        raise TypeError(\"result must be a ValidatedExactCommit or ExactCommitResult\")\\n    elif result.status is SolveStatus.OPTIMAL:\\n        raise ValueError(\"OPTIMAL decoder input requires a ValidatedExactCommit\")\\n'''",
    "    if old_validation not in text:",
    '        raise RuntimeError("decoder result validation marker missing")',
    "    text = text.replace(old_validation, new_validation, 1)",
    "    write(path, text)",
]
updated = lines[:start] + replacement + lines[end + 1 :]
path.write_text("\n".join(updated) + "\n", encoding="utf-8")
