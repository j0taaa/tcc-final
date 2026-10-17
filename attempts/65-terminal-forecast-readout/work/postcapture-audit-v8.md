# Post-capture integrity audit; no new heads or changed decision

2026-10-17. Producer04c8cf9 at running commit3fbb952 finished with observed
exit0: ALL8 valid originals,129/129 real forwards, only1/8 satisfies the
FROZEN N7>=0.005 magnitude screen (required4). Application is NEGATIVE; no
quality labels/campaign, another schedule/head/model or relaxed threshold.

Before writing/running the audit, define these checks of retained data:
all129 response-head packets and8 terminal score packets; all prompt IDs,
64->4 masked progression in steps of4, preserved previously committed IDs;
final float32 snapshot is EXACT BF16 expansion of its last archived head;
all original IDs equal final proposal and preserve pins. Recompute raw JSON
numbers from independently inverted byte-BPE vocabulary and stdlib Fraction
parsing, not just the recorded readout values. Recompute all24 means and
rendering sums exactly, every helper cost, finite stats and N7 binomial
formula independently. Hash every output file. No neural model/tokenizer
library or gold/outcome fields are needed. Keep the original records untouched.

The original full-head-bit capture is about2GB. To avoid duplicating opaque
compressed data needlessly, a separate lossless storage codec MAY delta-XOR
successive BF16 heads in small independent blocks and bitshuffle those exact
uint16s before ordinary ZIP compression. This is classical archive coding,
not a scientific contribution or changed experimental producer. Freeze codec
before use; verify EACH decoded head, IDs and reconstructed ORIGINAL NPZ byte
SHA256 against the untouched capture. Keep RNG and metadata files byte exact.
Roundtrip failure must preserve raw files and refuse compact promotion. Raw
temporary capture stays intact until all independent checks/archive validation.
