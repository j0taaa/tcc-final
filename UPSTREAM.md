# Upstream provenance

## EPIC baseline

- Repository: `https://github.com/hyundong98/EPIC-Decoding`
- Pinned commit: `5b1b31098f34ed3691d2a9f4aae14fdf5839d072`
- Commit date: 2026-06-02
- Paper: *EPIC: Efficient and Parallel Inference under CFG Constraints for Diffusion Language Models*, arXiv:2606.00722
- Local path: `vendor/EPIC-Decoding`
- Policy: read-only baseline; all new implementation lives outside the submodule.

Verify after cloning:

```bash
test "$(git -C vendor/EPIC-Decoding rev-parse HEAD)" = \
  "5b1b31098f34ed3691d2a9f4aae14fdf5839d072"
```

Do not advance the submodule without a documented literature and regression review. Preserve upstream licenses and notices.
