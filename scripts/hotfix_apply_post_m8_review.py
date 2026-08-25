#!/usr/bin/env python3
"""Correct the staged cleanup script before it is applied."""
from pathlib import Path

path = Path(__file__).with_name("apply_post_m8_review.py")
text = path.read_text(encoding="utf-8")
start = text.index("def require_validated_decoder_input() -> None:\n")
end = text.index("\n\ndef update_tests_for_typed_boundary_and_timeout()", start)
replacement = '''def require_validated_decoder_input() -> None:
    path = "src/mwpc_exact/decoder.py"
    text = read(path)
    text = text.replace(
        ''' + "'''" + '''    validation = result.diagnostics.get("certificate_validation")\n    if not isinstance(validation, Mapping) or validation.get("is_valid") is not True:\n        raise ValueError(\n            "OPTIMAL decoder input requires recorded independent certificate validation"\n        )\n''' + "'''" + ''',
        "",
        1,
    )
    text = text.replace(
        "def apply_exact_commit_result(\n    result: ExactCommitResult,",
        "def apply_exact_commit_result(\n    result: ValidatedExactCommit | ExactCommitResult,",
        1,
    )
    old_validation = ''' + "'''" + '''    if not isinstance(result, ExactCommitResult):\n        raise TypeError("result must be an ExactCommitResult")\n''' + "'''" + '''
    new_validation = ''' + "'''" + '''    if isinstance(result, ValidatedExactCommit):\n        result = result.result\n    elif not isinstance(result, ExactCommitResult):\n        raise TypeError("result must be a ValidatedExactCommit or ExactCommitResult")\n    elif result.status is SolveStatus.OPTIMAL:\n        raise ValueError("OPTIMAL decoder input requires a ValidatedExactCommit")\n''' + "'''" + '''
    if old_validation not in text:
        raise RuntimeError("decoder result validation marker missing")
    text = text.replace(old_validation, new_validation, 1)
    write(path, text)
'''
path.write_text(text[:start] + replacement + text[end:], encoding="utf-8")
