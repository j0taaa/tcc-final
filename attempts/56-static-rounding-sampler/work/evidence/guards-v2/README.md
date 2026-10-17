# Original-protocol boundary supplement

This separate packet executes the explicit invalid-support and zero-mass
requirements of gpu-preflight-v2.md. The first7-fixture packet is unchanged;
its185 masses/336 replays/4096 prefixes are not relabeled or inflated.

```
.venv-mosaic-native/bin/python -m attempts.56-static-rounding-sampler.work.guard_preflight --output /tmp/a56-guards-v2-first
```

Exit0 output was copied AFTER completion. Eight required boundaries pass:
duplicate original ID, overlapping arcs, invalid target, negative/NaN/above-one
weights, wrong dtype and zero target mass. Zero-mass query bounds are exactly
zero, and the sampler returns no word. This is not a timeout or guessed zero.

The packet also captures arithmetic specializations used by the previous
finite-word law. Its5 PTX files overlap2 files of the initial14, yielding17
UNIQUE preserved modules in the union. The raw additional_ptx_modules field
counts modules in this additional packet, not a disjoint increment of5.
All filenames are exact content hashes and none contains FTZ qualifiers.

No neural input/head/forward, timing, useful-effect or novelty measurement.
The exact executed source SHA256 is in summary.json. The maintained311-test
suite covers the CPU reference separately; these GPU checks are opt-in.
