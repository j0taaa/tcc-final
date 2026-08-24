# ADR 0007: EOS/PAD and finite-slot semantics

- Status: Accepted
- Date: 2026-08-24
- Applies to: T700--T704, finite-support construction, token/byte lattices,
  exact-commit certificates, independent validation, and the LLaDA exact
  strategy

## Scientific contract

Every represented completion has two simultaneous lengths: a fixed number of
physical token slots and a grammar-visible byte sequence ending at a precisely
defined content boundary. EOS and PAD consume physical slots but emit no CFG
terminal. An `OPTIMAL` certificate must retain every physical token ID and
must be independently interpretable without relying on tokenizer decoding or
parser internals. Top-K or otherwise pruned results remain
`exact_on_support`.

## Pinned LLaDA observations

The first production profile is pinned to
`GSAI-ML/LLaDA-8B-Instruct` tokenizer revision
`08b83a6feb34df1a6011b80c3c00c7563e963b07`, as established by ADR 0006 and
`docs/evidence/t600-llada-tokenizer-audit.json`.

At that revision:

- `eos_token` and `pad_token` are both `<|endoftext|>`, token ID `126081`;
- padding is on the right;
- `<|eot_id|>`, token ID `126348`, is an added backend-special token used by
  the chat template, but it is not the configured high-level EOS token;
- `<|mdm_mask|>`, token ID `126336`, is the diffusion mask and is neither
  content nor a completed witness token.

The preserved EPIC LLaDA decoder allocates exactly `gen_length` generated
slots. It maps both `<|endoftext|>` and `<|eot_id|>` to its EOS sentinel,
requires that sentinel for its successful-completion flag, and fills the
remaining generated suffix when one is committed. These observations explain
the compatibility choices below; the vendor baseline remains read-only.

## Policy object and task profiles

EOS behavior must be an explicit policy input. There is no inferred default.
The policy records an EOS mode, the accepted termination IDs, and the canonical
PAD ID. The pinned LLaDA special-token profile is:

```text
termination_token_ids = (126081, 126348)
pad_token_id = 126081
```

The following task profiles are the complete allowed set for the required
implementation:

| Task/profile | EOS mode | Meaning |
| --- | --- | --- |
| T600--T606 ordinary-token fixtures and campaigns | `ABSENT` | EOS, EOT, PAD, mask, and all other added controls are outside support. Every one of the `n` slots emits ordinary-token bytes. This preserves the completed M6 claim unchanged. |
| LLaDA exact constrained completion for C++, JSON Schema, and SMILES | `REQUIRED` | Exactly one first termination event must occur within the `n` generated slots. The grammar-visible content before it must be valid, and only canonical PAD follows it. |
| Explicit M7 optional-EOS fixtures/campaigns | `OPTIONAL` | Either the same terminated form is used or no terminator occurs and all `n` slots are content. This profile exists to test the permitted no-EOS case and must not be selected implicitly for production. |

Unconstrained, serial, and EPIC execution are not redefined by this policy.
They remain separate baselines. Any future model or task must declare a new
versioned profile instead of inheriting the LLaDA IDs by accident.

## Slot automaton

T701 must compose token choices with two states. A path starts in
`BEFORE_EOS`:

- an ordinary token remains in `BEFORE_EOS` and emits its ADR-0006 raw bytes;
- either termination ID consumes one slot, emits no grammar symbol, and moves
  to `AFTER_EOS`;
- PAD is not a separate legal role before termination. Because LLaDA aliases
  EOS and PAD to ID `126081`, that ID in `BEFORE_EOS` is always interpreted as
  the termination event;
- the mask ID and every other unsupported control remain illegal.

In `AFTER_EOS`, only canonical PAD ID `126081` is legal. It consumes one slot,
emits no grammar symbol, and remains in `AFTER_EOS`. In particular, ordinary
tokens and `<|eot_id|>` are illegal after termination. The same numeric ID
`126081` is therefore unambiguous: its role is EOS on the transition out of
`BEFORE_EOS` and PAD on later transitions in `AFTER_EOS`.

For `REQUIRED`, only `AFTER_EOS` is accepting at physical boundary `n`. For
`OPTIONAL`, both states are accepting there. For `ABSENT`, special transitions
do not exist and `BEFORE_EOS` is accepting after exactly `n` ordinary choices.

An EOS in slot zero is legal only when the grammar accepts the empty byte
string. An EOS in the final slot is legal and needs no following PAD. A fixed
ordinary token after a fixed/selected terminator makes that path invalid; fixed
positions never yield to EOS normalization.

## Physical and effective lengths

Let the generated canvas have physical slots `0 .. n-1`, and let `e` be the
zero-based position of its first termination token.

- Every complete witness contains exactly `n` token IDs, regardless of EOS.
- If EOS is present, `content_endpoint_slot = e`, the effective content token
  IDs are `witness_token_ids[0:e]`, and slots `e+1 .. n-1` are PAD.
- If EOS is absent under `OPTIONAL` or `ABSENT`,
  `content_endpoint_slot = n` and all witness token IDs are content.
- The effective terminal sequence is the concatenation of the ordinary-token
  raw-byte emissions before `content_endpoint_slot`. Its byte length is not
  generally equal to the content token count because tokens may emit multiple
  bytes.
- EOS and PAD contribute no terminal labels, but their token choices retain
  their own weights and matched proposal IDs. They cannot inherit or erase a
  neighboring token's provenance.

Thus a certificate must report the full physical token witness, the EOS
position or absence, `content_endpoint_slot`, and the effective terminal
labels. Independent validation recomputes all four from the policy and must
reject any disagreement.

## Support, infeasibility, and baseline compatibility

Termination and PAD choices needed by a configured profile must be added to
masked support rows explicitly and listed in exactness metadata. This does not
turn top-K into full-vocabulary exactness. If a valid `REQUIRED` completion is
absent from represented support, the result is `INFEASIBLE_ON_SUPPORT`; it is
never converted to `TIMEOUT` or a global infeasibility claim.

The exact strategy canonicalizes every post-termination slot to PAD ID
`126081`, including when `<|eot_id|>` caused termination. EPIC's existing
suffix-fill implementation is left unchanged and may repeat its selected
terminator ID. Comparisons decode content only through the first terminator;
they do not claim identical special-token suffixes across strategies.

## Alternatives considered

- Stopping the graph path at EOS was rejected because it loses physical slots,
  fixed-position checks, and proposal provenance.
- Letting all tokenizer-special tokens disappear under
  `skip_special_tokens=true` was rejected because it would permit normal tokens
  after EOS and make token roles unreconstructible.
- Treating EOS as optional for every task was rejected because EPIC's LLaDA
  constrained-completion success condition requires termination.
- Excluding `<|eot_id|>` was rejected because the pinned chat interface uses it
  and the preserved decoder already recognizes it as termination.
- Repeating `<|eot_id|>` as padding in exact certificates was rejected because
  it is not the tokenizer's PAD ID. Compatibility is handled at the content
  boundary rather than by weakening the exact witness contract.

## Executable evidence and next implementation step

The pinned tokenizer evidence is checked offline by
`tests/exact_commit/test_t600_tokenizer_audit_evidence.py`. The relevant
read-only baseline paths are
`vendor/EPIC-Decoding/constrained_diffusion/eval/dllm/models/llada/model.py`
and `generate_constrained.py` beside it.

T701 must implement the automaton above as a separate composition step. It may
not silently change the completed one-ordinary-token-per-slot M6 builder, and
T702 must independently recompute the state sequence and content boundary.
