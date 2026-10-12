# A grammar-specific precision count, without enlarging the implementation

Written proof before any corresponding manuscript revision or new timing.
This is a quantitative consequence of the existing endpoint/gate theorem;
binary parse-tree counting and source normalization are classical. The
independent V25 precision gate remains FAILED, and V26 is development.

## Admitted CNF word chart

Let an unambiguous epsilon/unit-free CNF grammar describe nonempty words.
Original tokens emit nonempty byte strings. Let

    B = sum_i max_{t in S_i, emission(t) supported} |emission(t)|.

If an entire position has no supported emission, feasibility is already zero.
Otherwise every original assignment emits at most B bytes. The last-byte
closure DAG and unambiguous chart supply the admitted original-event forest
already specified. Each chart cell is an OR over terminal edges or binary
production/split alternatives; each binary alternative is an AND. Empty-scope
units are exact and have no approximation cost.

**Lemma:** the maximum expanded compression count d is at most3B-2.

Proof: fix ANY root derivation emitting ell>=1 bytes. Its CNF tree has exactly
ell terminal cells and ell-1 binary cells. Each visited cell contributes at
most one OR compression, regardless of how many other alternatives its chart
contains. Each chosen binary alternative contributes at most one AND
compression. Thus the count is at most(2ell-1)+(ell-1)=3ell-2<=3B-2. Neutral
empty-scope and exact singleton passes can only reduce it. Parallel original
token closures/aliases affect the number of alternatives, not this tree
count. The bound is independent of the total chart size or number of rules.

For the implemented explicit-slot stack bridge, a similar structural count
is at most3n per derivation: one original-ID group OR, one binary product,
one suffix-state OR per physical slot. This does NOT make stack preparation
polynomial in n. It only bounds the compressed error propagation once the
explicit admitted bridge has been prepared.

## Quantitative consequence

Replacing the conservative generic d<=H by d<=3B in the established forest
theorem gives core size O(sqrt(B/epsilon)), core arithmetic work
O(H*(B/epsilon)*log(B/epsilon+2)) for bounded fan-in internal gates and
bounded singleton leaf lists, with the stated leaf-domain work added when
needed. Integer bit costs and both normalizers remain explicit. No root grid
in the active code is changed: it already computes its actual expanded count.

A normal chart cell can have a WIDE OR. Do not force binary OR conversion and
still reuse the3B bound: additional compressed OR nodes would add error.
Retaining the actual flat OR, an f-alternative union contains O(fM) rows and
costs O(fM log(fM+2)) with the existing unordered sort. Since the total number
of wires/alternatives is included in H, the appropriate full chart bound is

    O(H*((B/epsilon)*log(B/epsilon+2)
          +sqrt(B/epsilon)*log(H+2)))

arithmetic operations, plus input/normalizers. The second term pays wide-union
sorting; it cannot be dropped by calling the chart bounded-fan-in. Storage
is O(H*sqrt(B/epsilon)+B/epsilon), including one live Cartesian table and
wide-union storage. This is an upper bound, not an optimality claim.

This is a grammar-specific precision parameter, not a claim to improve the
classical cubic chart-construction cost, or a lower bound on every TV method.
Compared with a generic higher-dimensional compression bound instantiated at
dimension2, the sharpened endpoint precision dependence remains quantitative.
Do not call the parse-tree count itself a new parsing theorem.

## Full source-admission obligation

The lemma assumes an admitted UNAMBIGUOUS CNF grammar. It does not silently
certify a library normalizer. The earlier written source construction keeps
epsilon/unit productions, for which unit chains require additional accounting.
To apply this sharper bound to arbitrary LL(1) source input, explicitly prove
or cite an ambiguity-preserving polynomial CNF conversion after right
binarization, including removal of unproductive epsilon artifacts. Keeping
that obligation visible is preferable to assuming every language-preserving
normalization preserves derivation multiplicity.

For a FIXED admitted JSON CNF, preparation is separate and its size does not
grow with document nesting. Finite enumeration can attack the instantiated
claim but cannot replace admission or the general proof. No new model forward,
successful practical gate, exclusive novelty or human proof review is implied.
