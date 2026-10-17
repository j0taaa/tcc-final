# Copyright (C) 2024 Apple Inc. All Rights Reserved.
# FP32/LSE-only host adaptation of the pinned CCE launch wrapper. Native
# kernels are unmodified. See CCE-OUT-LICENSE and cce-out-origin-v9.json.
"""Competent output-buffer control; single-stream sequential use only."""

import torch
import triton


def forward_lse(h, w, b):
    from cut_cross_entropy.cce_lse_forward import cce_lse_forward_kernel

    return cce_lse_forward_kernel(
        e=h, c=w, bias=b, valids=None, softcap=None, targets=None, shift=0, return_logit_avg=False
    ).lse


def buffers(h, w):
    n, d = h.shape
    return (
        h.new_zeros((n,)),
        torch.zeros((triton.cdiv(n, 128), triton.cdiv(d, 64)), device=h.device, dtype=torch.int32),
        torch.zeros(
            (triton.cdiv(len(w), 128), triton.cdiv(d, 64)), device=h.device, dtype=torch.int32
        ),
    )


def backward_into(h, w, b, lse, delta, dh, dw, db, work):
    from cut_cross_entropy.cce_backward import _cce_backward_kernel
    from cut_cross_entropy.tl_utils import b_bin_fn

    zero, de_locks, dc_locks = work
    n = h.shape[0]

    def grid(meta):
        return (triton.cdiv(n, meta["BLOCK_B"]) * triton.cdiv(len(w), meta["BLOCK_V"]),)

    _cce_backward_kernel[grid](
        h,
        w,
        b,
        lse,
        zero,
        1.0,
        delta,
        None,
        None,
        None,
        None,
        dh,
        None,
        de_locks,
        dw,
        None,
        dc_locks,
        db,
        n,
        h.shape[1],
        len(w),
        len(h),
        *de_locks.size(),
        *dc_locks.size(),
        h.stride(0),
        h.stride(1),
        w.stride(0),
        w.stride(1),
        b.stride(0),
        1,
        None,
        shift=0,
        B_BIN=b_bin_fn(n),
        FILTER_E_GRAD=False,
        FILTER_C_GRAD=False,
    )
