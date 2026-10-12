# Conditional atom optimality does not imply IID covariance or verifier safety

The prospectively frozen endpoint screen b7ee9e0 stopped after3,842 checks
at an adverse five-class profile for t=1/6. This floating result was only
a search aid. A simpler EXACT rational verifier obstruction is:

    p=(49/100,49/100,1/150,1/150,1/150),
    event A={the three rare classes}, P(A)=1/50.

The t=1/6 conditional law preserves BOTH original marginals and attains the
minimum empirical diagonal for EVERY individual class in EVERY six-pool.
Yet the rational unconditional joint matrix gives

    Pr(X in A,Y in A)-P(A)^2 = 111816971/1687500000000 >0.

Its pass@2 is smaller than iid2 by exactly that positive fraction. Thus the
whole proposed family is NOT safe; neither increasing diversity per atom
nor its optimality proves the user's desired result. No class or failure
was excluded, and no tolerance was changed. V6's matching t=1/30 remains
covered by its pure proof; pivotal's t=1/27 and grouped rank alternatives
are not claimed unsafe by this counterexample.

## Necessary boundary for ANY number of classes

Take two heavy classes with masses(1-q)/2, and m equal rare classes with
mass q/m. Let A be the union of rare classes. As q tends to zero, the
two-rare-class contribution comes only from count profile(2,2,1,1).
Choosing the two rare positions gives15; the four other positions have
two of each heavy class with probability6*(1/2)^4. The event's conditional
joint probability is2t if the rare labels differ, and zero if they agree.
Consequently

    lim_(q->0) Cov(1_A(X),1_A(Y))/q^2
        = (45/4)*t*(1-1/m)-1.

For fixed m>=3 this forces t<=4m/(45*(m-1)). Since the family may have
arbitrarily many classes, universal covariance safety forces t<=4/45.
This is a NECESSARY bound only. Whether all t in[0,4/45] are safe is still
open. An absence of finite numerical obstructions will not prove it.

The exact JSON includes the complete rational joint matrix, its marginals,
atom diagonals and this verifier event. It is a proof object, not external
model data, practical superiority or an independent application benchmark.
