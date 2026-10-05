"""Audited CPU kernel port for the pinned official MDLM checkpoint.

The official Apache-2.0 architecture is downloaded unchanged and hash-checked.
Only rearrangement, split-half rotary and packed noncausal attention calls are
provided on CPU. This is not a claim of bitwise FlashAttention equivalence.
"""

from __future__ import annotations

import hashlib
import json
import sys
import types
from itertools import pairwise
from pathlib import Path

import torch
import torch.nn.functional as F


def rearrange(tensor, pattern, **sizes):
    if pattern == "b s (three h d) -> b s three h d":
        return tensor.reshape(*tensor.shape[:2], sizes["three"], sizes["h"], -1)
    if pattern == "b s ... -> (b s) ...":
        return tensor.flatten(0, 1)
    if pattern == "(b s) h d -> b s (h d)":
        return tensor.reshape(sizes["b"], -1, tensor.shape[-2] * tensor.shape[-1])
    raise ValueError(f"unsupported audited MDLM rearrangement: {pattern}")


def rotary(qkv, cos, sin):
    dim = qkv.shape[-1]
    fullcos = torch.cat((cos, cos), -1)[None, :, None, None, :]
    fullsin = torch.cat((sin, sin), -1)[None, :, None, None, :]
    querykey = qkv[:, :, :2]
    rotated = torch.cat((-querykey[..., dim // 2 :], querykey[..., : dim // 2]), -1)
    return torch.cat((querykey * fullcos + rotated * fullsin, qkv[:, :, 2:]), 2)


def attention(qkv, boundaries, max_sequence_length, dropout, *, causal):
    if dropout or causal:
        raise ValueError("audited CPU inference requires noncausal zero-dropout attention")
    outputs = []
    for lo, hi in pairwise(boundaries):
        block = qkv[int(lo) : int(hi)]
        q, k, v = (block[:, i].transpose(0, 1)[None] for i in range(3))
        outputs.append(
            F.scaled_dot_product_attention(q, k, v, dropout_p=0.0, is_causal=False)
            .squeeze(0)
            .transpose(0, 1)
        )
    return torch.cat(outputs, 0)


def load_cpu_model(config, cache: Path):
    from huggingface_hub import hf_hub_download
    from safetensors.torch import load_file

    files = {
        name: Path(
            hf_hub_download(
                config["model_id"], name, revision=config["model_revision"], cache_dir=str(cache)
            )
        )
        for name in (
            "config.json",
            "configuration_mdlm.py",
            "modeling_mdlm.py",
            "model.safetensors",
        )
    }
    hashes = {name: hashlib.sha256(path.read_bytes()).hexdigest() for name, path in files.items()}
    if hashes != config["checkpoint_sha256"]:
        raise ValueError("official MDLM files differ from the frozen hashes")
    configuration = types.ModuleType("mwpc_mdlm_cpu_configuration")
    configuration.__file__ = str(files["configuration_mdlm.py"])
    sys.modules[configuration.__name__] = configuration
    exec(
        compile(files["configuration_mdlm.py"].read_text(), configuration.__file__, "exec"),
        configuration.__dict__,
    )
    source = files["modeling_mdlm.py"].read_text()
    for line in (
        "import flash_attn\n",
        "import flash_attn.layers.rotary\n",
        "from einops import rearrange\n",
        "from .configuration_mdlm import MDLMConfig\n",
    ):
        if source.count(line) != 1:
            raise ValueError("official MDLM dependency surface differs")
        source = source.replace(line, "")
    source = source.replace(
        "torch.cuda.amp.autocast(enabled=False)", 'torch.autocast(device_type="cpu", enabled=False)'
    )
    source = source.replace(
        "torch.cuda.amp.autocast(dtype=torch.bfloat16)",
        'torch.autocast(device_type="cpu", enabled=False)',
    )
    adapted = cache / "audited_mdlm_cpu.py"
    adapted.parent.mkdir(parents=True, exist_ok=True)
    adapted.write_text(source)
    module = types.ModuleType("mwpc_mdlm_cpu_official")
    module.__file__ = str(adapted)
    module.__dict__.update(
        MDLMConfig=configuration.MDLMConfig,
        rearrange=rearrange,
        flash_attn=types.SimpleNamespace(
            layers=types.SimpleNamespace(
                rotary=types.SimpleNamespace(apply_rotary_emb_qkv_=rotary)
            ),
            flash_attn_interface=types.SimpleNamespace(flash_attn_varlen_qkvpacked_func=attention),
        ),
    )
    sys.modules[module.__name__] = module
    exec(compile(source, str(adapted), "exec"), module.__dict__)
    architecture = configuration.MDLMConfig(**json.loads(files["config.json"].read_text()))
    model = module.MDLM(architecture)
    model.load_state_dict(load_file(str(files["model.safetensors"]), device="cpu"), strict=True)
    model.eval()
    return model, hashes, hashlib.sha256(source.encode()).hexdigest()
