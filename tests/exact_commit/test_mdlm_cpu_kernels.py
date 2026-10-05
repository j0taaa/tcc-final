import pytest

torch = pytest.importorskip("torch")
from scripts.exact_commit.mdlm_cpu import attention, rearrange, rotary  # noqa: E402


def test_cpu_rotary_matches_independent_complex_rotation_and_preserves_values():
    torch.manual_seed(300500)
    qkv = torch.randn(2, 5, 3, 2, 8, dtype=torch.float64)
    angles = torch.randn(5, 4, dtype=torch.float64)
    out = rotary(qkv, angles.cos(), angles.sin())
    for b in range(2):
        for s in range(5):
            for component in (0, 1):
                for h in range(2):
                    z = torch.complex(qkv[b, s, component, h, :4], qkv[b, s, component, h, 4:])
                    expected = z * torch.exp(1j * angles[s])
                    assert torch.allclose(
                        out[b, s, component, h, :4], expected.real, atol=1e-12, rtol=0
                    )
                    assert torch.allclose(
                        out[b, s, component, h, 4:], expected.imag, atol=1e-12, rtol=0
                    )
    assert torch.equal(out[:, :, 2], qkv[:, :, 2])


def test_cpu_attention_matches_manual_segmented_softmax_without_cross_sequence_leakage():
    torch.manual_seed(300501)
    qkv = torch.randn(7, 3, 2, 8, dtype=torch.float64)
    out = attention(qkv, torch.tensor([0, 3, 7]), 4, 0.0, causal=False)
    for lo, hi in ((0, 3), (3, 7)):
        for h in range(2):
            q, k, v = (qkv[lo:hi, i, h] for i in range(3))
            expected = ((q @ k.T) / (8**0.5)).softmax(-1) @ v
            assert torch.allclose(out[lo:hi, h], expected, atol=1e-12, rtol=0)
    packed = torch.arange(2 * 3 * 3 * 2 * 4).reshape(2, 3, 24)
    rearranged = rearrange(packed, "b s (three h d) -> b s three h d", three=3, h=2)
    assert torch.equal(rearranged.reshape(2, 3, 24), packed)
    flat = rearrange(rearranged, "b s ... -> (b s) ...")
    restored = rearrange(flat[:, :, 0], "(b s) h d -> b s (h d)", b=2)
    assert restored.shape == (2, 3, 12)
