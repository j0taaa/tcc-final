# ADR 0006: LLaDA tokenizer raw-byte semantics

- Status: Accepted
- Date: 2026-08-24
- Applies to: T600, token support, byte-lattice construction, witness
  validation, and claims about tokenizer-aware exactness

## Scientific contract

For every supported token sequence, the byte lattice must emit exactly the
bytes defined by the pinned tokenizer interface, in token order and without
losing token IDs or slot provenance. Unsupported controls must be rejected
before solving; they may not disappear as empty arcs. This choice does not
alter the finite-support scope: a top-K result remains `exact_on_support`.

## Pinned interface

The first model adapter targets `GSAI-ML/LLaDA-8B-Instruct` because it is the
model used by the pinned EPIC LLaDA baseline. The tokenizer revision is the
immutable commit:

```text
08b83a6feb34df1a6011b80c3c00c7563e963b07
```

The audit hashes the three loaded tokenizer files and records the exact
Transformers, Tokenizers, Hugging Face Hub, and Python versions in
`docs/evidence/t600-llada-tokenizer-audit.json`. No model weights are needed.

At that revision the tokenizer is a fast BPE tokenizer with an NFC normalizer,
a GPT-2-style ByteLevel pre-tokenizer/decoder, `byte_fallback=false`, a base
vocabulary of 126,080 tokens, and 269 added tokens. All 126,080 base pieces are
non-empty strings over the 256-character ByteLevel alphabet.

## Chosen mapping

Let `u(b)` be the standard GPT-2 ByteLevel bijection from a raw byte `b` to a
Unicode code point used inside BPE vocabulary strings. For ordinary token ID
`t` with vocabulary piece `p_t = c_1 ... c_m`, define:

```text
emit(t) = u^-1(c_1) ... u^-1(c_m)
detokenize_bytes(t_1 ... t_n) = emit(t_1) ... emit(t_n)
```

The lattice will use this compositional **raw-byte** interface. The mapping is
implemented without a Transformers dependency in
`src/mwpc_exact/tokenizer_bytes.py`. The audit applies it to every base token;
there are no unknown characters or empty emissions, and one-token emissions
cover all 256 byte values.

This is the byte sequence accumulated by the ByteLevel decoder before Unicode
rendering. The official Tokenizers implementation documents ByteLevel as the
reversal of its byte-to-Unicode mapping, and its source concatenates those
bytes before applying lossy UTF-8 conversion:

- <https://huggingface.co/docs/tokenizers/api/decoders>
- <https://github.com/huggingface/tokenizers/blob/main/tokenizers/src/pre_tokenizers/byte_level.rs>
- pinned tokenizer artifact:
  <https://huggingface.co/GSAI-ML/LLaDA-8B-Instruct/blob/08b83a6feb34df1a6011b80c3c00c7563e963b07/tokenizer.json>

## Why `decode([id])` is not the mapping

`PreTrainedTokenizerFast.decode` returns Unicode, not the pre-rendering raw
bytes. Its ByteLevel decoder concatenates token fragments and then performs a
lossy UTF-8 conversion, so rendering can depend on adjacent IDs. The pinned
tokenizer provides a minimal deterministic counterexample:

```text
IDs                         [47681, 102]
pieces                      ["ðŁĳ", "©"]
raw bytes                   f0 9f 91 a9
decode([47681, 102])         "👩"
decode([47681])+decode([102]) "��"
```

Consequently, code must never construct emissions with singleton calls to
`decode`. The audit also checks 20,000 seeded random base-token sequences and
curated ASCII, whitespace, NFC/NFD Unicode, emoji/joiner, and raw-byte cases.
For valid UTF-8 raw streams, full Unicode decode matches strict UTF-8 decoding;
for all audited streams, it matches lossy rendering of the concatenated raw
bytes. Unicode rendering itself is outside the lattice contract. A consumer
that requires Unicode text must validate or render the complete witness only
after the byte-level grammar check.

## Unsupported token IDs

Only base IDs `0..126079` are ordinary grammar-emitting tokens. Every added ID
`126080..126348` is explicitly unsupported by the ordinary byte adapter. At
the pinned revision these IDs are:

- 126080 `<|startoftext|>`;
- 126081 `<|endoftext|>` (both EOS and PAD in the high-level configuration);
- 126082 `[CLS]`;
- 126083 `[gMASK]`;
- 126084..126335 `<|reserved_token_0|>` through
  `<|reserved_token_251|>`;
- 126336 `<|mdm_mask|>`;
- 126337..126339 `<|reserved_token_253|>` through
  `<|reserved_token_255|>`;
- 126340 `<role>` and 126341 `</role>`;
- 126342 `<|arithmetic_start|>` and 126343 `<|arithmetic_end|>`;
- 126344 `<|number_start|>` and 126345 `<|number_end|>`;
- 126346 `<|start_header_id|>`, 126347 `<|end_header_id|>`, and
  126348 `<|eot_id|>`.

The evidence artifact records every ID, spelling, backend special flag, and
decode behavior individually. All 269 are marked special by the Tokenizers
backend and disappear under `skip_special_tokens=true`, although only nine are
listed by the high-level `all_special_ids` property. They therefore cannot be
treated as ordinary literal grammar bytes. T700 will define EOS/PAD slot
semantics explicitly; this ADR does not silently give EOS or PAD an emission.
Generic empty pieces and characters outside the ByteLevel alphabet are also
rejected at adapter construction.

## Alternatives considered

- Concatenating `tokenizer.decode([id])` was rejected by the byte-fragment
  counterexample above.
- A stateful transducer reproducing lossy UTF-8 rendering was not selected for
  the required byte-grammar path. It would change invalid raw bytes into the
  UTF-8 encoding of U+FFFD and require state across token arcs, while the byte
  CFG is intentionally defined over the reversible raw ByteLevel stream.
- Choosing another model was unnecessary because the pinned LLaDA base
  vocabulary has a complete, non-empty compositional raw-byte mapping.

## Executable evidence

The dependency-free regression tests are
`tests/exact_commit/test_tokenizer_bytes.py`. The live, revision-pinned audit is
configured by `configs/exact_commit/t600_llada_tokenizer.toml` and run with:

```bash
HF_HOME=.cache/huggingface \
  python scripts/exact_commit/audit_t600_llada_tokenizer.py
```

Use `--local-files-only` after the exact snapshot has been cached. The script
fails on a changed class, vocabulary sizes, backend type, missing byte value,
malformed added-token range, empty/unknown base piece, or decode mismatch.
