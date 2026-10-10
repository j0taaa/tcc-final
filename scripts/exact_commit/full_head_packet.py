"""Small preselected full-head packet: offline origin audit without model weights."""

import argparse
import hashlib
import io
import json
import zipfile
from pathlib import Path


def digest(data):
    return hashlib.sha256(data).hexdigest()


def create(capture, packet):
    metadata = json.loads((capture / "metadata.json").read_text())
    selected = metadata["selected"][0]
    if metadata["phase"] != "independent":
        raise ValueError("packet selection requires the pinned independent capture")
    name = selected["key"] + "-4"
    files = [
        "metadata.json",
        "vocabulary.json",
        name + ".json",
        name + ".npy",
        name + ".logits.npy",
    ]
    data = {p: (capture / p).read_bytes() for p in files}
    data["original.json"] = selected["text"].encode("utf8")
    root = Path(__file__).resolve().parents[2]
    data["JSONTestSuite-LICENSE"] = (root / "tests/data/json_suite/LICENSE").read_bytes()
    data["THIRD_PARTY_LICENSES.md"] = (root / "THIRD_PARTY_LICENSES.md").read_bytes()
    manifest = dict(
        schema=1,
        case=name,
        selection="First pinned independent document/four masks, chosen before captures/timings",
        external_source=dict(
            repository="https://github.com/nst/JSONTestSuite",
            revision="1ef36fa01286573e846ac449e8683f8833c5b26a",
            file=selected["file"],
            source_sha256=selected["source_sha256"],
        ),
        effective_policy=(
            "F32 CUDA forward, F64 CPU full softmax with MASK50257 zero. "
            "All50258 original IDs, no top-K/alphabet/gold injection; other special IDs "
            "retain probability and have unsupported ordinary byte emissions. "
            "Legacy model-loader config fields top_k/support_policies/probes/CPU numeric_reference "
            "are NOT the effective capture policy. "
            "Binary probabilities normalized as rationals per row."
        ),
        scope=(
            "Complete original masked heads, full probability rows, original bytes and tokenizer. "
            "Offline softmax linkage, not independent rerun/proof of the neural model. "
            "Other complete heads remain local with hashes."
        ),
        files={p: dict(sha256=digest(raw), bytes=len(raw)) for p, raw in sorted(data.items())},
    )
    data["manifest.json"] = (json.dumps(manifest, indent=2) + "\n").encode()
    packet.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(packet, "x", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for name, raw in sorted(data.items()):
            info = zipfile.ZipInfo(name, (1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            archive.writestr(info, raw)
    return dict(
        packet_sha256=digest(packet.read_bytes()),
        packet_bytes=packet.stat().st_size,
        case=manifest["case"],
    )


def check(packet, *, torch_exact=False):
    import numpy as np

    from mwpc_exact.tokenizer_bytes import CompositionalByteLevelAdapter

    with zipfile.ZipFile(packet) as archive:
        manifest = json.loads(archive.read("manifest.json"))
        if set(archive.namelist()) != {*manifest["files"], "manifest.json"}:
            raise ValueError("packet has missing/unexpected inputs")
        data = {p: archive.read(p) for p in manifest["files"]}
    for name, inventory in manifest["files"].items():
        if len(data[name]) != inventory["bytes"] or digest(data[name]) != inventory["sha256"]:
            raise ValueError("packet input differs: " + name)
    metadata, name = json.loads(data["metadata.json"]), manifest["case"]
    case = json.loads(data[name + ".json"])
    if digest(data[name + ".npy"]) != case["probabilities_sha256"]:
        raise ValueError("probability row does not match captured metadata")
    if digest(data[name + ".logits.npy"]) != case["raw_logits_sha256"]:
        raise ValueError("raw original head does not match captured metadata")
    if digest(data["vocabulary.json"]) != metadata["vocabulary_sha256"]:
        raise ValueError("original tokenizer vocabulary differs")
    original = metadata["selected"][0]
    if digest(data["original.json"]) != original["source_sha256"]:
        raise ValueError("external original JSON bytes differ")
    adapter = CompositionalByteLevelAdapter.from_token_pieces(json.loads(data["vocabulary.json"]))
    if adapter.detokenize_bytes(original["tokens"]) != data["original.json"]:
        raise ValueError("original token IDs do not reconstruct the unchanged document")
    positions = [p for p, t in enumerate(case["canvas"]) if t is None]
    if positions != case["positions"] or any(
        t is not None and t != original["tokens"][p] for p, t in enumerate(case["canvas"])
    ):
        raise ValueError("captured frame differs from original fixed IDs")
    scores = np.load(io.BytesIO(data[name + ".logits.npy"]), allow_pickle=False)
    probabilities = np.load(io.BytesIO(data[name + ".npy"]), allow_pickle=False)
    if scores.shape != probabilities.shape or scores.shape != (
        len(positions),
        len(adapter.emissions),
    ):
        raise ValueError("full vocabulary/head dimensions differ")
    if not np.isfinite(scores).all() or not np.array_equal(
        scores, scores.astype("float32").astype("float64")
    ):
        raise ValueError("original F32 head lift changed")
    scores[:, metadata["config"]["mask_token_id"]] = -np.inf
    stable = np.exp(scores - scores.max(axis=1, keepdims=True))
    stable /= stable.sum(axis=1, keepdims=True)
    # This is a conservative cross-library numerical diagnostic, not equality
    # of rational inputs. Torch below reproduces the actual capture bit-for-bit.
    rtol = 8 * scores.shape[1] * np.finfo(np.float64).eps
    if not np.allclose(stable, probabilities, rtol=rtol, atol=0):
        raise ValueError("full-head softmax does not reproduce archived probabilities")
    exact = None
    if torch_exact:
        import torch

        torch.set_num_threads(1)
        reproduced = torch.from_numpy(scores).softmax(-1).numpy()
        exact = bool(np.array_equal(reproduced, probabilities))
        if not exact:
            raise ValueError("Torch full-head probabilities differ bit-for-bit")
    return dict(
        verification="PASS",
        case=name,
        full_rows=len(positions),
        vocabulary=scores.shape[1],
        numpy_softmax_rtol=str(rtol),
        numpy_max_absolute_difference=float(np.max(np.abs(stable - probabilities))),
        torch_bit_equal=exact,
        original_bytes_reconstructed=True,
        model_independently_rerun=False,
        packet_sha256=digest(packet.read_bytes()),
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--create", type=Path)
    parser.add_argument("--packet", type=Path, required=True)
    parser.add_argument("--torch-exact", action="store_true")
    args = parser.parse_args()
    result = (
        create(args.create, args.packet)
        if args.create
        else check(args.packet, torch_exact=args.torch_exact)
    )
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
