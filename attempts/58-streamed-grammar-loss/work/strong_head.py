"""Classical physically sorted/grouped controls with direct gradient assembly.

CCE is used unmodified through direct LSE adjoints. This is a comparator,
not a new differentiation algorithm or a measured performance result.
"""

import torch


def segmented_lse(logits, lengths):
    sizes = lengths[None, :].expand(len(logits), -1)
    maximum = torch.segment_reduce(logits, "max", lengths=sizes, axis=1)
    safe = torch.where(torch.isfinite(maximum), maximum, torch.zeros_like(maximum))
    expand = torch.repeat_interleave(safe, lengths, dim=1, output_size=logits.shape[1])
    total = torch.segment_reduce(torch.exp(logits - expand), "sum", lengths=sizes, axis=1)
    return safe + total.log()


class SortedHeadPlan:
    def __init__(self, mapping, device="cpu", threshold=32, panel=2048, backend="checkpoint"):
        if not mapping or sorted(set(mapping)) != list(range(max(mapping) + 1)) or panel < 1:
            raise ValueError("nonempty contiguous classes and positive panel required")
        if backend not in ("checkpoint", "CCE", "CCE_out", "dense"):
            raise ValueError("unknown control backend")
        self.backend, self.panel = backend, panel
        members = [
            [v for v, c in enumerate(mapping) if c == cls] for cls in range(max(mapping) + 1)
        ]
        order = sorted(range(len(members)), key=lambda c: (len(members[c]) > threshold, c))
        ids = [v for cls in order for v in members[cls]]
        self.perm = torch.tensor(ids, device=device)
        self.inv = torch.empty_like(self.perm)
        self.inv[self.perm] = torch.arange(len(ids), device=device)
        self.ranges, offset = [], 0
        for cls in order:
            self.ranges.append((cls, offset, offset + len(members[cls])))
            offset += len(members[cls])
        self.small = [r for r in self.ranges if r[2] - r[1] <= threshold]
        self.large = [r for r in self.ranges if r[2] - r[1] > threshold]
        self.small_count = sum(hi - lo for _, lo, hi in self.small)
        self.small_classes = torch.tensor(
            [c for c, _, _ in self.small], device=device, dtype=torch.long
        )
        self.small_lengths = torch.tensor(
            [hi - lo for _, lo, hi in self.small], device=device, dtype=torch.long
        )
        self.small_member_class = torch.repeat_interleave(self.small_classes, self.small_lengths)
        self.all_lengths = torch.tensor([hi - lo for _, lo, hi in self.ranges], device=device)
        self.all_classes = torch.tensor([c for c, _, _ in self.ranges], device=device)
        self.all_member_class = torch.repeat_interleave(self.all_classes, self.all_lengths)
        self.class_count = len(members)
        # None preserves dynamic checks; a declared immutable bias support
        # can instead be prepared once alongside the other metadata.
        self.blocked_classes = None
        self.out_work = {}

    def blocked(self, cls, bias, lo, hi):
        if self.blocked_classes is not None:
            return cls in self.blocked_classes
        return bool(torch.isneginf(bias[lo:hi]).all())

    def __call__(self, hidden, physical_weight, physical_bias, original_targets):
        return _SortedHead.apply(hidden, physical_weight, physical_bias, original_targets, self)


class _SortedHead(torch.autograd.Function):
    @staticmethod
    def forward(ctx, h, w, b, targets, plan):
        z = h.new_empty((len(h), plan.class_count))
        children = []
        if plan.backend == "dense":
            logits = h @ w.T + b
            grouped = segmented_lse(logits, plan.all_lengths)
            z[:, plan.all_classes] = grouped
        else:
            if plan.small_count:
                logits = h @ w[: plan.small_count].T + b[: plan.small_count]
                z[:, plan.small_classes] = segmented_lse(logits, plan.small_lengths)
            for cls, lo, hi in plan.large:
                if plan.blocked(cls, b, lo, hi):
                    z[:, cls] = -torch.inf
                    children.append(None)
                elif plan.backend == "CCE_out":
                    from .cce_out_v9 import buffers, forward_lse

                    value = forward_lse(h, w[lo:hi], b[lo:hi])
                    key = (len(h), h.shape[1], cls)
                    if key not in plan.out_work:
                        plan.out_work[key] = buffers(h, w[lo:hi])
                    children.append(value)
                    z[:, cls] = value
                elif plan.backend == "CCE":
                    from cut_cross_entropy import linear_cross_entropy

                    # Native reverse contexts see contiguous physical views.
                    # No full-V gather/scatter graph exists for each class.
                    with torch.enable_grad():
                        hh = h.detach().requires_grad_()
                        ww = w[lo:hi].detach().requires_grad_()
                        bb = b[lo:hi].detach().requires_grad_()
                        _, zz = linear_cross_entropy(
                            hh,
                            ww,
                            torch.zeros_like(targets),
                            bias=bb,
                            reduction="none",
                            return_lse=True,
                            filter_eps=None,
                            accum_e_fp32=True,
                            accum_c_fp32=True,
                        )
                    children.append((zz, hh, ww, bb))
                    z[:, cls] = zz.detach()
                else:
                    value = h.new_full((len(h),), -torch.inf)
                    for start in range(lo, hi, plan.panel):
                        stop = min(start + plan.panel, hi)
                        logits = h @ w[start:stop].T + b[start:stop]
                        value = torch.logaddexp(value, torch.logsumexp(logits, 1))
                    z[:, cls] = value
                    children.append(None)
        physical_targets = plan.inv[targets]
        target_logits = (h * w[physical_targets]).sum(1) + b[physical_targets]
        ctx.save_for_backward(h, w, b, physical_targets, z)
        ctx.plan, ctx.children = plan, children
        return z, target_logits

    @staticmethod
    def backward(ctx, dz, dt):
        h, w, b, targets, z = ctx.saved_tensors
        plan = ctx.plan
        dh = torch.zeros_like(h)
        dw = torch.zeros_like(w) if plan.backend == "CCE_out" else torch.empty_like(w)
        db = torch.zeros_like(b) if plan.backend == "CCE_out" else torch.empty_like(b)
        transposed_dz = dz.T.contiguous() if plan.backend.startswith("CCE") else None

        def block(lo, hi, classes):
            logits = h @ w[lo:hi].T + b[lo:hi]
            norm = z[:, classes]
            safe = torch.where(torch.isfinite(norm), norm, torch.zeros_like(norm))
            g = dz[:, classes] * torch.exp(logits - safe)
            dh.add_(g @ w[lo:hi])
            torch.mm(g.T, h, out=dw[lo:hi])
            db[lo:hi].copy_(g.sum(0))

        if plan.backend == "dense":
            block(0, len(w), plan.all_member_class)
        else:
            if plan.small_count:
                block(0, plan.small_count, plan.small_member_class)
            for ordinal, (cls, lo, hi) in enumerate(plan.large):
                if plan.blocked(cls, b, lo, hi):
                    dw[lo:hi].zero_()
                    db[lo:hi].zero_()
                elif plan.backend == "CCE_out":
                    from .cce_out_v9 import backward_into

                    backward_into(
                        h,
                        w[lo:hi],
                        b[lo:hi],
                        ctx.children[ordinal],
                        transposed_dz[cls],
                        dh,
                        dw[lo:hi],
                        db[lo:hi],
                        plan.out_work[(len(h), h.shape[1], cls)],
                    )
                elif plan.backend == "CCE":
                    zz, hh, ww, bb = ctx.children[ordinal]
                    gh, gw, gb = torch.autograd.grad(zz, (hh, ww, bb), transposed_dz[cls])
                    dh.add_(gh)
                    dw[lo:hi].copy_(gw)
                    db[lo:hi].copy_(gb)
                else:
                    for start in range(lo, hi, plan.panel):
                        stop = min(start + plan.panel, hi)
                        cls_for_panel = torch.full(
                            (stop - start,), cls, device=h.device, dtype=torch.long
                        )
                        block(start, stop, cls_for_panel)
        # Target adjoints are added exactly once, regardless of class size.
        dh.add_(dt[:, None] * w[targets])
        dw.index_add_(0, targets, dt[:, None] * h)
        db.index_add_(0, targets, dt)
        return dh, dw, db, None, None
