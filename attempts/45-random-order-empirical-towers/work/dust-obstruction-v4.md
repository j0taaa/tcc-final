# Rare-class completion: a written upper-bound audit before new checks

2026-10-16. Separate V4 mathematical refinement, BEFORE symbolic/rational
checks or a concrete finite obstruction. The eight criteria in the README
remain: no new consumer, neural campaign, timing or publication promotion.
V3's positive six/seven theorem and proved interval are preserved literally.
This note does not refute A45 towers (lambda=2), matching or pivotal.

## 1. An equivalence that prevents discarding the constraint too quickly

Write Q_lambda(p,b) for the completed covariance polynomial in the V3 notes:

    Q=-sum_i D_lambda(p_i)b_i²
       +2lambda*(sum_i L_i b_i)²+R_lambda*(sum_i p_i b_i)²,

where z=e2(p), w=e3(p), v=e4(p), L_i=p_i(1-p_i-z),

    D_lambda(x)=(6+2lambda)z²-(2+4lambda)w+4(lambda-1)v
               +[2(2-lambda)z+6lambda*w]x+2(lambda-1)z*x²,
    R_lambda=2z+6z²+2(lambda-1)w+4(lambda-1)v.

The actual covariance identity requires sum_i(1-p_i)b_i=0. V3's sufficient
proof happens to establish nonpositivity even WITHOUT that constraint for
the stated endpoints. An arbitrary violation of the unconstrained inequality
is not itself an admitted finite sampler counterexample. However:

**Rare-class completion lemma.** For a fixed lambda, Q<=0 for every finite
positive probability vector p and every constrained b IF AND ONLY IF Q<=0
for every finite positive p and every UNCONSTRAINED b.

One implication is immediate. For the other, suppose Q_lambda(p,b)>0 for
some unconstrained b on k classes. For epsilon>0 and integer M add M new
classes with mass epsilon/M each, and rescale the old masses:

    p'_i=(1-epsilon)p_i, i<=k;
    p'_(k+j)=epsilon/M, 1<=j<=M.

Keep old b_i. Put

    A_epsilon=sum_(i<=k) (1-(1-epsilon)p_i)b_i,
    b'_(k+j)=-A_epsilon/[M(1-epsilon/M)].

Then sum(1-p')b'=0 EXACTLY. All masses are positive. Taking M->infinity,
the new b values have squared sum O(1/M); their contributions to sum p'b'
and sum L'b' tend to zero. Old coefficients D,R converge to continuous
functions of epsilon and old power sums. Subsequently epsilon->0 makes
these coefficients converge to those of Q_lambda(p,b). Consequently there
exist FINITE epsilon>0 and FINITE M with constrained Q_lambda(p',b')>0.
This is continuity plus finite sums, not a statement that zero-mass classes
can carry nonzero b in the original operation. The orders of the two limits
and strict positivity of the original obstruction are essential.

For completeness, the b-to-score map is invertible on the admitted hyperplane.
Set q=sum p'_i b'_i and a_i=b'_i-q p'_i, f_i=a_i/p'_i. The constraint gives
sum b'=q, so sum a=0. Moreover h=sum p'a=q(1-S2), hence b=a+(h/A)p'
is exactly the V3 transformation. Thus the completed polynomial really is
the population covariance of this finite centered class score.

## 2. Two old classes already imply a stronger necessary upper bound

Take the UNCONSTRAINED base vector p=(x,y), x+y=1, x,y>0. Let

    z=xy, m=x-y, s=b_1+b_2, d=b_1-b_2.

Here w=v=0. Direct expansion of the above polynomial gives

    Q_lambda/z² = (lambda-5)s²/2+(3-lambda)m*s*d
                  +[(lambda+3)m²/2-6]d².                  (1)

The determinant of the NEGATIVE of this2x2 form is

    det = [(lambda-6)m²+15-3lambda].                       (2)

For9/2<lambda<=5 this determinant is negative when

    m² > (15-3lambda)/(6-lambda),

and such m²<1 exists. Thus the quadratic form has a positive direction.
For lambda>5, s=1,d=0 already gives a positive direction. By rare-class
completion, universal covariance safety for arbitrary finite class counts
therefore NECESSARILY requires

    lambda<=9/2, equivalently t<=1/12.                     (3)

This strengthens the earlier necessary t<=4/45 bound. It does NOT prove
sufficiency at1/12 or anywhere in(1/15,1/12]. All old finite screens remain
historical evidence under their old class-count ranges, not proofs.

At lambda=5 one particularly simple rational unconstrained base is

    p=(4/5,1/5), b=(7/16,9/16),
    s=1,d=-1/8,m=3/5,
    Q_5=63/31250 >0.

It is deliberately labeled UNCONSTRAINED here. Only a finite exact completion
and full original joint-law check may be reported as a concrete counterexample.
The limiting construction already proves existence of such a finite instance.

## 3. Verifiers and the limits of this obstruction

The resulting class score is finite. Shift and scale it into[0,1]. Enlarge
each source class with an independent Boolean payload having this success
probability. The sampler's class-only choice of distinct IID source indices
preserves conditional independence of those residuals. The downstream Boolean
verifier then has positive cross-covariance, so its pass@2 is BELOW iid2.
Rational masses/scores allow rational residual success probabilities. A class
indicator counterexample is not required for a claim about EVERY verifier.

This is an obstruction to the proposed larger family interval, not an asserted
real-model semantic failure, latency result, new lower bound for all samplers,
or fulfillment of the positive scientific goal. Completion, continuity and
quadratic-form determinants are classical. Any own priority/significance and
the useful-operation obligation remain OPEN. Next only minimal independent
symbolic/rational checking, not an expanded population or neural campaign.
