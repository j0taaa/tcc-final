# V12 — Remove marginal tables from the integer-CDF preparation

2026-10-13. Written BEFORE code or performance measurements. V11's reduction
stands: this is an engineering refinement of the classical residual control,
not a fresh claim of inventing coupling, precision doubling or rejection.
The same eight criteria apply. The real operation remains exact correction
between two frozen grammatical heads; full-head input and both normalizers
are paid. An expensive pair of marginal tables need not be produced merely
to choose rounding precision. A prospective cost comparison must retain V8,
V9, direct target sampling and competent exact residual controls. Publication
significance and faster dLLM generation remain open.

## 1. Equality without marginals or numerical thresholds

Use V8's admitted smooth/decomposable word-faithful forest and integer heads
A,B. Compute the joint-support A total by the ordinary inside recurrence,
replacing each choice weight a by a*1[b>0]. Compute the joint-support B total
symmetrically. If either joint total differs from its own positive root
normalizer, the posterior supports differ and P!=Q.

Otherwise propagate the minimum and maximum PRODUCT ratio A(y)/B(y) over
the joint support. At a choice with a,b>0, both ratios are a/b. Empty leaves
have ratio1. Binary products multiply child extrema; OR alternatives take
minimum/maximum among nonempty alternatives. Decomposability makes the
extrema attainable and word-faithfulness makes them actual original events.
All rational ratio operands have polynomial bit length from the original
disjoint leaf scopes.

The two posteriors are equal iff their supports agree and both extrema
equal Z_A/Z_B. This is a classical likelihood-ratio range query, not a new
identity. It costs O(H) rational arithmetic and input/scaling work. It
does not enumerate words or ask for all n*q marginals. Z_A,Z_B must remain
the original positive root normalizers for this immutable state.

## 2. Precision determined by its own common-mass error bound

Let c be V8's exact local common mass, r=1-c. Let c_hat(S) be V9's dyadic
common mass with grid1/S and r_hat(S)=1-c_hat(S). The positive induction in
V9 gives

    0 <= c-c_hat(S) <= D/S.

For unequal laws, r>=TV(P,Q)>0. Evaluate c_hat using ONLY node grid integers
and the already prepared exact inside totals, without channel CDFs or
marginals. Start with S=2. Double the BIT PRECISION b (S=2^b), until

    2D <= S - Cint_root,

equivalently D/S<=r_hat(S)/2. Then

    r_hat <= r+D/S <= r+r_hat/2,
    TV <= r_hat <= 2r <= 4D*TV.

Construct V9's actual scaled common submeasure and channel CDFs ONCE at
that chosen grid. Its accepted law is still EXACT (P-Q)_+/TV. Expected
conditional attempts are at most4D; the discarded trial grids are not
sampling proposals, so adaptive preparation cannot bias outputs. If the
exact equality test says P=Q, return the same undefined residual state;
do not use a near-equality cutoff or loop indefinitely.

## 3. Termination and full costs

The grid test must hold once S>=2D/r, since r_hat>=r. For positive rational
posteriors, TV>=1/(Z_A*Z_B): at least one original word has a positive
integer cross-multiplied difference. Thus a sufficient b is
O(log(D+2)+log Z_A+log Z_B), polynomial in the cleared input bits. Doubling
b takes O(log(b+2)) trial passes and ends at less than twice a sufficient
bit precision, apart from the trivial initial grid. Equality/range work,
all trial passes, inside totals and CDF construction count toward preparation.
There is no all-marginal-table cost hidden in the implementation.

Memory keeps O(H) bounded-bit scalars/CDF entries, with original n*q input
stored separately. Trial pass operations use O(W+b+log(H+2))-bit integers;
selected trace and point submeasure products retain the polynomial D factor
from V9. Random-bit retries and residual attempts have the charged geometric
tails. A cap still returns FAIL and never a biased replacement from P.

This changes the engineering comparison: V9's fewer2D+1/2 attempts may be
offset by all marginals and larger preparation, while V12's4D bound may
have cheaper preparation. Neither inequality promises physical speed over
direct target sampling or the exact scalar control.

## 4. Independent verification required

Enumerate original words with the independent JSON/stack recognizer. Check
the exact support/range equality criterion against P=Q; reconstruct the
ACTUAL three channel laws and accepted law; verify the stopping inequality
and r_hat<=4D*TV. Include singular, tiny, scaled, fixed-slot, alias, prefix,
zero-posterior and equal-head cases. Grid trials count in evidence. No model
measurement is inferred from a finite law check, and no historical oracle
is relabelled as belonging to this new source.
