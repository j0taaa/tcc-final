"""Execute the pinned official Python checker functions, no custom value metric."""

import ast
import hashlib
import re
from enum import Enum
from types import SimpleNamespace

CHECKER_SHA256 = "2aae7a68461a8f76c0be3894c8901b66b56967a1989d3ab066051e3fb97f1538"


class Language(Enum):
    PYTHON = "python"
    JAVA = "java"
    JAVASCRIPT = "javascript"


def load_checker(path):
    raw = path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != CHECKER_SHA256:
        raise ValueError("official checker source mismatch")
    tree = ast.parse(raw)
    # Only imports are replaced: Python enum and no dotted-name conversion.
    # Every function body/constant is original. Non-Python conversion unused.
    tree.body = [node for node in tree.body if not isinstance(node, (ast.Import, ast.ImportFrom))]
    scope = {
        "re": re,
        "Language": Language,
        "MODEL_CONFIG_MAPPING": {"A31": SimpleNamespace(underscore_to_dot=False)},
    }
    exec(compile(tree, str(path), "exec"), scope)

    def check(function, output, gold):
        if not isinstance(output, dict) or set(output) != {"name", "arguments"}:
            return False
        if not isinstance(output["name"], str) or not isinstance(output["arguments"], dict):
            return False
        return bool(
            scope["simple_function_checker"](
                function, {output["name"]: output["arguments"]}, gold[0], Language.PYTHON, "A31"
            )["valid"]
        )

    return check


def strict_json(text):
    import json

    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError("duplicate JSON key")
            result[key] = value
        return result

    return json.loads(
        text,
        object_pairs_hook=unique,
        parse_constant=lambda s: (_ for _ in ()).throw(ValueError(s)),
    )
