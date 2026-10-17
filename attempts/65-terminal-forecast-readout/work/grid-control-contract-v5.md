# V5 competent exact-grid semantic moment control, before code/execution

2026-10-17. This refines README1--8 without promoting conditional averaging.
The actual native x-prob grammar has at most101 values per field. A classical
finite-state integer-sum/moment DP is therefore mandatory before real heads,
not a new proposed algorithm or a deliberately unbounded baseline. V4's48
synthetic records remain correctness evidence, not actual forecast variance.

## Same frozen native path kernel, numerical-law boundary explicit

Start from a TerminalSnapshot of the native final temperature0 proposal. On
each free edge e at layer t, weight is the sum of ALL original token masses
allowed on that edge, but the emitted ID is the deterministic within-edge
argmax, with native original-ID tie breaking. On a forced edge its weight is
the binary native allowed indicator and its original pinned ID is emitted.
Preserve accepted-prefix IDs, thinking offset, budget-forced PAD, end-node
coaccessibility and actual final log-marginals. No raw-head substitution or
another marginal call. The ideal arithmetic path law is NOT a theorem about
the exact finite torch.multinomial RNG law. Evaluate that distinction honestly.

The classical control implements direct float64 weighted DP; 'exact-grid'
means no truncation/approximation of numerical values or semantic states, not
exact rational evaluation of floating exponentials. Independent rational toys
will verify semiring algebra; ordinary native comparisons have tolerance5e-5.
No claim that float64 outputs are certified probability intervals.

## Semantic machine and sufficient statistics, written before implementation

The response has a fixed order of ASCII labels under the native JSONBuilder.
Build a deterministic semantic byte parser for exactly the nested object with
that field order, whitespace, probability spellings0/0.d/0.dd/1/1.0/1.00,
EOT then PAD. Model this as a syntax pattern whose K holes are numbers.
The parser's numeric register contains only the current unfinished spelling;
at field completion emit the exact integer x=100*p in[0,100] and its field j.
A token may finish several fields. Original distinct aliases and EOT/PAD are
preserved; tokenizer/control IDs are consumed as indivisible controls.

After each token track (native node, semantic parser state, S), S the SUM of
all completed field integers so far, bounded by100K. Each state carries:

* mass z;
* K first-moment numerators m_j for completed integers;
* total squared-integer numerator q for sum_j x_j^2.

Upon completing field j with value x, update S+=x, m_j+=x*z and q+=x*x*z.
All quantities multiply by the edge weight; merge identical states by summing
their z/m/q. No vector of all101^K completed choices is kept. Partial numbers
have a finite set of native spellings/registers. This is ordinary weighted
automaton composition and expectation semirings, with polynomial bounded
integer sum; the principles are antecedents.

The accepted prefix is run through the same semantic parser once and its
completed values initialize S/m/q. Thinking-offset IDs are ignored. At the
last layer apply native end weights. Total denominator Z includes EVERY native
path, also proposals which do not complete the JSON: compute it in a separate
plain native-node forward DP. Completed semantic states have mass Z_C.

For each terminal sum s>0 contribute m_j/s to unnormalized normalized mean and
q/s^2 to unnormalized second squared norm; s=0 contributes z/K per coordinate
and z/K to squared norm, the common uniform fallback. Divide by Z_C. Then
alpha=Z_C/Z and V=E||X||^2-||E X||^2. Theoretical bounded-helper improvement
is V*(1-E[1/(1+Bin(N,alpha))]); this is an IDEAL frozen-kernel quantity,
not measured whole-model quality. The DP mean removes all ideal terminal
variance; helpers can only be preferable for actual complete cost/rounding-law
or resource reasons. No fabricated advantage versus this control.

## Small prospective preflight only

Before any native/model call freeze source and four checks:

1. Independent literal JSON/syntax tests, aliases/split numbers, pinned prefix,
   wrong field order, too many decimals, missing EOT and illegal PAD.
2. Exact Fraction semiring DP versus independent full path enumeration on
   constructed paths including prefix fields, zero sum, incomplete outcomes
   and multiple fields in ONE token. At least three different rational laws.
3. Conditional per-S moments and final normalized means/variance/alpha agree,
   including a constructed dependent-field law where naive field means fail.
4. DP on ALL fixed six V4 native fixture families, CPU/CUDA, compared to
   independent path enumeration. Both first marginal errors remain<=5e-5;
   alpha/each mean/variance discrepancy<=5e-5. Preserve zero/incomplete cases.

Do not time this as a competitive campaign, load a pretrained tokenizer/model,
read corpus/gold rows, generate new neural heads or alter V4 evidence. Guards:
500000 live semantic DP states/5000000 transitions/600s whole check. A refusal
is not a zero-mass success. Preserve partial results and failed sources.

After correctness, freeze a SEPARATE real resource/variance-necessity protocol
with feasible named backbone, input-only selection and all costs/strong
controls. The original26B/48GB setup does not fit the present unquantized
12GB GPU/16GB host setup. A smaller/quantized substitute is a distinct
application, not reproduction. This control itself is not the positive
scientific contribution or a sufficient reason for a large neural campaign.
