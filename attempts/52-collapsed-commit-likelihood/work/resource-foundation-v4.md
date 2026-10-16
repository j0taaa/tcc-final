# V4 initial implementation foundation, before pretrained heads

This records classical implementation details and initial correctness checks;
it is not a new mathematical discovery, a competitive timing or resource-screen
completion. The original V4 input/protocol freeze is47b7f6c. No real model has
been evaluated at this stage.

The numeric byte DFA has22 states, including the true EOT/PAD tail. It accepts
the LITERAL ASCII spelling of the sole property key answer; alternate escaped
spellings of the same semantic key are outside this declared language. This
clarifies the exact-key wording BEFORE pretrained output; it is not a claim
of completeness for all JSON-schema-equivalent serializations. The number
itself remains unrestricted JSON sign/integer/fraction/exponent syntax. The
independent parser must retain numeric lexemes instead of overflowing Python
float/Decimal when an exponent is large, and must reject duplicate properties.

Every original ID has an explicit byte emission. The pinned official tokenizer
JSON under Transformers4.57.1/tokenizers0.22.1 agrees on ALL151936 individual
IDs and4096 three-token words with concatenated ByteLevel bytes/UTF8 replacement.
All266 undefined IDs are empty emissions. They remain distinct aliases before
EOT and are forbidden in the PAD-only tail. This is a finite library audit,
not a theorem about every possible tokenizer implementation or a native RNG.

Grouping by effect in all22 states yields38 classes and92 valid state/class
arcs (2944 for32 positions); ALL151936 original IDs remain members. No class
representative supplies its confidence/gate. Two rational/JSON-parser oracles
compare22608 complete small original words, specials, aliases and exact class
sums. The compiler/counting principles are classical.

The NumPy reference propagates a root forward vector with per-layer positive
scaling. Independent suffix vectors give class coefficients; distributing each
coefficient by its ORIGINAL unary weight yields conditional token marginals.
The optional Torch adapter reduces ORIGINAL per-ID factors to class masses,
forms transition matrices and multiplies them in the log semiring with a
balanced tree. Safe log/logsumexp branches exclude structurally impossible
subpaths from undefined gradients. This is standard semiring/parallel inference.
Floating operations are checked approximations, never directed certificates.

For planner alpha_i, beta and anchor logits r, use

    h[i,v]=alpha_i+beta*log(c[i,v])-log(1/100),
    g[i,v]=sigmoid(h[i,v]),   pi=softmax(r).

The V4 initial values alpha=0,beta=1,r=0 reproduce its frozen g=c/(c+1/100)
and uniform anchor. c is the full-V original probability and the pretrained
model is frozen. The adapter differentiates log(Z_a/Z)+log(S_a) with respect
to those planner parameters. This is not a full-backbone parameter update;
V3's rational chain-rule oracle separately covers differentiating confidence.

Initial48 records (16 small cases, NumPy/Torch CPU/Torch CUDA) match the
independent rational law and all three planner readouts. Maximum absolute
log-probability error1.7763568394002505e-15; alpha1.3877787807814457e-16,
beta8.881784197001252e-16, anchor1.1102230246251565e-16. These are tested
toy cases, not a universal numerical bound or a real-neural benefit. Stronger
discarded-token/whole-V checks and the actual resource runner are still pending.

Runtime isolation preserved .venv-live's Torch2.8.0+cu128, Transformers4.52.2
and tokenizers0.21.4. New .venv-a52 appends that runtime's site-packages AFTER
its own packages and installs only Transformers4.57.1/tokenizers0.22.1 locally
with ignore-installed/no-deps. The custom pinned module imports successfully
without constructing a model. The initial host-Python3.12 venv attempt failed
because ensurepip was unavailable; its partial directory is retained under
.cache/a52-runtime-initial-py312. No apt/host or previous environment was changed.

Checkpoint weights may be downloaded/hashed while preparing source, but no
pretrained forward is permitted before actual runner/protocol/runtime freeze.
Every subsequent head/parameter update/timing must be recorded separately.
