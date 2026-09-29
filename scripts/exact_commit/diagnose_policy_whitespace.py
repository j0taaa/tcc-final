#!/usr/bin/env python3
"""Post-hoc sensitivity to lexical whitespace; never change archived primary scores."""

import io
import tokenize
from collections import defaultdict

from mwpc_research.grounded_calls import grounded_grade
from mwpc_research.schema_calls import strict_schema_grade
from mwpc_research.tool_screen import normalize_tool_call


def normalize_lexical_whitespace(output):
    """Preserve token strings, including quoted contents, while joining physical lines."""
    ignored = {tokenize.NL, tokenize.NEWLINE, tokenize.INDENT, tokenize.DEDENT, tokenize.ENDMARKER}
    try:
        # Outer parentheses suppress Python indentation rules during lexical analysis.
        tokens = list(tokenize.generate_tokens(io.StringIO("(" + output + "\n)").readline))
    except (tokenize.TokenError, IndentationError, SyntaxError):
        return output
    kept = [token for token in tokens if token.type not in ignored]
    return " ".join(token.string for token in kept[1:-1])


def diagnose(config, rows):
    groups = defaultdict(list)
    for row in rows:
        output = normalize_lexical_whitespace(row["output"])
        task = row["task"]
        correct = row["status"] == "complete" and (
            (grounded_grade if config.get("grounded_calls", False) else strict_schema_grade)(
                output, task["function"], task["ground_truth"]
            )
            if config.get("schema_calls", False)
            else normalize_tool_call(output) == task["expected"]
        )
        groups[row["method"]].append((row, correct, output))
    return {
        name: {
            "n": len(items),
            "primary_correct": sum(row["correct"] for row, _, _ in items),
            "after_whitespace_correct": sum(correct for _, correct, _ in items),
            "changed_grades": [
                {
                    "task_id": row["task"]["id"],
                    "before": row["correct"],
                    "after": correct,
                    "raw_output": row["output"],
                    "normalized": output,
                }
                for row, correct, output in items
                if correct != row["correct"]
            ],
        }
        for name, items in sorted(groups.items())
    }
