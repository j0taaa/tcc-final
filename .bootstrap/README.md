# Content-addressed bootstrap source

The full agent-ready source tree is reconstructed from the checked-in
`chunk-*.b64` files. The decoded ZIP must match the SHA-256 recorded in
`source-template.sha256` before any file is copied.

The repository is now fully expanded. Verify the retained recovery archive
without changing the working tree:

```bash
python scripts/materialize.py --verify-only
```

The script verifies the decoded archive, rejects unsafe archive paths, and
does not overwrite an expanded workspace by default. Restoring the historical
snapshot is destructive to newer parent-side files and therefore requires the
explicit `--force` option. It never touches `.git` or the pinned EPIC
submodule.

The local payload replaces the original remote snapshot at
`j0taaa/tcc@2ae9fe6a888d0e97f5921810c8effa4c7024ca30`, whose fourth Base64 chunk
was truncated by 174 characters. Keeping the repaired payload local makes
fresh materialization deterministic and independent of network availability.
