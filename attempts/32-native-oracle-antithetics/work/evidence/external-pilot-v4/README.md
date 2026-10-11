# A32/v4 complete negative pilot

Frozen producer: `8fc0999736724b7b28159653503693f95b272c4a`; external input/protocol source was pushed BEFORE evaluation. Source/config SHA256 values, EPIC/model revisions, hardware and load/setup costs are in `results.metadata.json`. The producer files were not changed during this campaign.

1056/1056 preregistered records; 2208/2208 outputs are strict valid numerical JSON. Zero errors/resource refusals/first-trajectory mismatches. 32,716 NEW model forwards. One seed321001 on ALL32 hash-selected official TRAIN questions, BOTH temperatures, all16 configurations and32 deterministic controls.

All EIGHT walk candidate configurations cover20/32 and tie native iid2 while costing more. Mixed stochastic/deterministic covers21/32 for less cost. Thus the frozen negative resource screen triggers: no other development seeds, no test labels/evaluation. This does NOT statistically refute all implementations or seeds.

`audit-v1.json` is derived AFTER measuring by `../../analysis/audit_v4.py`; it independently reparses numbers with Fraction, rejects duplicate keys/NaN/Inf/extra keys, verifies complete tuple identities and every literal first trajectory against iid2, and ADDS `results.io.jsonl` output write/flush costs to full wall/CPU. Full costs include preparation, recovery, cache/transfers, forward/head digests, verification and output. Common model/tokenizer load72.446s is separately excluded for ALL methods. Sidecar research bookkeeping is outside output latency as preregistered.

No heavy tests/build/LP ran during competitive timings; the139-test suite ran AFTER completion. Native finite sampler and recovery remain unmodified. known_p control uses continuous PL approximation explicitly; it is not finite-law exact. JSON number grammar is a regular CFG subclass, not a recursive-generation test.

Pool and walk16 have the SAME law; the22/32 pool_batch16_state at temperature1 in this seed versus20/32 walk is an RNG realization, not an expected-quality law comparison.

## Reproduce the audit

Download the TRAIN file URL pinned in `../../gsm-inputs-v4.json` to a new local file. The analyzer verifies its full SHA256 before opening labels. `selected-train-gold.json` publishes ONLY the32 used rows plus full-source hash/provenance for offline inspection; other train data and test labels are not included. Model weights/caches/full logits are not required to audit the recorded outputs. No measured generation is claimed independently rerun by this output audit.

```bash
.venv/bin/python -m attempts.32-native-oracle-antithetics.work.analysis.audit_v4 --raw attempts/32-native-oracle-antithetics/work/evidence/external-pilot-v4/results.jsonl --train-gold /path/to/pinned/train.jsonl --output /path/to/new/audit.json
```

The analyzer refuses incomplete identities, incorrect original train hash, independent-verifier differences or duplicate rows, and never overwrites its output. `sha256.json` inventories ALL files originally preserved here except itself and this explanatory README. `run.log` retains all progress lines.

## All configurations, including losses

Wall/CPU are campaign totals with amortized deployment setup AND output I/O. Complete raw rows also retain cold first-use costs. No timing is a claim about an uninstrumented fastest EPIC.

|Method|Temperature|Correct/32|Wall seconds|CPU seconds|Forwards|Aux draws|
|---|---:|---:|---:|---:|---:|---:|
|deterministic|0.0|20|168.303|168.005|968|0|
|iid2|0.5|20|211.784|211.482|976|0|
|iid2|1.0|20|215.582|215.273|1008|0|
|iid4|0.5|23|281.827|281.538|983|0|
|iid4|1.0|22|288.271|287.965|1039|0|
|known_p_root|0.5|20|213.140|212.010|976|12|
|known_p_root|1.0|20|217.399|216.272|1008|26|
|known_p_state|0.5|20|214.235|213.092|975|784|
|known_p_state|1.0|20|218.639|217.511|1009|917|
|mixed|0.5|21|203.181|202.884|970|0|
|mixed|1.0|21|207.874|207.582|978|0|
|pool16_root|0.5|20|213.529|212.402|976|448|
|pool16_root|1.0|20|217.085|215.952|1008|448|
|pool16_state|0.5|20|216.177|215.033|976|13426|
|pool16_state|1.0|20|219.658|218.521|1009|12936|
|pool_batch16_root|0.5|20|213.586|212.452|976|448|
|pool_batch16_root|1.0|20|217.062|215.923|1008|448|
|pool_batch16_state|0.5|20|216.661|215.546|976|13426|
|pool_batch16_state|1.0|22|219.482|218.353|1010|12922|
|raw_history|0.5|20|212.876|212.580|975|0|
|raw_history|1.0|20|216.264|215.959|1008|0|
|raw_root|0.5|20|211.892|211.589|976|0|
|raw_root|1.0|20|216.003|215.698|1008|0|
|raw_state|0.5|20|212.407|212.102|975|0|
|raw_state|1.0|20|216.128|215.826|1008|0|
|walk16_root|0.5|20|213.564|212.435|976|200|
|walk16_root|1.0|20|216.903|215.765|1008|143|
|walk16_state|0.5|20|215.142|214.006|976|5358|
|walk16_state|1.0|20|218.819|217.680|1009|4066|
|walk4_root|0.5|20|214.378|212.630|976|35|
|walk4_root|1.0|20|217.309|216.177|1008|28|
|walk4_state|0.5|20|214.539|213.413|976|838|
|walk4_state|1.0|20|218.311|217.185|1008|727|
