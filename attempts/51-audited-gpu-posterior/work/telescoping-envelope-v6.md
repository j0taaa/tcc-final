# V6 — local count factors instead of a second max-ratio pass

2026-10-16. Written BEFORE code/timings. Same target, consumer and all eight
README obligations; this is a CLASSICAL potential/envelope specialization of
rejection/positive messages, not a claimed new sampling theorem. It refines V1's
implementation plan: avoid an additional max-product graph pass by a possibly
looser inexpensive bound. Strong V4 interval control remains mandatory.

## General potential identity

For each layer p choose a positive finite potential h[p,s] at EVERY state and
positive common scale S[p]. Accepting leaves have h[n,s]=1. These may come from
untrusted fast approximate backward messages, or V3's upper messages; numerical
closeness is not a correctness premise. Nonaccepting outcomes have target weight0.
Let original-ID blocks partition each arc's labels. Obtain directed upper block
masses B[p,b]>=sum_(t in b) w[p,t], directed upper edge masses E[p,e]>=sum_b B[p,b],
and token upper values f[p,t]>=w[p,t]. If block masses are computed by summing f,
these relations hold by upward nonnegative arithmetic. Aliases remain outcomes.

Take ticket grid D=2^40 and H=2^64. Install POSITIVE integer counts satisfying:

 a_token(t) >= D*f[p,t]/B[p,b],
 a_block(b) >= D*B[p,b]/E[p,e],
 a_edge(e) >= D*E[p,e]*h[p+1,dst(e)]/(S[p]*h[p,s]).

Ceiling an UPWARD evaluated RHS and taking max(1,...) is sufficient. Check each
categorical total A=sum a <=2^41 BEFORE drawing. Denominator0, bad conversion,
overflow or a violated cap is REFUSE, never deleting a positive original event.
Singleton categories still have their constructed counts for bounding purposes,
even though their actual law is1 and no source word is needed.

Counts need not sum to D. The proposal uses V1's executed multiply-high integer
CDF, with exact probabilities q_i=b_i/H and b_i determined by endpoint ceilings.
For a category with total A, set

 k(category) = (A/D)/(1-A/H).

Its actual q_i >= (a_i/A)*(1-A/H), hence

 w[p,t]/q_token <= B[p,b]*k_token,
 B[p,b]/q_block <= E[p,e]*k_block,
 E[p,e]*h_child/q_edge <= S[p]*h_parent*k_edge.

Combining gives w[p,t]/(q_edge*q_block*q_token) <=
S[p]*h_parent/h_child * k_edge*k_block*k_token.
Along a valid word, potentials TELECOPE to h[0,root]/h[n,accept]=h_root.
Let gamma[p,phase] be the maximum k over ALL categories of that layer/phase.
Then an admissible global rejection envelope is

 M = h_root * product_p S[p] * product_(p,phase) gamma[p,phase].

Every original valid positive-weight word has a unique trace and is covered.
Therefore the SAME exact scalar acceptance W/(M*Q) and all V1 rate/FAIL/censoring
statements hold. Gamma can instead use a coarser UPWARD max(A)/D times the
universal g>=1/(1-2^-23). Ceilings, products, maxima and scalar reconstruction
must be genuinely conservative. No numerical inspection may lower M heuristically.
The exact word Q STILL uses finite preimages, not the ideal counts ratio.

This proof is a standard importance-potential telescoping argument; the specific
engineering opportunity is to obtain global count maxima while materializing
proposal CDFs, avoiding V1's additional max-ratio backward DP. It is not an
impossibility bound or unconditional speed advantage over certified intervals.

## Practical potentials and numerical trust

V3 upper beta values and their SAVED common scales are already suitable. Zero
values may be replaced by a positive minimum dyadic before making proposals;
this can make totals too large and force refusal. It cannot justify dropping
support. A positive potential is required on all positive target traces.
Use leaf potential1 for accepts. Arbitrary bad approximations may produce a
poor admission M/L; directed lower mass L is still required to certify useful
acceptance. A word-level correction is charged EVERY trial, unlike interval
control's observed zero exact fallbacks on the240 old-head draws.

Products of TWO finite binary32 potentials/scales are exactly representable in
binary64: at most48 significand bits and exponent range within binary64. Thus
S[p]*h_parent and E[p,e]*h_child can be formed exactly in binary64 (compiler must
preserve that operation). Directed-up binary64 division and multiplication by
D then upward integer conversion implement the count premise without a log/exp
error bound. Actual instruction/compiler tests and count cap checks are required.
This is an explicit numerical implementation contract, not ideal-real native
Torch multinomial equivalence or formal software verification.

## Comparative consequence and next test

Preparation adds directed count construction/segmented integer prefixes and
per-layer total maxima to shared class/inside work, rather than another max DP.
The GPU walk uses integer CDF searches and records selected endpoints; one exact
O(n) scalar acceptance follows. The classical interval control instead performs
directed CDF scans and only rare exact fallback. Either may win; ordinary FP64
and published/native kernels remain practical alternatives with their declared
laws. A large model forward may erase even a decoder-only advantage.

First rational oracle: construct counts from exact rational upper masses and
positive scaled potentials, enumerate EVERY original-word W/Q, verify M dominates
and accepted laws match target, including variable EOT/PAD/aliases/fixed IDs.
Include bad potentials/cap refusal and compare M to the tighter V1 max-product
bound. No extensive GPU implementation or performance protocol follows just from
this written classical lemma. Specific useful systems novelty and user goal
remain open; no new neural head, own theorem priority or publication claim.
