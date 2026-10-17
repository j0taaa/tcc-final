# V7 — Best completion-preserving classical control and all-law cost comparison

2026-10-17. Written AFTER V6, BEFORE new code/execution. The preceding rank
controls are preserved and remain mandatory. This is a stronger control than
V5, not an own invention of common-part coupling or exact short circuiting.

## Eight criteria re-evaluation

README1/2 remain: an opaque iid original-payload source, three ALLOWED keys,
literal first and exact full-six matching pair law. The own claim is the
stopped-work theorem/attaining rule, not elementary coupling. For3/4 the
comparison below predicts a strict all-law source saving versus an entire
specified classical realization class. For5 freeze the operational common-
part control before exhaustive rational checks. For6 all source/preparation/
RNG/storage/downstream work remains charged. For7/8 this does not bound every
classical factory: distributionally valid methods may redistribute mass among
different tape orders. Specific priority/real full-cost usefulness remain open.
No head/weight/update/label/timing/native campaign is triggered.

## 1. The complete conditional-tape control class

For each full ordered six-key tape t, let q_t(j) be the partner-key probability
of uniform minimum-repeat matching, conditional on that ENTIRE tape. q depends
only on the first key and final counts. This is the exact kernel implemented
by V5, before any averaging over the source. For a prefix s write

    a_j(s)=min_(t extends s) q_t(j),  A(s)=sum_j a_j(s).

Every sequential algorithm whose conditional output law is q_t ON EACH TAPE
has cumulative probability of stopping with j by s at most a_j(s). The same
internal stop event occurs under every suffix, and cannot exceed any q_t(j).
Thus its survival probability at s is at least1-A(s). This holds without
knowing P, for every P and independently of how auxiliary random bits are used.

The bound is achieved simultaneously at every prefix. The a_j(s) increase
coordinatewise along a path. Use one independent U~Uniform[0,1). At s append
three intervals of lengths a_j(s)-a_j(parent(s)), in label order, starting at
A(parent(s)). Stop with j if U lies in its interval; otherwise continue.
On reaching s, U necessarily lies in[A(parent(s)),1). Along any full t, total
length assigned to j telescopes to a_j(t)=q_t(j), so the exact q_t law holds.
Every selected class has a nonfirst observed representative: if it did not,
a compatible completion without that class in nonfirst positions has q_t(j)=0.
Return the earliest such original payload; do not clone/rewrite a raw value.

This is ordinary greatest-common-component allocation. It gives a POINTWISE
minimum E_P N within the conditional-tape class for EVERY P, since its survival
bound is attained at every individual prefix. This is not a new general
maximal-coupling theorem, and does not constrain V6's different full-tape
rank kernels or A63's distributional-only rule.

## 2. Written source-cost calculation, to be checked before claims

No positive a exists before depth4. Define q=e2 and r=e3. Grouping all depth4
prefixes by their first-class multiplicity gives

    E A4=(8/5)S3+(3/2)S2^2-(13/5)S4
        =1/2-(2/5)q+(4/5)q^2-(28/5)r.

Depth5 grouping gives

    E A5=(19/5)S4+7*S2*S3-10*S5+14*r*S2+12*q*r
        =4/5-q/5-(2/5)q^2+r/5-8*q*r.

Here A4/A5 are CUMULATIVE stopped masses, not P(N=4/5). Consequently

    C_common(P)=6-E A4-E A5
              =47/10+(3/5)q-(2/5)q^2+(27/5)r+8*q*r.     (1)

At U3 this predicts E A4=67/270,E A5=242/405 and mean835/162.
All grouping identities must be checked against full operational tape/coin
enumeration and independent homogeneous coefficients. A discrepancy is a
failure to preserve, not permission to replace the recorded formula silently.

## 3. A sharp all-law comparative consequence, conditional on those checks

The frozen A63 rule has C_A=4+2q-2q^2+10r-4qr and the SAME final ordered raw
pair law after iid tape averaging. The difference is

    D=C_common-C_A=7/10-(7/5)q+(8/5)q^2-(23/5)r+12qr.

Since0<=q<=1/3, the coefficient -(23/5)+12q is negative. The elementary
inequality q^2>=3r therefore implies

    D >= 7/10-(7/5)q+q^2/15+4q^3.

The derivative of this last polynomial is increasing on[0,1/3] and at1/3
equals-1/45, so it is decreasing there. Hence D>=7/18, attained at U3.
Also(1) increases in both q and r on[0,1/3]x[0,1/27]: partial_q>=1/3>0 and
partial_r>0. Thus C_common<=835/162, again with equality at U3, and

    (C_common-C_A)/C_common >=63/835 =7.5449...%,          (2)

for EVERY allowed P. Equality holds at uniform key masses, so this relative
source-work bound is sharp for this comparison. It is stronger than five
point evaluations and narrower than a guarantee against all competent designs.
The earlier20.576% remains versus always-six only; do not keep the9.56%
headline after adding this stronger classical control.

Finite Wald transfers source-query comparison to complete iid source work of
finite mean, including key/status/failed-call work correlated with contents.
Shared setup, actual coordination, memory and downstream consumption still
matter. Exact final pair-law equality cancels the expected cost of an identical
pair-only consumer; a consumer that also observes discarded auxiliaries is a
different contract. No physical latency or semantic improvement is measured.

## 4. Predeclared exact operational audit

Compute q_t from the three-class count formula and independently compare ALL729
tapes to ALL15 perfect matchings. Build a(s) from ALL compatible completions.
Freeze source before execution. Enumerate the complete rational partition of U
induced by every appended interval endpoint on all729 tapes; replay every cell
midpoint with original payload identities. Refuse beyond1000000 replay reads.
Check exact per-tape law q, actual stop counts, prefix survival optimum, and
all degree-six coefficients of(1),E A4,E A5. Retain all five original laws,
including any unfavorable comparison. These are proof/correctness objects,
not model samples, an independent benchmark or a timing campaign.

General reverse-martingale/Bernstein and common-component methods are prior
art. Exact primary read scopes and the difference between the conditional-
tape control and unrestricted factory must stay explicit. An LP optimizer
can also produce the candidate; no own generic optimization method is claimed.
