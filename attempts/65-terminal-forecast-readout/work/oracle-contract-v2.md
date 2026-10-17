# V2 minimal validation contract, before reference/oracle code

2026-10-17. The eight README criteria, real consumer and classical-principle
limitations remain. This is no native adapter, new head or performance gate.

Implement only a small callable proof reference: normalized nonnegative
rational vectors, fixed N helper calls returning a vector or None for a
noncompleting proposal, original normalized point retained in the mean, and
largest-remainder finite-decimal rendering. The caller supplies the SAME
frozen kernel; no reference code can certify this hypothesis by itself.

Use THREE independent exact oracles, fixed before code:

1. Enumerate all original/auxiliary outcomes for N=0,1,3 in two finite rational
   terminal kernels. Include aliases with equal normalized values, zero-sum
   uniform fallback, nonterminal/FAIL helpers and M=0. Check exact common mean,
   conditional covariance/second moments and binomial factor. Include guard
   checks for invalid vectors/budgets, charged draws and no first-input rewrite.
2. Enumerate an entire two-stage absorbing original chain. A has terminal
   weights1/4 each for raw(1/10,1/5), alias(1/5,2/5), raw(4/5,1/5), and
   nonterminal1/4 leading to B. B has terminal zero vector1/3, pure first1/6,
   pure second1/6 and FAIL1/3. Whole model-step/failure probabilities must stay
   unchanged. Check exact first moments and second-moment gain versus the
   occupation-weighted theorem, rather than a selected gold point. Also
   preserve expected helpers N times eligible mass11/12. No fake head claims.
3. Check rendering on a fixed finite set of simplex points and precisions0,2,8,
   bounds versus several fixed gold vectors. Preserve a native-grid-compatible
   SHORTCUT COUNTEREXAMPLE: equal mixture raw(.4,.6) and(.01,.01). Averaging
   before normalizing gives(41/102,61/102); its squared risk at gold(1,0) is
   WORSE than the normalized native mixture61/100. Correct semantic averaging
   has the common mean(9/20,11/20). This is a constructed correctness objection,
   not model performance evidence or novelty.

Freeze source BEFORE execution, report every assertion/failure and exact
counts. No main-suite count inflation, source/third-party execution, token
instance, dataset row/gold, native replay, competitive timing or backbone
forward is authorized by this reference. If it passes, next is a prospectively
frozen native correctness/variance-necessity screen; a proof with tiny terminal
variance or expensive helpers is insufficient to justify a large application.
