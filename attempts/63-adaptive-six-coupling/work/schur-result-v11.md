# V11 — Four global regression certificates; four larger cases remain open

2026-10-17. Contractc2d42edb897671feae82d8e43d2907625ceac73a precedes
sourcead7e82f37505038249fee985bccbc83d4e09a560 and ALL new executions.
The four regressions passed before the four larger-cap searches launched.
All eight producing exits and four verifying exits were directly observed.

| Cap | Frozen U3 optimum | New Schur search | Independent global audit |
| --- | --- | --- | --- |
| 4 | 31/9 | MINIMAX_CERTIFIED | MINIMAX_VERIFIED |
| 5 | 31/9 | MINIMAX_CERTIFIED | MINIMAX_VERIFIED |
| 6 | 386/81 | MINIMAX_CERTIFIED | MINIMAX_VERIFIED |
| 7 | 386/81 | MINIMAX_CERTIFIED | MINIMAX_VERIFIED |
| 8 | 4529/729 | INCONCLUSIVE | NOT_RUN: no new certified primal |
| 9 | 40663/6561 | INCONCLUSIVE | NOT_RUN: no new certified primal |
| 10 | 620/81 | INCONCLUSIVE | NOT_RUN: no new certified primal |
| 11 | 450262/59049 | INCONCLUSIVE | NOT_RUN: no new certified primal |

For4..7, the NEW rational primal and the UNCHANGED original unrestricted
V10 dual have zero exact gap. The independent verifier reconstructs the
homogeneous cost from new continuation flows, checks all six permutations,
and uses direct polynomial long division for the Schur quotient. Every
coefficient is nonnegative. Thus the cost is maximized at U3, giving a
matching all-P minimax upper bound for the FIXED full ordered pair law.
The lower bounds are explicitly REUSED, not computed independently again.
The broader old cap6/7 atom-maximizer theorem remains separate and valid.

The operational re-audit covers1080 first0 named tails and4140 prefix steps
in total, checking terminal count/output coefficients and all five original
weighted laws. No literal first-native-RNG/tape equivalence is asserted.

For8..11, HiGHS reports the added sufficient coefficient cone infeasible;
each process exits2 and its record remains INCONCLUSIVE. There is no rational
infeasibility certificate here. Even exact infeasibility of THIS cone would
not prove absence of another all-law upper bound. It does not invalidate
V10's exact U3 primal/dual optima or prove that they are minimax optima.
All four failures and the old cap11 unfavorable point-mass cost are retained.

Schur--Ostrowski, symmetrization and coefficient positivity are classical.
This is a successful alternative verification of small-cap bounds and an
unsuccessful sufficient-certificate search for the new cases, not a new
all-budget theory. There is no asymptotic upper result, timing, model/head,
neural forward, semantic observation or parameter update. The345-test
maintained suite was not rerun or credited; these exact CLI checks are separate.

## Decision under the eight criteria

Criteria2/4/5 now have the eight verified U3 optima of V10, including small
strict odd-cap effects, but no confirmed substantive new family minimax
theorem beyond4..7. Criteria1/6/8 remain OPEN: a real useful full-cost consumer
and sufficient own priority have not been established. V8's strong unrestricted
estimation controls still apply. Increasing caps, widening a certificate cone
or generating more solver constants is not justified merely to accumulate
positive-looking results. The next investigation must establish an independent
scientific/application consequence or a genuinely different direction before
another extensive implementation or neural campaign. The user's goal remains
active and is NOT considered fulfilled by this finite certificate family.

Raw records, exact polynomials, logs, source hashes and statuses are in
`evidence/v11/`; V10 records are unchanged in `evidence/v10/`.
