# Full arithmetic accounting: remove the hidden GCD primitive

Written proof, not a new benchmark or measured-source modification. V25's
failed gate and V26's active program remain unchanged. This sharpens the
algorithm specification; choosing a common denominator is not itself novel.

## The concern

The ordered-product bound was stated PLUS reading/scaling/normalizers. A row
LCM computed by Euclid can have an arithmetic operation count depending on
the numeric bit lengths. Calling that unspecified preprocessing strongly
polynomial would hide work. Polynomial BIT cost was already recorded; these
are different statements. The actual reference currently uses LCMs.

## An explicit O(q) arithmetic scaling algorithm

For a row of q nonnegative rational probabilities a_j/b_j, with b_j positive,
set D=product_j b_j and return A_j=a_j*(D/b_j). All divisions are exact. This
uses O(q) integer arithmetic operations and O(sum_j bitlength(b_j)) bits for
D. Every A_j has polynomial input bits. D need not be the least denominator;
any common row multiplier cancels in the conditioned law.

An equally justified shortcut first takes D=max_j b_j and checks D mod b_j=0
for every j. When that succeeds, use this smaller D; otherwise use the product.
The shortcut and fallback both cost O(q) arithmetic operations. They require
no factoring, GCD oracle, ideal square root or minimum probability floor.
Dyadic rows always take the shortcut. Other rows may produce much larger
integers than an LCM: that bit cost must remain explicit, not called free.

## Consequence for the stated quantitative theorem

On normalized/subnormalized rational rows, exact scoped masses are bounded
by products of their row denominators. The same coordinate bound holds for
retained generators by the axis norm invariant. Consequently all intermediate
integer coordinates and determinant/projection comparisons have polynomial
total-input bit length under the scaling above. Grid computation adds a
polynomial dependence on log(n/epsilon+2), explicitly charged.

Reading/scaling costs O(nq), inside normalizers O(H), and the ordered product
core costs O(nq sqrt(n/epsilon) log(q+2)) arithmetic operations. Thus the SAME
complete bound, allowing the elementary grid-computation term, can be stated
for an explicit arithmetic algorithm whose operation count is independent of
numeric probability bit lengths and whose intermediates have polynomial
input length. The BIT running time still depends on those lengths, as it
must. For a general admitted forest retain the H/leaf-list/d bounds and all
source-grammar preparation costs; this is not a bound on every source API.

The programmed LCM reference has polynomial-bit preprocessing but has NOT
been changed to this algorithm while a measured experiment is running. It
cannot yet inherit the full operation-count statement. If the shortcut is
implemented, validate all original word/product cases and report complete
costs anew; no historical timings or archives may be reassigned.

## Scientific significance and limits

This closes an accounting detail, not a separate research direction. The
eight criteria in README and decision-operation-v27.md remain applicable.
Known common-denominator scaling is credited. The candidate novelty is the
quantitative deterministic TV precision bound, not this arithmetic trick or
the first polynomial-bit TV solver. Fu's extended real-arithmetic theorem is
a competent antecedent; this note does not prove that its principles cannot
be given a different effective rational implementation. Publication review
and priority remain open, and the unsuccessful practical gate remains so.
