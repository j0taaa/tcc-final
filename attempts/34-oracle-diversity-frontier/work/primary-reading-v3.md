# Primary comparison completed after v2: Wasan and the output restriction

2026-10-11. This is a NEW dated reading record; older frozen retrieval failures
remain historical facts. It does not change the producer of A32/v4 or claim
publication priority from a search that returned no match.

## Original full texts actually read

Wasan1964 ORIGINAL13 pages, Sections1.1,2.1--2.5,3.1--3.3 and references:
[public CMU journal archive](https://stat.cmu.edu/technometrics/59-69/VOL-06-03/v0603259.pdf).
PDF743666bytes/SHA256 `7a4f32ff616482389f50b1cd9e55181bc7d7cc946e8cdbf723712fe349116b36`.
Printed261/262 were VISUALLY inspected, not only OCR. Section2.1 already
constructs the randomized m/m+1 fixed-sample estimator with variance
`[(1-lambda)/m+lambda/(m+1)]p(1-p)`. The expression s_b and the idea of mixing
adjacent integer budgets are therefore EXPLICIT precedents, not inventions.
Wasan does NOT establish sharpness of that expression for noninteger budgets
in Section2.1; he says the unrestricted variance problem lacks a uniform
minimizer. His output is a real estimator, not two original decoder payloads.
Sections2.3/2.4 analyze curtailed and truncated sampling asymptotically;
Section3 trades estimator variance against observation cost. These principles
must also be credited in any proposed two-cost application.

The proposed A34 distinction is narrower: output-pair integrality supplies
an exact lower bound s_b (stronger than1/b at noninteger b), and a retained-
first construction reaches that bound uniformly in normalized binary Fréchet
improvement. The fixed-size estimator of Wasan cannot directly serve as two
payloads: its mean has values such as1/3 and2/3, whereas (X+Y)/2 only admits
0,1/2,1. Additional rounding may change variance and original payload laws.
This difference is a candidate result, not proof of publication significance.

Wu/Wasan1991, ORIGINAL7 pages/Sections1/2 and all theorem proofs were read at
[the journal MathNet archive](https://m.mathnet.ru/links/184e9dacad20e68d4e42298c3c2cb510/tvp2849.pdf).
Theorem2.1 derives polynomial moments for curtailed stopping, Theorem2.2
proves no uniformly least-work plan under a maximum-variance bound for m>=5,
and Theorem2.3 supplies asymptotic error estimates. It explicitly distinguishes
pointwise/uniform expected-work criteria. This does not itself state the
output-pair normalized frontier. It is NOT substituted for an unexamined
subsequent paper.

Ghosh/Purkayastha2010 authored review, ORIGINAL Sections2--5 OCR actually
read at [the public uploaded original](https://www.scribd.com/document/829519814/Battacharya).
Theorem5 and Remarks8/9 explain Ghosh1987's ALL-parameter attainment and
inverse-binomial cases, plus Simons' regularity counterexample. This is a
primary authored review but NOT the original1987 paper. A34's fair-point
identity must not be confused with attaining Cramér--Rao at every p.

## An apparent strictness problem: audit separately before asserting a correction

Wasan's printed261 Theorem1 states that a non-fixed plan with uniformly bounded
variance1/(4m) must have STRICT E_(1/2)N>m. Printed262 repeats that premise.
The r=3 first-return/excursion plan in A34 appears to contradict this strict
clause, while preserving the NONSTRICT minimax bound:

- after one bit, stop the signed walk at first return0 or |M|=3;
- estimate H=1/2+M_N/6, in{0,1/2,1};
- E_p N=3 and E_p H=p for EVERY p;
- Var_p H=z(1-2z)/[2(1-z)]<=1/12, z=p(1-p);
- equality at p=1/2, although N is random with positive mass at2 and3.

The variance inequality follows by clearing positive denominator:
`1/12 - Var H = (1-4z)(1-3z)/[12(1-z)]>=0` for0<=z<=1/4.
Finite live-state equations independently recomputed these moments rationally
at six p values. The r=3 chain also lies among the66 A34 independent tests.
Uniform geometric tails give the regularity conditions. The stopping rule
uses ONLY (n,S_n); it is not an output-specific hidden use of p. It is closed
but not a simple contiguous boundary. The original theorem does not state a
simple-boundary restriction at that point; investigate whether a correction
or implicit narrower convention resolves this before claiming a new erratum.

This observation is NOT the requested dLLM contribution by itself. Do not
turn an old apparent error into a publicity claim or contact authors/journals.
Its relevance is to prevent a false uniqueness argument from invalidating a
valid candidate construction, and to refine what is already known.

## Outstanding obligations

Specific priority of the discrete-output sharp frontier (including implicit
reductions); regularity scope; meaningful accepted-transition application;
raw-randomness side-information controls; probability-aware approximations;
more-output iid; total cost and semantic class signal. Original full1987
retrieval is still missing, but the1959/1964 mathematical gaps have materially
narrowed. No independent human review or publication acceptance is claimed.
