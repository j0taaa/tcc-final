# V11 — All-law work certificates on the existing optimal faces, before code

2026-10-17. AFTER V10's eight exact optima, BEFORE new solver/auditor code or
any new solve. The unfavorable cap11 point-mass cost and all prior data stay
preserved. V10's objective/producing commits are not retroactively changed.

## Eight criteria refinement

README1/8 remain OPEN: no exact real consumer or sufficient priority from more
certificates. For2/3/4 the candidate is a true family minimax source-work result,
if the old U3 lower bounds can be matched by all-law upper rules. Schur-Ostrowski
and coefficient positivity are CLASSICAL sufficient tools, not own theory.
For5 seek feasible primals for ALL4..11 using the SAME frozen lower bounds;
regress4..7 first. Preserve every inconclusive/numerical failure. For6/7 source
count is not full-cost utility; all prior controls/cost objections still apply.
The coefficient cone may be too restrictive and failure is not impossibility.

## 1. Symmetric cost polynomial

Given a count-flow primal c(k), use a fair independent choice of the two
mappings of the actual other keys into1/2 after the literal first key.
This leaves the full target raw pair law unchanged. Write L=B-1 and S=p0+p1+p2.
The expected-work polynomial on S=1 has homogeneous form

    G(p)=S^L + (1/2) sum_(sigma in S3) sum_(|k|<=B-2)
         M(k)c(k) p_(sigma0)^(k0+1) p_(sigma1)^k1 p_(sigma2)^k2
         S^(L-|k|-1).                                    (1)

It is symmetric in all three masses. The first term charges the original
first draw; k=0 with c(0)=1 charges the first nonfirst draw. No score evaluation
or model operation is hidden in this polynomial.

Let

    Q(p)=[partial_1 G(p)-partial_0 G(p)]/(p0-p1).

Symmetry makes the division exact; Q is homogeneous of degree L-2. If EVERY
ordinary monomial coefficient of Q is nonnegative, then Q>=0 on the positive
orthant. Thus equalizing any two unequal coordinates while fixing their sum
cannot decrease G: the directional derivative toward equality is
(p0-p1)Q>=0. Symmetry covers the other pairs. Repeated averaging and continuity
give

    E_P N=G(p)<=G(1/3,1/3,1/3).                          (2)

This is the usual Schur-concavity criterion, with its elementary averaging
proof; not a new inequality principle. It is only a SUFFICIENT certificate.
Nonpositive monomial coefficients do not prove a violation on the simplex.

## 2. Linear feasibility on the original optimal face

Every coefficient of Q is linear in c(k). The first constant term S^L has
zero derivative difference. Add these rational linear inequalities to V10's
count-flow equations, and constrain the original U3 objective to E_B^*, the
already independently verified exact optimum at that cap. Set the numerical
feasibility objective to zero; no newly selected favorable mass law is fitted.

If a rational primal satisfies the original equations, the old U3 value and
the nonnegative Schur coefficients, then the existing unrestricted dual proves
a lower bound against ALL exact-law algorithms, while(2) proves a matching
all-P upper bound. Hence this is a sharp MINIMAX source-work value for the
fixed full ordered-law operation. It does not extend the old broader atom-
maximizer lower bound to8+ or show pointwise optimality at every nonuniform P.

Keep the old dual and producing source reference explicit. This is a new
upper-rule search, NOT a new independent lower-bound computation or a claim
that the numerical Schur LP proves infeasibility. If no certified primal is
found, report the gap/open status; do not raise the target cost and call the
restricted solution globally optimal.

## 3. Frozen execution/verification contract

Use the existing isolated NumPy2.2.6/SciPy1.15.3, HiGHS-ds60s, nonnegative
variables, exact original equalities plus the fair-cost equality and Schur
coefficient inequalities. Numerical reconstruction uses the predeclared1e-10
zero proposal and denominator<=100000000; exact arithmetic decides acceptance.

ALL4..11 remain. First require4..7 new primals and the expected old costs; if
those fail, preserve8..11 as NOT_RUN until the mechanism is corrected. Otherwise
run all8..11 without cap selection. Status is MINIMAX_CERTIFIED only after an
independent stdlib verifier checks the old full dual with the NEW primal,
all named-tail realization and terminal coefficients, recomputes(1) and its
symmetry, divides the derivative polynomial using an independent algorithm,
and confirms every rational coefficient of Q>=0 plus equality at U3.

The solver can use antisymmetric-pair polynomial division; the verifier must
use direct polynomial long division. No import of solver algebra by verifier.
Reuse of the unchanged V10 independent word/dual verifier is explicit and
its source remains frozen in this version. The1000000 word-prefix guard per
cap stays. Record all five original weighted laws, especially the point mass.

Primal/status/raw floating output, source hashes and any numerical/cone failure
must be preserved. No new model/head/weights/row-label/update or timing. No
equality of odd/even work, all-budget asymptotic attainment, practical speed
or sufficient publication originality is inferred even if every finite cap
gets a valid certificate. A real full-cost consumer remains a separate task.
