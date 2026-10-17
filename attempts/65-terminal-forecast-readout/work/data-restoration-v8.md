# Reconstruct every original capture file, without a model or GPU

The immutable packet root is `docs/artifacts/raw/a65-masked-resource-v8`.
Its manifest describes129 full response-head bit packets,8 final snapshot
packets,137 RNG files and5 metadata files. Storage uses classical delta-XOR/
bitshuffle in independent blocks of four; no precision is discarded. The
captured source is still04c8cf9/run3fbb952. Storage21b8a9d and restoration
540c988 are later tools, not producers of the neural observations.

From the repository root, with NumPy2.4.6 and the zlib version recorded in
`evidence/v8/restoration-origin.json`:

```sh
.venv/bin/python attempts/65-terminal-forecast-readout/work/restore_capture.py \
  --packets docs/artifacts/raw/a65-masked-resource-v8 \
  --output /tmp/a65-restored-new
```

The destination must not exist. This recreates original NPZ bytes, checks
every ORIGINAL file SHA256, copies RNG/metadata unchanged and refuses any
mismatch. Exact compressed-file byte reproducibility requires the recorded
NumPy/zlib serialization versions; the underlying lossless BF16 arrays are
retained in the packets independently of a neural runtime.

Observed standalone restoration exits0 and validates ALL279 original files,
2,023,497,815 bytes, with no neural forward. Output in `evidence/v8/restore.log`.
Original temporary capture remains untouched. The encoded package's280 files
(including its manifest) and all137 RNG metadata files are tracked; these
`.pt` files contain RNG state, not model weights, and were force-added through
the generic checkpoint ignore rule. No model/tokenizer weight cache is bundled.

Versioned evidence keeps the small metadata/source in its normal archive and
the independent blocks in separate `heads-00.zip`...`heads-32.zip` supplements.
To restore a standalone evidence release, extract all supplements with their
original `docs/artifacts/raw/...` paths, the packet manifest/metadata, and the
later storage/restoration scripts from the evidence archive. Original scientific
source.zip intentionally reflects the pre-head producer and predates these
post-capture integrity tools. Archive integrity does not prove useful quality,
priority or the positive scientific objective.
