"""Pinned public tokenizer emissions; no model construction or inference."""

import argparse
import hashlib
import importlib.metadata
import json
import random
from pathlib import Path

MODEL_REVISION = "c8d24a3f4adaeef46881b450e1bf7d1005203bd7"
FILES = {
    "config.json": "02494589af3c9284b381929c576e5865c8f026b5bfed4b9a08d1b38bd4b8623e",
    "tokenizer_config.json": "ffe505983791f3fd517c246cc8fb173bbefc2ef657ce9cf2182ac9d97951f77b",
    "modeling_qwen3.py": "624175f036b6552db473e911e5ec57a09d518c7241b11bc375a7b4bf558675ce",
    "vocab.json": "ca10d7e9fb3ed18575dd1e277a2579c16d108e32f27439684afa0e10b1440910",
    "merges.txt": "8831e4f1a044471340f7c0a83d7bd71306a5b867e95fd870f74d0c5308a904d5",
    "added_tokens.json": "6ad14248a97d96b55f4439a9c441348f7ab308509b6c39d3cbdbfd59d928dce0",
    "special_tokens_map.json": "676a177c1945a87fc5297d228bd9a57c325cb69514644fcdda3b22e113671336",
    "tokenizer.json": "6d55810de1daf81d1d1259355b4b85810385022ab745be68029295935a4eacf0",
    "chat_template.jinja": "87a2728cb8dc9fe424d624542f6060ec05a1d285ebbec578bb078900e33396b5",
    "generation_config.json": "48667a223c617e2e6c2f7f3f7b89a3c8b9e86fc1788055c10583620e10a3552e",
}


def verify_files(folder):
    for name, expected in FILES.items():
        actual = hashlib.sha256((folder / name).read_bytes()).hexdigest()
        if actual != expected:
            raise ValueError(f"pinned source hash mismatch: {name}")


def emissions(folder):
    """ByteLevel BPE inversion, added literals, explicit empty undefined IDs."""
    verify_files(folder)
    config = json.loads((folder / "config.json").read_text())
    vocab = json.loads((folder / "vocab.json").read_text())
    added = json.loads((folder / "added_tokens.json").read_text())
    if len(vocab) != 151643 or set(vocab.values()) != set(range(151643)):
        raise ValueError("ordinary vocabulary differs from declared domain")
    if set(added.values()) != set(range(151643, 151670)) or config["vocab_size"] != 151936:
        raise ValueError("added/output vocabulary differs from declared domain")
    byte_values = [*range(33, 127), *range(161, 173), *range(174, 256)]
    codepoints = byte_values[:]
    extra = 0
    for value in range(256):
        if value not in byte_values:
            byte_values.append(value)
            codepoints.append(256 + extra)
            extra += 1
    inverse = {chr(c): b for c, b in zip(codepoints, byte_values, strict=True)}
    table = [b""] * config["vocab_size"]
    for spelling, token in vocab.items():
        table[token] = bytes(inverse[c] for c in spelling)
    for spelling, token in added.items():
        table[token] = spelling.encode("utf8")
    return tuple(table)


def audit(folder):
    from transformers import AutoTokenizer

    table = emissions(folder)
    tokenizer = AutoTokenizer.from_pretrained(
        folder, local_files_only=True, trust_remote_code=False
    )
    actual = tokenizer.backend_tokenizer.decode_batch(
        [[i] for i in range(len(table))], skip_special_tokens=False
    )
    single_errors = [
        i for i, text in enumerate(actual) if table[i].decode("utf8", errors="replace") != text
    ]
    rng = random.Random(520400)
    words = [tuple(rng.randrange(len(table)) for _ in range(3)) for _ in range(4096)]
    decoded = tokenizer.backend_tokenizer.decode_batch(
        [list(w) for w in words], skip_special_tokens=False
    )
    multi_errors = [
        i
        for i, (w, text) in enumerate(zip(words, decoded, strict=True))
        if b"".join(table[v] for v in w).decode("utf8", errors="replace") != text
    ]
    digest = hashlib.sha256()
    for spelling in table:
        digest.update(len(spelling).to_bytes(8, "little"))
        digest.update(spelling)
    report = {
        "model_revision": MODEL_REVISION,
        "file_sha256": FILES,
        "runtime": {
            p: importlib.metadata.version(p)
            for p in ("transformers", "tokenizers", "torch", "numpy")
        },
        "single_ids": len(table),
        "single_errors": single_errors,
        "multi_token_words": len(words),
        "multi_errors": multi_errors,
        "empty_undefined_ids": sum(not table[i] and actual[i] == "" for i in range(151670, 151936)),
        "emission_table_sha256": digest.hexdigest(),
        "tokenizer_length": len(tokenizer),
        "mask": tokenizer.mask_token_id,
        "eos": tokenizer.eos_token_id,
        "pad": tokenizer.pad_token_id,
        "decoder": json.loads(tokenizer.backend_tokenizer.to_str())["decoder"],
        "audit_performs_no_model_forward": True,
    }
    report["status"] = (
        "PASS"
        if not single_errors and not multi_errors and report["empty_undefined_ids"] == 266
        else "REFUSE"
    )
    return report


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--tokenizer-dir", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    report = audit(args.tokenizer_dir)
    (args.output / "report.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({k: v for k, v in report.items() if k not in ("file_sha256", "decoder")}))
    if report["status"] != "PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
