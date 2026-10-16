"""Official tokenizer and SYNTHETIC full-V states only, no old-path replay."""

import argparse
import json
import resource
from pathlib import Path

from .flat_language import MANY
from .llada_tokenizer_v10 import EOS, audit, emissions
from .terminal_compiler import NumericSuffix, TerminalCompiler, encode


def run(model_dir, output):
    output.mkdir(parents=True, exist_ok=False)
    token_audit = audit(model_dir)
    table = emissions(model_dir)
    one, brace = table.index(b"1"), table.index(b"}")
    compilers = [TerminalCompiler(NumericSuffix(table, EOS, EOS), erase) for erase in (False, True)]
    cases = []
    for width, fixed in (
        (4, {}),
        (4, {1: one, 2: brace, 3: EOS}),
        (64, {0: one, 1: brace, 63: EOS}),
    ):
        values = []
        for compiler in compilers:
            grouped = compiler.classify(width, fixed)
            assert grouped == compiler.generic_graph_control(width, fixed)
            values.append(grouped)
        assert values[0] is MANY
        if not fixed:
            assert values[1] is MANY
        elif 0 in fixed:
            assert values[1] == b"1}"
        else:
            assert values[1] is MANY  # leading free slot can change the number
        cases.append({"width": width, "fixed": fixed, "results": list(map(encode, values))})
    result = {
        "status": "PASS",
        "scope": "official tokenizer and SYNTHETIC full-V states only",
        "tokenizer": token_audit,
        "SYNTHETIC_cases": cases,
        "new_model_forwards": 0,
        "old_real_path_certificates": 0,
        "classes": [len(c.members) for c in compilers],
        "peak_CPU_process_RSS_bytes": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * 1024,
    }
    (output / "summary.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--model-dir", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    a = p.parse_args()
    run(a.model_dir, a.output)
