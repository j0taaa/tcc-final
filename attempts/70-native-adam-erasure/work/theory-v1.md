# A70 V1 — Exact observable reconstruction by rounded-state erasure

Written2026-10-17 BEFORE source/execution. Classical rounding/interval tools;
candidate is their precise lazy-optimizer consequence. Priority/use OPEN.

## 1. The reference operation, including every rounding

Let R denote IEEE binary32 round-to-nearest-ties-to-even, with gradual
underflow, finite admitted results and NO contraction/reassociation. Inputs
and each named intermediate are binary32. Let beta1,beta2 in(0,1),
c1=R(1-beta1), c2=R(1-beta2), epsilon>0. At step t use SUPPLIED positive
binary32 scalars a_t,d_t. For conventional Adam these are its learning rate
divided by its first bias correction, and the square root of its second
bias correction, respectively. Their actual bits are part of the input:
no claim about exact pow/libm or another library's formula is required.

    m' = R(R(beta1*m) + R(c1*g))
    v' = R(R(beta2*v) + R(R(c2*g)*g))
    z  = R(R(sqrt_R(v')/d_t) + epsilon)
    u  = R(R(a_t*m')/z)
    w' = R(w-u).                                           (1)

The square root is correctly rounded in the reference contract. Inputs have
v>=0; zero-gradient steps have g=+0. Include their actual effect on signed
zero. There is no weight decay, stochastic rounding, EMA overwrite, trust
ratio, or observer of optimizer moments during an implicit interval.
NaNs/infinities, nonpositive denominators and FP modes outside this contract
are not certified. Admission/fallback must not silently relabel them.

Schedule scalars are COMMON inputs to every control, prepared/checked once
with their cost included. A bound A>=max a_t over the skipped interval is
also required. A supplied bound is validated, or an ordinary range-max data
structure is charged. This is not a claim that preparing a whole schedule
has constant cost. d_t>0 and nonnegative rounded sqrt imply z>=epsilon.

The operation is a scalar row/coordinate of a sparse read interface. After
the last actual gradient at s, the coordinate is not read and its actual
gradients are +0 until its next read after h steps. The stored starting
(w_s,m_s,v_s) is exact. Its implicit representation retains these exact seeds
and a counter, not approximate concrete optimizer moments.

## 2. A guard for ALL remaining parameter writes

For finite x>=0 and 0<beta<1, 0<=R(beta*x)<=x. This follows from monotonicity
of nearest rounding and the available representable upper endpoint x.
For signed m, |m| cannot increase under the zero-gradient moment recurrence;
its nonzero sign cannot reverse. Zero-sign changes are harmless below because
the parameter is required to be nonzero and endpoint certificates require
nonzero resulting moments.

At an exactly replayed prefix state (w,m,v), compute

    U = R(R(A*abs(m))/epsilon),
    G = [w is finite/nonzero, U finite,
         bits(R(w-sign(m)*U)) == bits(w)].                  (2)

When m is zero either direction may be used. Positive arithmetic in(1) is
monotone, a_t<=A and z>=epsilon, so EVERY future zero-gradient |u|<=U.
All those updates have the same weak direction as m. Nearest rounding is
constant over the segment from w to w-sign(m)*U when its endpoints round to
the same NONZERO w. Therefore the first subsequent parameter write equals
w bit-for-bit. Inductively every later zero-gradient parameter write does
too, while |m| remains bounded by the same |m|. This proves(2) for ANY finite
remaining gap without evaluating those nonlinear weight updates.

This is a classical floating-point absorption/invariant argument. It does
not assert that many small REAL increments sum to zero. Rounding once after
summing differs: at w=1, four decrements2^-26 are individually absorbed in
binary32, while their sum2^-24 is not. Treating BF16 projection absorption as
FP32-master absorption is likewise invalid.

## 3. Cheap upper enclosure for a ROUNDED moment recurrence

For binary32 set unit roundoff u=2^-24 and least positive subnormal nu=2^-149.
The standard rounding bound gives, for finite x>=0,

    R(beta*x) <= alpha*x + nu/2,  alpha=beta*(1+u)<1.

For admitted binary32 beta<1, even its largest possible value1-u satisfies
beta*(1+u)<1. Write delta=1-alpha>0 and gamma=nu/(2*delta). Induction gives

    x_r <= alpha^r*x_0 + gamma*(1-alpha^r)
        <= alpha^r*x_0 + gamma.                            (3)

All constants here are exact rationals, not rounded down. Put

    M=ceil(1/delta),  k=floor(r/M).

Since (1-delta)^M<=exp(-delta*M)<=exp(-1)<1/2, alpha^r<=2^-k.
Use the deliberately COARSER bounded-exponent enclosure

    B_beta(x_0,r) = x_0*2^-min(k,512)+gamma.                 (4)

Thus the true rounded nonnegative moment lies in[0,B]. For a signed moment,
use[0,B] or[-B,0] according to its original sign, conservatively including
both zero representations as possible. Rounding B UP to binary32 is sound;
if the upper bound overflows, the cheap certificate is unavailable.

No exact rational beta^r is materialized. The exponent is at most512, and
binary32 values/constants have a fixed finite bit range. Computing(4) and
its upward-rounded endpoint costs O(log(r+2)) bit work with fixed-format
constant arithmetic (or that plus the stated integer-division cost), and
O(log(r+2)) counter bits. More conservatively, with ordinary big-integer
division the bound is polynomial in log(r+2), independent of r iterations.
It is not a constant-bit theorem for a varying precision/exponent format.

The enclosure has a nonzero rounding floor gamma, which is ESSENTIAL.
Repeated multiplication can stick at a subnormal fixed point instead of
decaying to zero. Substituting beta^r*x0 without a sound rounding allowance
is not a bound on(1). The coarse512 cap preserves soundness for huge binary
gaps without constructing an exponentially long denominator.

## 4. A fresh gradient can erase uncertainty EXACTLY

After a guard succeeds at prefix length j<=h, retain w exactly and seeds
m_j,v_j. At the next model read, return w; do not expose a guessed moment.
After the model supplies its fresh binary32 gradient g, use(4) for the r=h-j
remaining zero steps to enclose the true m_h and v_h.

For FIXED g the two moment-update maps in(1) are monotone in the old moment,
since beta1,beta2>0 and each primitive rounding is monotone. Evaluate each
map at its lower and upper interval endpoints. Accept a concrete new m' or
v' only when BOTH endpoint results have identical bits and that common result
is finite and NONZERO. Then every possible enclosed native old moment maps
to the same new value, bit-for-bit. Excluding zero outputs avoids conflating
their two representations via a numeric monotonicity argument.

If BOTH maps are admitted, compute the current weight update from exact w,
the recovered exact m',v', and the supplied scalars. It equals(1). Discard
the now-erased uncertainty and store the exact new state/timestamp. This is
a standard interval/Ziv-style test applied to an unobserved rounded-state
recurrence, not invention of the endpoint principle.

If either map is undecided, replay the r native MOMENT steps from the exact
seeds, then apply the fresh gradient and exact weight update. The parameter
tail need not be replayed because(2) already proved it constant. This finite
fallback preserves boundary/zero/failure cases; termination does not rely on
indefinitely refining an interval containing a rounding boundary.

## 5. Algorithm and identity theorem

At a sparse coordinate read:

1. Replay native zero steps, checking(2) at each exact state, for at most a
   predeclared cap H or the whole gap, whichever comes first.
2. If no guard succeeds, replay the remaining native steps, return the exact
   parameter, and execute the fresh-gradient step normally.
3. If a guard succeeds, return its exact w and retain the implicit moments.
   Apply the fresh-gradient endpoint admission/fallback in Section4.
4. Any observer/export requiring moments before that fresh update triggers
   exact materialization. Those costs are real, not a certificate success.

THEOREM (WRITTEN). Under Section1's FP and read/state contract, every returned
parameter and every stored state after a fresh-gradient update equals the
eager recurrence(1) bit-for-bit. It holds for adaptive sparse read sets and
gradients depending on all returned parameter values, provided the model's
other state/RNG and supplied schedule are preserved and moments are hidden.

Proof: literal replay is identical. A guard implies all skipped parameter
writes equal its exact w by Section2. The interval contains the literal
rounded moments by Section3; admission recovers their exact next values by
Section4, or exact replay does. The current weight update therefore matches.
Induct on reads/steps: identical consumed parameters, model state and RNG give
identical next gradients/read decisions; apply the same local argument.
An observer asking for hidden moments falls back to literal materialization.
This is a mathematical trace theorem for the DECLARED recurrence/interface,
not a validated arbitrary software/library/distributed execution theorem.

## 6. Delimited benefit and all costs

For a gap h whose guard succeeds after j<=H and whose two fresh maps admit
erasure, the algorithm executes j zero steps, bounded-format rational bounds
and endpoint checks, rather than h literal native zero steps. Its gap counter
work is polynomial in log(h+2); no h-term moment/power sum remains. If the
guard succeeds but erasure fails, r moment-only steps are still paid. If no
guard succeeds, the full gap plus guard overhead is paid. This is a
conditional comparative UPPER bound, not a lower bound on all exact methods.

The relevant potential benefit is exact native preservation with less work
on natural long inactive intervals. There is no claim that every/typical
gap qualifies, or that a j-step scalar loop beats a vectorized dense kernel.
Per-coordinate seeds, pending counter, schedule preprocessing/range queries,
certification, copies, final state export and all model computation count.
Weight-absorption-only replay, generic interval erasure, real-kernel interval
methods and fused eager implementations are mandatory strong controls.

GS-Scale's cap15 and reported short delays do not establish this condition;
no quality campaign is proposed for its scenes here. PULSE's BF16-visible
sparsity under DENSE gradients does not establish zero-gradient FP32-master
gaps. Sparse embeddings are a plausible consumer requiring a separate
input-only real workload audit. Adequate priority/use/whole-cost benefit,
formal verification and sufficient publication significance remain OPEN.
