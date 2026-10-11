# Deterministic work cap with exact marginals: written refinement

2026-10-11, AFTER sourcefdc5edc of the initial A34 proof, DURING A32/v4.
Do not relabel earlier frozen notes/results as this refinement.

## Eight questions revisited before a minimal reference

Same two native structured candidates and marginal/first-output contract;
the refinement makes a random-runtime mathematical construction deployable
with an explicit hard bound. Classical truncation and Dyck paths are credited.
The proposed distinction remains the sharp budget frontier PLUS certified
approximation of that frontier while preserving the ORIGINAL marginals,
not TV-approximate output sampling. Priority and significance remain open.
Compare ALL regular p-blind factories under expected cost, and Nacu–Peres/
bounded pools under hard cost. No probability-aware comparator is excluded.
First independent finite transcript oracles; no new neural campaign without
a useful cheap native transition and a novelty gate. Charge every draw and
full oracle classification, including fallback. A class with no semantic
signal gives zero gain. Neither deterministic cap nor proof implies general
EPIC latency superiority. The closest literature and useful application
remain publication obligations; no reviewer or result is invented.

## 1. Safe fallback, no added FAIL

Fix barrier r>=2 and hard cap n>=2. Start the exact ruin construction with
the original iid payloads X,Y. If they have different class bits, the walk
absorbs after Y. If both are1, its level after Y is2; if both are0, level r-2.
Run until absorption or n TOTAL oracle draws. At absorption use the final
payload. If unabsorbed at n, return the ORIGINAL Y. X always stays literal.

The only ways to change Y's class are:

- initial11, then first return of the total signed walk to0 before reaching r;
- initial00, then its complemented path returning to0 before reaching-r.

Every such terminating transcript has equally many ones and zeros: changing
11 to10 requires offsetting the initial excess of two ones, and vice versa.
Complementation is a bijection between the two switching sets, preserves n
and the barriers, and each length2h transcript has probability(pq)^h.
Thus the two class-switching flows are EXACTLY equal at ANY deterministic cap.
Both complete payload marginals remain P; choice of last or original Y
depends only on class bits and uses a distinct draw from X. No FAIL is added,
no conditioning on success and no renormalized tail. The pair law changes:
it is explicitly the capped law, not the uncapped target.

The stopped count is min(N_infinite,n), so E N<=r for every p and N<=n.
This fallback is NOT justified for a gold-aware, asymmetric or arbitrary
runtime/semantic stopping rule. A wall-clock timeout is not the same as the
deterministic draw cap; do not substitute one in the proof.

## 2. Certified uniform loss in normalized diversity

Let delta_(r,n) denote the switching flow, and a_(r,h) the number of allowed
positive first-return transcripts of length2h, beginning11, below barrier r.
These are restricted Dyck excursions, a classical combinatorial object.

    delta_(r,n)(p)=sum_(2<=h<=floor(n/2)) a_(r,h)(pq)^h.

The infinite sum gives delta_r. For p<=q,

    [delta_r(p)-delta_(r,n)(p)]/p²
      =q² sum_(h>floor(n/2)) a_(r,h)(pq)^(h-2)
      <=16[delta_r(1/2)-delta_(r,n)(1/2)].

At the fair point the last difference is1/4 times the probability of a late
return to0 conditional on initial11. The live walk on1,...,r-1 has symmetric
substochastic matrix Q, norm||Q||_2=cos(pi/r). Its probability of survival t
steps from level2 is <=sqrt(r-1) cos(pi/r)^t by Cauchy–Schwarz. A late return
requires survival through n-2 steps, hence for r>=3

    eta_(r,n)(p) >= 1-2/r
                  -4 sqrt(r-1) cos(pi/r)^(n-2), for EVERY p.

Swap0/1 for p>=q. For r=2, iid is already attained with exactly two draws;
there is no tail. The spectral/square-norm bound is CLASSICAL, not an
invented fast-mixing theorem. The useful statement is its application to an
exact-marginal capped pair and the normalized comparative guarantee.

For the budget-b mixture, r<=m+1. A common n yields

    eta_(b,n)(p) >= eta_b
      -4 sqrt(m) exp[-pi²(n-2)/(2(m+1)²)]

for all p, since cos(x)<=exp(-x²/2). Thus choosing

    n>=2+2(m+1)²/pi² * log[4 sqrt(m)/epsilon]

certifies eta>=eta_b-epsilon, with E total work<=b and hard work<=n.
Take a ceiling. Negative lower bounds are harmless but should be reported
as uninformative, not as positive utility. Exact probabilities/tokens are
preserved even when the diversity certificate is weak.

## 3. Practical and scientific boundaries

This is not superiority over every known-p method, and not the optimum joint
hard/expected-budget frontier. Native complete transition draws still have
parser/recovery costs. The old bounded walk maximizes a DIFFERENT target at
a fixed hard cap; its larger minimax expected work is not itself a fair
speed comparison. A34 needs its own tiny implementation, independent laws,
nearest-prior audit and meaningful native application before promotion.

