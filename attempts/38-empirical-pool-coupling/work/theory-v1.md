# A38: empirical coupling, simultaneous atom optimum and its cost

Written2026-10-11 BEFORE implementation or model measurement. The construction
principle (empirical coupling/quantiles) and Bernstein bounds are precedents.
Specific priority and full-cost usefulness are NOT asserted.

## Contract

D is an iid COMPLETE-payload oracle, with arbitrary law P on a countable
alphabet; include failures. k is a fixed canonical map without gold answers.
The algorithm sees only draws/keys and independent randomness, never P.
It returns literal first X and another observed original payload Y, preserving
BOTH full marginals for EVERY oracle law. No external time-limit fallback.

Let p_i=P(k=i), c=sum_i p_i^2 and s3=sum_i p_i^3. First define a cap4
reference. Draw X1,...,X4. Let their canonical multiplicities be the pattern.

-2+2: return X1 and a uniform payload among the other canonical class.
-2+1+1: return X1 and a uniform payload among the two singleton indices if
  X1 belongs to the repeated class; otherwise among its two repeated indices.
-All other patterns: return X1 and the ORIGINAL X2.

Never select index1 as the second output. Canonical aliases remain distinct
payloads; choices inspect only keys. All probabilities in choices are1/2.

## Full marginals and law

Condition on the unordered four-sample multiset. First has its empirical law.
In2+2 and2+1+1, the displayed pairing has that SAME empirical law for second.
Other patterns retain original-second exchangeability. Averaging proves both
original marginals. This is standard conditional coupling, not a new principle.

Conditional on the class transcript, different original draw indices have
independent within-class payload laws. The rule never selects first, so full
joint payload law is the canonical joint law lifted through independent P|i.

For any outcome i with a=p_i, whenever its count among the four is2, the
reference never returns it twice. For counts0/1, twice is impossible; for3/4
it retains X2, giving conditional diagonal1/2 and1 respectively. Therefore

    J_ii = 2*a^3*(1-a)+a^4 = a^2-a^2*(1-a)^2,
    d_i  = a^2*(1-a)^2.                                      (1)

For i!=j, counting patterns2+2 and2+1+1 gives

    J_ij = p_i*p_j + e_ij,
    e_ij = p_i*p_j*(p_i+p_j-p_i*p_j-c).                       (2)

Some e_ij are NEGATIVE. Do not claim that every off-diagonal exceeds iid.
Nevertheless every common square-integrable RAW-payload score f has Cov<=0.
Write mu_i=E[f|i], mu=E[f], g_i=mu_i-mu. Algebra in (2) gives

    Cov(f(X),f(Y))
      = -(1-c)*sum_i p_i^2*g_i^2 - (sum_i p_i^2*g_i)^2 <=0.  (3)

Indeed the negative covariance is sum_(i<j) e_ij*(g_i-g_j)^2.
The part with p_i+p_j is sum p_i^2*g_i^2+c*Var_p(g); the part with p_i*p_j
is c*sum p_i^2*g_i^2-(sum p_i^2*g_i)^2, and the remaining c part cancels
c*Var_p(g). Thus all verifier events have pass@2>=iid2, including events
that distinguish raw aliases. Square integrability ensures convergence.

## Simultaneous pointwise optimality under cap4

Fix a canonical outcome i. For a variable a in(0,1), feed D the law
a*P_i+(1-a)*Q, where P_i is its original within-class law and Q the fixed
law of all other classes. Simulate this through Bernoulli(a) bits plus
P_i/Q randomness independent of a. Every candidate obeying the contract
is then a binary factory, retaining its first bit and using at most4 bits.

Pad a stopped execution with unobserved virtual iid bits to length4. Let
A_r be the conditional probability of both returned bits being1 given r
ones in that virtual tape. It does not depend on a. The joint diagonal is

    J11(a)=sum_(r=0)^4 binom(4,r)*a^r*(1-a)^(4-r)*A_r.

Both marginals Bernoulli(a) imply J00=J11-2a+1. Uniqueness of Bernstein
coefficients and nonnegativity of the two diagonals imply

    A_r>=0 and A_r+1-r/2>=0,
    hence A_r>=max(0,r/2-1).

Thus EVERY cap4 factory has J11>=2a^3*(1-a)+a^4, or gain<=a^2*(1-a)^2.
This is the known binary Bernstein argument, including independent auxiliary
information Q. Equation(1) ATTAINS it for EVERY atom simultaneously, for
every P, with unknown probabilities. Consequently it also maximizes total
canonical collision reduction under this contract. It does NOT bound informed
decoders, unknown algorithms with more than4 draws, or all generation methods.

The maximum collision reduction over all pairs with known marginals is
D_opt=c-max(0,2*max_i p_i-1), by classical half-circle quantiles. Equation(1)
gives sum_i d_i>=D_opt/4: below1/2, d_i>=p_i^2/4; for the single heavy
mass m>1/2, d_m>= (1-m)^2/4, and sum the others. Heavy mass1/2 plus diffuse
remaining mass makes the fraction tend to1/4. This is a proof object,
not a benchmark or claim of generation speed.

## Expected work and what optimality costs

If k(X2)=k(X3), every possible X4 would give a second output in that same
class; choosing ORIGINAL X2 has the same integrated raw within-class law.
Omit X4 in this case. This early version has the IDENTICAL full output law
and expected TOTAL full draws

    E N =4-Pr[k(X2)=k(X3)]=4-c.                              (4)

The reduction is distributional, not literal equality with every full-pool
RNG tape: choosing X2 rather than an interchangeable X3 may change that tape's
payload. It preserves literal FIRST and the promised full joint law.

The WORST expected work4 is necessary to attain (1) for all atoms/P under
cap4 and the retained-first/observed-payload contract. Here is the argument
to audit independently before calling it fully verified:

Equality in the Bernstein bound at any interior a forces every coefficient
to its minimum. Count_i=2 then forces zero diagonal. Since E[1_(Y=i)] has
Bernstein coefficient r/4, when count_i=2 and first!=i it forces Y=i with
probability1. In a positive-probability virtual multiset2+1+1, each singleton
first MUST therefore return the repeated class.

With at least three possible keys, stopping before draw3 cannot obey this:
two equal initial keys can be followed by two different keys, forbidding a
diagonal; two distinct initial keys can be followed by a third key twice,
forcing that unobserved key. After three DISTINCT keys, any premature return
can be contradicted by making draw4 repeat the other nonfirst key; returning
first is contradicted by repeating first. Therefore N>=3 always and N=4
on the event of three distinct initial keys. Hence

    E N >=3+Pr[three distinct]=4-3c+2s3.

For uniform P on M keys, this approaches4. Since the reference is cap4,
the infimum over all universal maximizers of sup_P E N is EXACTLY4.
Binary known-alphabet methods can have smaller cost; do not suppress them.
This is an oracle-call theorem, not a physical-time or arbitrary-tail theorem.

## Expected-budget3 comparison

Choose independently with probability1/2 this early reference or iid2.
It retains first, has both original marginals, cap4, expected draws3-c/2<=3,
and collision reduction at least D_opt/8. A37's guarantee is D_opt/13;
the new guarantee is stronger with the same WORST mean budget, but it need
not improve every P pointwise. Full costs/cheap verification/iid3/no-replacement
and known probabilities remain legitimate practical controls.

No implementation, model data, priority confirmation or publication claim
accompanies this first written version. Conditional empirical coupling and
the binary bound may make the result a known corollary; investigate that first.
