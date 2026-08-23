# Upstream provenance

## EPIC baseline

- Repository: `https://github.com/hyundong98/EPIC-Decoding`
- Default branch at capture time: `main`
- Pinned commit: `5b1b31098f34ed3691d2a9f4aae14fdf5839d072`
- Commit date: 2026-06-02
- Paper: *EPIC: Efficient and Parallel Inference under CFG Constraints for Diffusion Language Models*, arXiv:2606.00722
- Local path: `vendor/EPIC-Decoding`
- Policy: read-only baseline; new implementation lives outside the submodule.
- `LICENSE` SHA-256: `5b23746803b6d9687562034f4e31a8dcddeb47521517c8fcb72c7401f71a9388`
- `THIRD_PARTY_LICENSES.md` SHA-256: `f6456782c874f543c3b8ea703fa07d5fdcf2624b516b5df8f990df48f9753124`

Verify after cloning:

```bash
git submodule update --init --recursive
test "$(git -C vendor/EPIC-Decoding rev-parse HEAD)" = \
  "5b1b31098f34ed3691d2a9f4aae14fdf5839d072"
```

`scripts/verify_upstream.sh` checks the gitlink commit, official URL, configured
default branch, clean submodule status, and both notice-file hashes. Do not
advance the submodule without a separate documented literature and regression
review. Preserve the upstream `LICENSE` and `THIRD_PARTY_LICENSES.md` files
unchanged inside the submodule.
