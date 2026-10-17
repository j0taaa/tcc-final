"""Pinned text/AST audit and independent arithmetic; never import vendor code."""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
import math
from fractions import Fraction
from pathlib import Path

PIN = "0c927733af21f156d61743c4a40d03d13e65c16b"
HASHES = {
    "tokenization_p10.py": "40f99ebd2ae674d7d58bb25efbabf4c8b285a8843a5861133029595351672c6b",
    "configuration_regresslm.py": (
        "5a72f125c3d1462f5394fdd0e376ee3ed3ac56b6f5a368585f527a59eab07313"
    ),
    "modeling_regresslm.py": "a082dd3e10fb40ceb96f56e8e887410f947b7d8e578f7a76da2a885e6088558c",
    "config.json": "56875fa550cb1560e4d7642bcf615c9886b66cd93fc0c7ed1c7f42553025e9c8",
    "generation_config.json": "586fc33af4352570ac65042951115bef7fa2a4c3d0ff007636636842dd1989e1",
    "ieee_vocab.json": "b79c82d4706d5a199086e5895e4dfb8b8190271e2e2840f4fda02d63675be319",
}


def method(tree: ast.Module, cls_name: str, method_name: str) -> ast.FunctionDef:
    cls = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == cls_name)
    return next(n for n in cls.body if isinstance(n, ast.FunctionDef) and n.name == method_name)


def inspect(source_dir: Path) -> dict:
    texts = {}
    for name, expected in HASHES.items():
        data = (source_dir / name).read_bytes()
        if hashlib.sha256(data).hexdigest() != expected:
            raise ValueError(f"pinned source mismatch: {name}")
        texts[name] = data.decode()
    cfg = json.loads(texts["config.json"])
    vocab = json.loads(texts["ieee_vocab.json"])
    layout = {
        k: cfg[k]
        for k in (
            "decoder_vocab_size",
            "ieee_base",
            "ieee_exponent_digits",
            "ieee_mantissa_digits",
            "num_tokens_per_obj",
            "max_num_objs",
        )
    }
    assert list(layout.values()) == [13, 10, 2, 5, 9, 1]
    assert vocab == {"<pad>": 0, "<+>": 1, "<->": 2} | {f"<{d}>": d + 3 for d in range(10)}
    tok = ast.parse(texts["tokenization_p10.py"])
    conv = method(tok, "IEEEFloatTokenizer", "tokens_to_float")
    ret = conv.body[-1]
    assert isinstance(ret, ast.Return)
    expression = ast.unparse(ret.value)
    assert expression == "sign * self.base ** exponent * mantissa"
    allowed = method(tok, "IEEEFloatTokenizer", "_possible_next_tokens")
    assert "range(self.base)" in ast.unparse(allowed)
    model = ast.parse(texts["modeling_regresslm.py"])
    proc = method(model, "RegressLMForConditionalGeneration", "_get_logits_processor")
    assert isinstance(proc.body[-1], ast.Return)
    assert ast.unparse(proc.body[-2]) == (
        "processors.append(_NumericLogitsProcessor(self.constraint_helper))"
    )

    def word(sign: int, exponent: int, mantissa: int) -> list[int]:
        return [0, 1 if sign == 1 else 2, 1 if exponent >= 0 else 2] + [
            vocab[f"<{d}>"] for d in f"{abs(exponent):02d}{mantissa:05d}"
        ]

    pairs = []
    cases = [
        ("positive_ulp", 1, -1, 30000, 0, 3000, True),
        ("negative_ulp", -1, -1, 30000, 0, 3000, True),
        ("equal_integer", 1, 0, 30000, 1, 3000, False),
        ("equal_fraction", 1, -1, 10000, 0, 1000, False),
        ("positive_zero", 1, -99, 0, 99, 0, False),
        ("negative_zero", -1, -99, 0, 99, 0, False),
    ]
    for name, sign, e1, n1, e2, n2, different in cases:
        exact1 = sign * Fraction(n1, 10000) * Fraction(10) ** e1
        exact2 = sign * Fraction(n2, 10000) * Fraction(10) ** e2
        assert exact1 == exact2
        # Independently evaluate the literal arithmetic expression observed in
        # source. This does NOT execute the native tokenizer or model module.
        a = sign * (10**e1) * (n1 / 10000)
        b = sign * (10**e2) * (n2 / 10000)
        assert (a != b) == different
        if different:
            assert abs(Fraction(a) - Fraction(b)) == Fraction(math.ulp(a))
        pairs.append(
            {
                "name": name,
                "original_ids": [word(sign, e1, n1), word(sign, e2, n2)],
                "exact_decimal": str(exact1),
                "literal_float_hex": [a.hex(), b.hex()],
                "binary64_atoms_differ": different,
            }
        )
    corners = [
        sign * (10**e) * (n / 10000) for sign in (-1, 1) for e in (-99, 99) for n in (0, 1, 99999)
    ]
    assert all(math.isfinite(v) for v in corners)
    assert all(
        sign * (10**e) * (n / 10000) != 0 for sign in (-1, 1) for e in (-99, 99) for n in (1, 99999)
    )
    return {
        "revision": PIN,
        "source_sha256": HASHES,
        "layout": layout,
        "observed_return_expression": expression,
        "pairs": pairs,
        "finite_corner_checks": len(corners),
        "scope": "Text/AST and independent literal arithmetic only; not native execution.",
        "vendor_modules_executed": 0,
        "neural_forwards": 0,
        "weight_downloads": 0,
        "dataset_rows_read": 0,
        "quantile_solver_implemented": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-dir", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    result = inspect(args.source_dir)
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    print(
        json.dumps(
            {
                "pairs": len(result["pairs"]),
                "different_float_pairs": sum(p["binary64_atoms_differ"] for p in result["pairs"]),
                "finite_corner_checks": result["finite_corner_checks"],
                "neural_forwards": 0,
            }
        )
    )


if __name__ == "__main__":
    main()
