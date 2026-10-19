# EPIC provenance

- Upstream: `https://github.com/hyundong98/EPIC-Decoding`
- Captured commit: `5b1b31098f34ed3691d2a9f4aae14fdf5839d072` (2026-06-02).
- Local production snapshot: `vendor/EPIC-Decoding`.
- The user requested deletion of every test on 2026-10-05. The submodule was
  converted into a reproducible versioned snapshot; 12 test files and ten
  `cfg(test)`-only source sections were removed. Production prefixes/declarations
  remain unchanged; no decoder/parser algorithm was edited.
- `.upstream-manifest.json` contains the complete original and retained file
  SHA-256 inventories, deleted paths and each test-only source removal.
- Upstream MIT and third-party notices remain byte-for-byte unchanged.

```bash
./scripts/verify_upstream.sh
```

The verifier checks every retained file against that versioned manifest. Original
upstream source/tests can be recovered through the pre-cleanup source commit and
its original submodule. Do not edit the retained baseline production source.
