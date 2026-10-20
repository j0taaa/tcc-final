"""Untimed rank probe using the maintained CFG frontend, original IDs intact."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from audit import enumerate_dag, integer_rank
from contraction import Node, compile_forest
from operational import MODEL, sha_file

from mwpc_exact.cfg_posterior import compile_cfg_sampler
from mwpc_exact.eos_policy import EOSMode, EOSPolicy
from mwpc_exact.reference.byte_grammars import _SourceGrammarBuilder
from mwpc_exact.reference.json_grammar import json_source_grammar
from mwpc_exact.reference.normalization import normalize_to_cnf
from mwpc_exact.state import SelectionInput
from mwpc_exact.support import SupportPolicy, build_per_position_support
from mwpc_exact.tokenizer_bytes import CompositionalByteLevelAdapter
from mwpc_exact.types import SupportKind


def dyck_source():
    builder = _SourceGrammarBuilder(("S", "N"), start="S")
    builder.rule("S", "N", "S")
    builder.rule("S")
    builder.rule("N", b"(", "S", b")")
    builder.rule("N", b"[", "S", b"]")
    return builder.build()


def convert(plan):
    """Children precede parent in the maintained plan's evaluation order."""
    nodes, converted = [], {}
    for index in plan.order:
        alternatives = []
        for term in plan.terms[index]:
            alternatives.append(len(nodes))
            if term.choice is not None:
                position, choice = term.choice
                token = plan.state.support.rows[position][choice]
                nodes.append(Node("leaf", position=position, token=token))
            else:
                nodes.append(Node("and", tuple(converted[c] for c in term.children)))
        converted[index] = len(nodes)
        nodes.append(Node("or", tuple(alternatives)))
    return nodes, converted[plan.root]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(args.output)
    from tokenizers import Tokenizer

    assert sha_file(MODEL / "tokenizer.json") == (
        "6d55810de1daf81d1d1259355b4b85810385022ab745be68029295935a4eacf0"
    )
    tokenizer = Tokenizer.from_file(str(MODEL / "tokenizer.json"))
    chars = sorted(set('[]{}":,01ab ()'))
    ids, text_by_id = {}, {}
    for char in chars:
        encoded = tokenizer.encode(char, add_special_tokens=False).ids
        assert len(encoded) == 1
        token = encoded[0]
        assert tokenizer.decode(encoded, skip_special_tokens=False) == char
        assert token not in text_by_id
        ids[char], text_by_id[token] = token, char
    emissions = [None] * 151936
    for token, char in text_by_id.items():
        emissions[token] = char.encode("ascii")
    cases = [("json", n, None) for n in (8, 16, 32)]
    cases += [("dyck", n, None) for n in (4, 8, 16, 32)]
    cases += [("json_array", 5, "[x,x]"), ("json_object", 13, '{"a":x,"b":x}')]
    report = []
    for family, n, template in cases:
        record = {"case": f"{family}{n}", "timings": "not measured", "gpu_used": False}
        try:
            source = dyck_source() if family == "dyck" else json_source_grammar()
            alphabet = "()[]" if family == "dyck" else '[]{}":,01ab '
            if template:
                assert len(template) == n
                rows = tuple((ids["0"], ids["1"]) if c == "x" else (ids[c],) for c in template)
                canvas = tuple(None if c == "x" else ids[c] for c in template)
            else:
                rows = (tuple(sorted(ids[c] for c in alphabet)),) * n
                canvas = (None,) * n
            support = build_per_position_support(
                canvas=canvas,
                policy=SupportPolicy(kind=SupportKind.EXPLICIT, vocabulary_size=151936),
                explicit_support=dict(enumerate(rows)),
            )
            state = SelectionInput(
                normalize_to_cnf(source).grammar,
                canvas,
                (),
                support,
                CompositionalByteLevelAdapter(tuple(emissions)),
                EOSPolicy(EOSMode.ABSENT),
            )
            parser_plan = compile_cfg_sampler(
                source,
                state,
                max_chart_cells=100000,
                max_alternatives=500000,
                timeout_seconds=120,
            )
            if parser_plan.root is None:
                record.update(status="infeasible_on_support")
            else:
                nodes, root = convert(parser_plan)
                plan = compile_forest(nodes, root, n)
                per_id = {}
                for token, basis in plan.by_token.items():
                    varying = sum(any(row[j] for row in basis.rows) for j in range(n))
                    per_id[token] = {
                        "text": text_by_id[token],
                        "q": len(basis.pivots),
                        "varying_positions": varying,
                    }
                sparse = sum(x["varying_positions"] for x in per_id.values())
                record.update(
                    status="complete",
                    parser_cells=len(parser_plan.terms),
                    parser_alternatives=parser_plan.alternatives,
                    stats=plan.stats,
                    per_id=per_id,
                    sparse_queries=sparse,
                    contracted_queries=plan.stats["sum_q"],
                )
                if template or (family == "dyck" and n <= 8):
                    assignments = enumerate_dag(nodes, root)
                    words = [tuple(v for _, v in word) for word in assignments]
                    for word in words:
                        text = "".join(text_by_id[v] for v in word)
                        if template:
                            json.loads(text)
                        else:
                            stack = []
                            for char in text:
                                if char in "([":
                                    stack.append(char)
                                else:
                                    assert stack and stack.pop() == {")": "(", "]": "["}[char]
                            assert not stack
                    for token, basis in plan.by_token.items():
                        vectors = [tuple(int(v == token) for v in word) for word in words]
                        diffs = [
                            tuple(a - b for a, b in zip(x, vectors[0], strict=True))
                            for x in vectors
                        ]
                        assert integer_rank(diffs) == len(basis.pivots)
                    if template:
                        assert len(words) == 4
                    record["independently_checked_words"] = len(words)
        except Exception as exc:
            record.update(status="refused_or_error", exception=type(exc).__name__, reason=str(exc))
        report.append(record)
        print(json.dumps(record, sort_keys=True), flush=True)
        args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print("sha256", hashlib.sha256(args.output.read_bytes()).hexdigest(), flush=True)


if __name__ == "__main__":
    main()
