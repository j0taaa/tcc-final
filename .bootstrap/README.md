# Immutable bootstrap source

The full agent-ready source tree is reconstructed from six base64 chunks stored at the immutable public commit:

`j0taaa/tcc@2ae9fe6a888d0e97f5921810c8effa4c7024ca30`

Run:

```bash
python scripts/materialize.py
```

The script downloads the chunks, verifies the decoded archive with `.bootstrap/source-template.sha256`, rejects unsafe archive paths and expands the workspace without touching `.git` or the pinned EPIC submodule.
