"""CPU correctness prototype of the grouped indirect linear-LSE interface.

Ordinary checkpoint/recomputation and CCE are direct antecedents. No GPU
kernel, optimized implementation, memory measurement or speed claim here.
"""


def grouped_head(hidden, classifier, bias, targets, mapping, panel=32):
    import torch

    if panel < 1 or sorted(set(mapping)) != list(range(max(mapping) + 1)):
        raise ValueError("positive panel and contiguous nonempty class IDs required")
    members = tuple(
        torch.tensor([v for v, c in enumerate(mapping) if c == cls], device=hidden.device)
        for cls in range(max(mapping) + 1)
    )

    class GroupedHead(torch.autograd.Function):
        @staticmethod
        def forward(ctx, h, w, b, t):
            columns = []
            for ids in members:
                accum = h.new_full((len(h),), -torch.inf)
                for begin in range(0, len(ids), panel):
                    subset = ids[begin : begin + panel]
                    logits = h @ w[subset].T + b[subset]
                    accum = torch.logaddexp(accum, torch.logsumexp(logits, dim=1))
                columns.append(accum)
            z = torch.stack(columns, dim=1)
            target_logits = (h * w[t]).sum(dim=1) + b[t]
            ctx.save_for_backward(h, w, b, t, z)
            return z, target_logits

        @staticmethod
        def backward(ctx, dz, dt):
            h, w, b, targets, z = ctx.saved_tensors
            dh, dw, db = torch.zeros_like(h), torch.zeros_like(w), torch.zeros_like(b)
            for cls, ids in enumerate(members):
                for begin in range(0, len(ids), panel):
                    subset = ids[begin : begin + panel]
                    logits = h @ w[subset].T + b[subset]
                    norm = z[:, cls, None]
                    norm = torch.where(torch.isfinite(norm), norm, torch.zeros_like(norm))
                    g = dz[:, cls, None] * torch.exp(logits - norm)
                    g += dt[:, None] * (targets[:, None] == subset[None, :])
                    dh += g @ w[subset]
                    dw.index_add_(0, subset, g.T @ h)
                    db.index_add_(0, subset, g.sum(dim=0))
            return dh, dw, db, None

    return GroupedHead.apply(hidden, classifier, bias, targets)
