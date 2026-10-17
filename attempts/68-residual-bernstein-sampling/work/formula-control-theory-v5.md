# V5 competent formula-aware controls, before code or measurements

2026-10-17, AFTER V4 preflight, BEFORE V5 implementation. This is classical
control construction, not a new claimed contribution or a timing experiment.
V4's runtime/source/data remain unchanged. The six fixed functions are used
as known piecewise polynomials as well as callbacks; formulas are legitimate
information for all comparisons in which they are available.

## Exact compact coefficient integration

Given polynomial pieces of f on rational intervals, the classical FD
coefficient b_m(y)=f(y)-m*q(y)[f(y)-2f(y+s*h)+f(y+2s*h)]/[2(m-1)] is
piecewise polynomial, degree at most5 for a cubic spline. Partition integer
i by the known stencil switch y=1-2h and shifted knots y=a-j*s*h, j=0..2,
s=+-1. On each integer interval, expand its polynomial in y=i/m. No scan
of all function values is necessary to determine these pieces. Endpoint
conventions are harmless for the C2 functions used here.

For an integer interval[L,R], the factorial-moment identity is

    E[(K)_r 1{L<=K<=R}]
      =(m)_r(k)_r/(4m)_r * P(L-r<=K'<=R-r),
    K'~Hypergeom(4m-r,k-r,m-r).

It follows by cancelling (i)_r C(m,i)=(m)_r C(m-r,i-r) and the ratio of
binomial normalizers. Zero (k)_r terms vanish. Ordinary powers satisfy
i^j=sum_r S2(j,r)(i)_r, giving each restricted polynomial expectation
from finitely many exact hypergeometric interval masses. These are classical
factorial moments and polynomial integration, not a new factory mechanism.

Compute interval masses by balanced hypergeometric sums, using the shorter
inside or complementary tails; use1 for the complete support and0 for empty
intervals. Permit local and persistent memoization of interval masses,
compiled degree pieces and scalar probabilities. All preparation and cache
work is charged later. This control can have ZERO black-box f calls despite
performing actual formula/arithmetic work; the oracle lower bound does not
apply to a known spline formula.

## Analytic-derivative control

Also use the genuine classical coefficients
C_m(y)=f(y)-q(y)f''(y)/[2(m-1)]. Their piecewise degree is at most3,
with no shifted knots. The classical analysis gives approximation/elevation
error<=7H/(30m^1.5); delta=H/m^1.5 is valid. Select its own first power4
n0>=16 with M/[8(n0-1)]+H/n0^1.5<=epsilon. This can be smaller than the
FD n0; do not handicap it by forcing the larger degree. Its positive-mixture
factory targets the SAME f(p), although its conditional vote kernel can
differ from the FD kernel. On the current fixtures both initial degrees16
coincide; exact conditional kernels are compared against their respective
independent formulas, not falsely equated.

## Direct known-polynomial alternatives

Constant1/2, affine1/4+p/2, quadratic1/4+p^2/4 and cubic1/4+p^3/4 have
standard auxiliary-ticket/product factories. Include both output-only
short-circuit source work and non-adaptive preselected-parent alternatives.
For the latter a product branch preselects degree2/3; constant branches may
draw one unused dummy parent if a nonempty genealogy is required. No
source-outcome-dependent parent selection is then introduced. These cheap
controls can beat the candidate substantially and must remain visible.
They are not finite polynomial factories for the NONPOLYNOMIAL spline;
mark that scope rather than assign a false success or global failure.

## Prospective correctness checks only

- Freeze this proof and README criterion update, then freeze V5 source before
  ONE run. No runtime file fromV4 is edited; its validated outer sample loop
  may be reused with an explicit formula-vote subclass/dispatch.
- Verify the known six polynomial representations at every grid point
  n16,64,256 against the independent original Fraction functions.
- Compare exact HG interval masses with independent integer-combination sums,
  including empty/full/endpoint and complementary-tail cases.
- For all six base degree16 kernels, and all old m16,64/new k for H>0,
  compare compact FD and derivative probabilities with INDEPENDENT rational
  dense sums of their respective definitions. Check bounds without clipping.
- Execute both formula-aware complete controls for all six functions,
  p1/4,1/2,3/4 and seeds0..7, with the SAME external-source/level/auxiliary
  stream conventions as V4 and explicit65536 resource limit. Preserve FAIL.
- Exhaust the direct polynomial ticket/parent-bit laws with rational p;
  verify non-adaptive parent count is chosen before observing source bits.
  Keep cheap direct and padded alternatives distinct.
- Check scalar/piece/moment cache reuse with fresh RNG, and invalid input
  refusals. Report formula and moment work, not only zero f-query counts.

No competitive times or measurement gate are defined here. Remaining
coefficient-free/lazy controls and a full-cost, first-vote/repeated-vote
protocol must be justified/frozen before measuring a claimed advantage.
Priority, real useful benefit, publication and the user goal remain OPEN.
