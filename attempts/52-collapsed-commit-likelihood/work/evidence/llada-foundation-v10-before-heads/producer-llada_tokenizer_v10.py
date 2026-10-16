"""Pinned LLaDA full-original-V ByteLevel audit, without model construction."""

import argparse
import hashlib
import json
import random
from pathlib import Path

REVISION = "08b83a6feb34df1a6011b80c3c00c7563e963b07"
VOCABULARY = 126464
EOS = 126081
MASK = 126336
FILES = {
    "config.json": "5f99fefe855fdb5100bb6cadb57bdb09fae723ad54811f95c00ecacf29d58a6a",
    "configuration_llada.py": "c947a64d8b735affa69d5adeb416c83ce607c8925270884e4471ae11068e2bfe",
    "modeling_llada.py": "98bac7e53fef0bb7ca01e3716c11a7f710d183e10dbb9783b88db9dbba2e3766",
    "tokenizer.json": "071eb20fe7bd601550b1b7838ff696d6c93b88f51257f753303d3df23163c381",
    "tokenizer_config.json": "b9a6102c39a4f42f47f0d63fc6cee58a2381199d90f2a4f39b3f6871f32b4119",
    "special_tokens_map.json": "e9f1f0f6fa133da3169ae69b1969c51cced047a900050893d7a0711c6bd063aa",
    "model.safetensors.index.json": (
        "28b4ec27206e42e7ade630450e6ce618bd197acf34d35120e8e86d2bb910a408"
    ),
}
WEIGHTS = (
    "ff6699df9635a267fb4ac801ea8012d39b21bb22ed290d5a57128521b889c230",
    "b8ddf571b47f57ce654913877f3625d2c7b9a4c3f81cb6f41f6c3055473b0281",
    "8347db2fd61a3b5bad2970c2f83ecb84b93632e276a41ca169dcc5efae15462c",
    "93d8706872e7432d5cd40c9a61f9f9d270c101828cef2adaf27c67743d3dcf1a",
    "ff5f765eb7ec8bfdbe3b962a9e920d71de43d55e04eb4844710c0efcc8855092",
    "f25d4cc57b24a79a840d49c3b25d9a22dd5caf3a9766f591e4625377901194e2",
)


def digest(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def verify_files(folder, weights=False):
    result = {}
    for name, expected in FILES.items():
        value = digest(folder / name)
        if value != expected:
            raise ValueError(f"pinned LLaDA metadata/source mismatch: {name}")
        result[name] = {"sha256": value, "bytes": (folder / name).stat().st_size}
    if weights:
        for index, expected in enumerate(WEIGHTS, 1):
            name = f"model-{index:05d}-of-00006.safetensors"
            value = digest(folder / name)
            if value != expected:
                raise ValueError(f"pinned original weight mismatch: {name}")
            result[name] = {"sha256": value, "bytes": (folder / name).stat().st_size}
    return result


def emissions(folder):
    verify_files(folder)
    data = json.loads((folder / "tokenizer.json").read_text())
    config = json.loads((folder / "config.json").read_text())
    ordinary, added = data["model"]["vocab"], data["added_tokens"]
    if (
        data["model"]["type"] != "BPE"
        or data["decoder"]["type"] != "ByteLevel"
        or set(ordinary.values()) != set(range(126080))
        or {t["id"] for t in added} != set(range(126080, 126349))
        or config["vocab_size"] != VOCABULARY
        or config["eos_token_id"] != EOS
        or config["pad_token_id"] != EOS
        or config["mask_token_id"] != MASK
    ):
        raise ValueError("original tokenizer/head/control domain differs from contract")
    byte_values = [*range(33, 127), *range(161, 173), *range(174, 256)]
    codepoints = byte_values[:]
    extra = 0
    for value in range(256):
        if value not in byte_values:
            byte_values.append(value)
            codepoints.append(256 + extra)
            extra += 1
    inverse = {chr(c): b for c, b in zip(codepoints, byte_values, strict=True)}
    table = [b""] * VOCABULARY
    for spelling, token in ordinary.items():
        table[token] = bytes(inverse[c] for c in spelling)
    for entry in added:
        table[entry["id"]] = entry["content"].encode("utf8")
    return tuple(table)


def audit(folder, weights=False):
    from tokenizers import Tokenizer

    source = verify_files(folder, weights)
    table = emissions(folder)
    tokenizer = Tokenizer.from_file(str(folder / "tokenizer.json"))
    singles = tokenizer.decode_batch([[i] for i in range(VOCABULARY)], skip_special_tokens=False)
    errors = [i for i, text in enumerate(singles) if table[i].decode("utf8", "replace") != text]
    rng = random.Random(52100)
    triples = [tuple(rng.randrange(VOCABULARY) for _ in range(3)) for _ in range(4096)]
    decoded = tokenizer.decode_batch([list(w) for w in triples], skip_special_tokens=False)
    multi_errors = [
        i
        for i, (word, text) in enumerate(zip(triples, decoded, strict=True))
        if b"".join(table[v] for v in word).decode("utf8", "replace") != text
    ]
    undefined = [i for i in range(126349, VOCABULARY) if not table[i] and singles[i] == ""]
    if errors or multi_errors or len(undefined) != 115:
        raise ValueError(
            f"official original-ID emission disagreement: {errors[:5]}, {multi_errors[:5]}"
        )
    checksum = hashlib.sha256()
    for row in table:
        checksum.update(len(row).to_bytes(8, "little"))
        checksum.update(row)
    return {
        "status": "PASS",
        "model_revision": REVISION,
        "source_sha256_bytes": source,
        "original_ids": VOCABULARY,
        "single_errors": errors,
        "triples": len(triples),
        "triple_errors": multi_errors,
        "empty_undefined_ids": undefined,
        "emission_sha256": checksum.hexdigest(),
        "model_constructed": False,
        "new_model_forwards": 0,
    }


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--model-dir", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    ap.add_argument("--weights", action="store_true")
    args = ap.parse_args()
    result = audit(args.model_dir, args.weights)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x") as stream:
        stream.write(json.dumps(result, indent=2) + "\n")
    print(
        json.dumps(
            {
                k: v
                for k, v in result.items()
                if k not in ("source_sha256_bytes", "empty_undefined_ids")
            }
        )
    )
