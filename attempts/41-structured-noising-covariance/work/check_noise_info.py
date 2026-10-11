"""Offline/live numerical information-probe checks, ZERO external model calls."""

import itertools
from fractions import Fraction as Q
from math import comb

import numpy as np
import torch

from .count_source import CountSource
from .noise_features import classify, features, fit_proxy, roles
from .noise_information import bank_geometry
from .test_reductions import pivotal_companion


def run():
    for n in range(1, 8):
        source = CountSource(n)
        observed = {}
        for address in range(source.size):
            mask = tuple(source.decode(address))
            observed[mask] = observed.get(mask, 0) + 1
        expected = {
            tuple(bool(bits & (1 << j)) for j in range(n)): source.block // comb(n, k)
            for bits in range(1, 1 << n)
            if (k := bits.bit_count())
        }
        assert observed == expected
        assert sum(observed.values()) == source.size
    source = CountSource(64)
    assert source.size.bit_length() <= 64 * 65 + 7
    for address in (0, source.block - 1, source.block, source.size - 1):
        assert source.decode(address).sum() == address // source.block + 1
    assert np.array_equal(source.decode(0), source.decode(source.block // 64 - 1))
    for invalid in (-1, source.size):
        try:
            source.decode(invalid)
        except ValueError:
            pass
        else:
            raise AssertionError("out-of-range source accepted")
    text = '["a,\\"b",-2.4e-3,true]'
    role = roles(text, [(i, i + 1) for i in range(len(text))])
    assert role.tolist() == [0, *([1] * 7), 0, *([2] * 7), 0, *([3] * 4), 0]
    mask = np.arange(len(role)) % 2 == 0
    assert len(features(mask, role)) == len(role) + 6
    rng = np.random.default_rng(17)
    x = rng.normal(size=(32, 10))
    x[:, 0] = 1
    y = rng.normal(size=(32, 9))
    beta, centers = fit_proxy(x, y)
    labels = classify(x[:, None], beta, centers)
    assert labels.shape == (32,)
    assert labels[0] == classify(x[0], beta, centers)
    for device in ("cpu", "cuda"):
        logits = torch.arange(35, dtype=torch.float64, device=device).reshape(5, 7) / 10
        bias = torch.zeros(7, dtype=torch.float64, device=device, requires_grad=True)
        targets = torch.tensor((0, 1, 0, 4, 5), device=device)
        actual = logits + bias
        valid = torch.arange(7, device=device) != 6
        actual = actual.masked_fill(~valid, -torch.inf)
        logq = actual.log_softmax(dim=-1)
        loss = -logq.gather(1, targets[:, None]).mean()
        gradient = torch.autograd.grad(loss, bias)[0]
        expected = logq.exp().mean(dim=0).detach()
        expected.scatter_add_(
            0, targets, torch.full((5,), -0.2, dtype=torch.float64, device=device)
        )
        assert torch.allclose(gradient, expected, atol=1e-14, rtol=1e-14)
    keys = (0, 0, 1, 2)
    f = np.array(((1, 0), (0, 1), (1, 1), (-1, 2)))
    joint = np.zeros((4, 4))
    for tape in itertools.permutations(range(4)):
        for j, weight in pivotal_companion(tape, keys).items():
            joint[tape[0], j] += float(weight * Q(1, 24))
    covariance = sum(joint[i, j] * (f[i] @ f[j]) for i in range(4) for j in range(4)) - np.sum(
        f.mean(axis=0) ** 2
    )
    result = bank_geometry(f, np.array(keys))
    assert abs(result["covariance"] - covariance) < 1e-12
    print(
        "PASS exact count/subset source law including aliases, full-V "
        "bias-gradient CPU/CUDA autodiff, JSON roles/proxy dimensions "
        "and independent pivotal bank trace; ZERO external model forwards"
    )


if __name__ == "__main__":
    run()
