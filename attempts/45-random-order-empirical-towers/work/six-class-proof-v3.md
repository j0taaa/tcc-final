# Six proposals: written arbitrary-class covariance proof

2026-10-16. WRITTEN before new symbolic checks, oracles or implementation.
This is a proof candidate subject to independent algebraic audit. It does
not prove the all-budget conjecture, new literature priority or a useful
neural application. A44's rejected consumer remains closed.

## 1. Eight criteria reassessment before further work

The existing README's operation, source assumptions and controls remain.
The precise change is mathematical: resolve six proposals (and seven by V2)
for ANY finite number of unknown-mass classes, including the one-parameter
interval below. Earlier A42 already proves a different six-pool kernel by
classical matching; A38 handles four/five. No dominance over those kernels
or their total costs is claimed. The possible distinction is a safety proof
for this particular random-label-order tower law. Tower coupling, empirical
transports, weighted Cauchy, degree elevation and symmetric polynomials are
CLASSICAL. Sufficient own significance/priority remains to be assessed.

First only audit the full law and algebra against rational enumeration.
Source/evaluator/continuation costs, fitted proxies, known-mass/RSS/CV/pivotal
controls and the lack of a useful source boundary still apply. Passing this
proof audit cannot trigger a neural campaign or satisfy the user's goal.
A defensible article still needs a useful own difference and a real consumer;
do not promote merely one more safe classical coupling.

## 2. Operation and class law

Use the original A45 operation on six IID ORIGINAL payloads from arbitrary P,
with a FIXED finite class map. Uniformly order the class blocks independently
of payload values and downstream scores. Pair a uniform ticket with its
half-circle antipode. Given the retained first payload's label, sample from
the corresponding conditional row and then a uniformly selected NONFIRST
original source index of the partner class. This retains the literal first
payload and both original marginals. Repeated values/aliases are not removed.

The empirical class diagonal is (r_i/3-1)_+. For all count profiles the law
equals A42's six-pool anonymous family, except that on(2,2,1,1) it has
small/small t=1/18 rather than the matching control's1/30:

    big/big=2/9, big/small=1/18, small/small=1/18.

Other profiles are forced by count symmetry and the minimum diagonal, as
tabulated in A42 V6. This finite enumeration, followed by multinomial
averaging, gives the same population identity used below. No numerical
population search is needed for the proof. The family interpolation has
lambda=90t-3, so the tower endpoint is lambda=2.

## 3. Exact covariance identity

Omit zero-mass classes; put p_i=P(class=i). For a centered scalar class-mean
score f, sum_i p_i f_i=0, define

    S_k=sum_i p_i^k,
    A=1-S_2,
    T=S_2-2S_3+S_4,
    B=A²+T,
    a_i=p_i f_i, h=sum_i p_i a_i,
    b_i=a_i+(h/A)p_i,
    q=sum_i p_i b_i=h/A,
    H=sum_i p_i² b_i,
    E=S_2²-S_4, D=S_2-S_3,
    F=A+2S_3+E, K=B+A,
    d_i=B+A p_i(2-p_i),
    e_i=E-2D p_i+A p_i².

A>0 when there are at least two positive classes. From the finite joint-law
polynomial (A42 family-algebra-v9), at lambda=2 the unconditional class
covariance quadratic form is exactly

    C(f) = -sum_i (d_i+2e_i)b_i²
           +4H²-4(1+S_2)qH+(K+2F)q².                  (1)

This population identity includes the random pool's mean variance; no
conditional covariance assertion is substituted for it. The transformation
to b also gives sum_i(1-p_i)b_i=0, although the final bounding step below
does not discard any needed normalization factor.

Write z=e_2(p), w=e_3(p), v=e_4(p) for elementary symmetric polynomials;
missing orders are zero. Newton identities give

    S_2=1-2z,
    S_3=1-3z+3w,
    S_4=1-4z+2z²+4w-4v.

Set

    C0=10(z²-w)+4v,
    R=2z+6z²+2w+4v >=0,
    L_i=p_i(1-p_i-z).

Substitution and completion of the square in(1) yield

    d_i+2e_i=C0+12w p_i+2z p_i²,
    K+2F-(1+S_2)²=R,
    H-(1+S_2)q/2 = -sum_i L_i b_i,
    C(f)=-sum_i(C0+12w p_i+2z p_i²)b_i²
          +4(sum_i L_i b_i)²+R(sum_i p_i b_i)².        (2)

## 4. Two different nonnegative weight systems

For x=p_i and u=1-x, let z_i=e_2(p without i). Then

    z=xu+z_i <= xu+u²=u.

The inequality z_i<=u² follows directly from nonnegative pair products.
Thus L_i>=0. Also

    sum_i L_i=1-S_2-z=z.

Apply weighted Cauchy SEPARATELY with weights L_i and p_i:

    (sum_i L_i b_i)² <= z sum_i L_i b_i²,
    (sum_i p_i b_i)² <= sum_i p_i b_i².

Since R>=0, equation(2) implies

    C(f) <= -sum_i s_i b_i²,                          (3)
    s_i=C0+12w x+2z x²-4z x(1-x-z)-R x
       =(1-x)C0-6zx(1-x)+8z²x.                       (4)

Using the SAME weights for both terms would give a weaker bound which can
fail, as recorded in A42 V9. No implication from that failed bound is used.

## 5. Explicit positive remainder for every number of classes

For the remaining probabilities after removing i, write

    u=sum_(j!=i) p_j=1-x,
    z_i=e_2(p without i),
    w_i=e_3(p without i),
    v_i=e_4(p without i).

Substitute z=xu+z_i, w=x z_i+w_i and v=x w_i+v_i into(4). Expanding gives

    s_i = 2(1+u)x²u² +4xu² z_i +2x z_i²
          +(6+4u)(z_i²-u w_i)+4u v_i.                (5)

Every term is nonnegative. To verify the only non-obvious term, for any
nonnegative remaining weights y with sum u,

    e_2(y)²-u e_3(y)
      =sum_(j<k) y_j²y_k²
       +sum_(j<k<l) y_jy_ky_l(y_j+y_k+y_l)
       +2 sum_(j<k<l<m) y_jy_ky_ly_m >=0.             (6)

This is an elementary counting expansion, not an appeal to an unverified
numerical inequality. If 0<x<1, the first term of(5) is STRICTLY positive.
With at least two positive classes, every s_i>0. Thus(3) is strictly
negative for every nonzero b. If b=0 then a=-(h/A)p, so sum_i a_i=0 forces
h=0, hence a=f=0 on the positive support. This proves C(f)<0 for every
nonconstant class-mean direction. A one-class map has covariance zero.

## 6. Original payloads, vectors, verifiers and seven proposals

Conditional on the class tape, selected distinct IID source indices carry
independent original within-class residuals. Selection uses ONLY class
labels and independent randomness. Hence the original score cross-covariance
is precisely the class-mean form already bounded in(3). For every
square-integrable finite-dimensional downstream score G,

    Cov(G(X),G(Y)) <=0,
    Cov((G(X)+G(Y))/2) <= Cov(G(Z))/2,

in Loewner order. A projected inequality is strict iff its conditional class
means differ. For a Boolean terminal verifier, pass@2 is at least IID2;
strict iff the conditional success probabilities differ. No semantic signal
or physical speed is presumed, and pass@1 is unchanged.

V2's full joint parity identity gives the SAME population pair law at seven
proposals, so seven adds no distributional benefit. No need to spend the
seventh draw in an implementation seeking this law. Equal joint law does
not mean the second fixed RNG-tape output stays literal.

By convexity of covariance in the family parameter and A42's already written
lambda=0 proof, EVERY t in[1/30,1/18] is now covered. This is only a proved
SUBINTERVAL of A42's necessary interval[0,4/45], not its entire sharp region.
Even pool sizes >=8 remain open; this argument is specific to the six-pool
polynomial. Classical matching/pivotal/RSS/CV/mass-informed controls remain
legitimate. No dominance over them, all-budget theorem, new neural work,
confirmed priority, human review or fulfilled scientific goal is claimed.
