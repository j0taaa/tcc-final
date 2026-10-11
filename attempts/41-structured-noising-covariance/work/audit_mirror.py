"""Legitimate ReLU/softmax masked-JSON gradient counterexample, NOT benchmark."""

import math

import torch


def audit():
    devices = ["cpu"] + (["cuda:0"] if torch.cuda.is_available() else [])
    for device in devices:
        for theta in (-4.0, 0.0, 2.0, 9.0):
            parameter = torch.tensor(theta, dtype=torch.float64, device=device, requires_grad=True)
            gradients = []
            for source in range(4):
                masks = torch.tensor([(source >> i) & 1 for i in range(2)], device=device)
                r = masks.sum().to(torch.float64)
                gate = torch.relu(r) - 2 * torch.relu(r - 1) + torch.relu(r - 2)
                logit = -parameter * gate + math.log(3) * (1 - gate)
                loss = r * torch.nn.functional.softplus(-logit)
                (gradient,) = torch.autograd.grad(loss, parameter)
                gradients.append(gradient.item())
            b = 1 / (1 + math.exp(-theta))
            assert all(abs(g - e) < 1e-12 for g, e in zip(gradients, (0, b, b, 0), strict=True))
            mean = sum(gradients) / 4
            iid_variance = sum(((a + b) / 2 - mean) ** 2 for a in gradients for b in gradients) / 16
            mirror_variance = (
                sum(((g + gradients[s ^ 3]) / 2 - mean) ** 2 for s, g in enumerate(gradients)) / 4
            )
            analytic_variance = (
                sum(((g + gradients[s ^ 1]) / 2 - mean) ** 2 for s, g in enumerate(gradients)) / 4
            )
            assert abs(mirror_variance - 2 * iid_variance) < 1e-12
            assert analytic_variance == 0
    print(
        "PASS legitimate CPU/CUDA ReLU/softmax gradients: MIRROR 2x iid2 variance; "
        "analytic control exact and cheaper"
    )


if __name__ == "__main__":
    audit()
