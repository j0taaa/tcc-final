# Two more endpoints: a proved subinterval of the six-pool family

Written after the tower proof and before new endpoint checks. Same eight
criteria, source, costs and unresolved useful-consumer/priority obligations.
This is a mathematical refinement, not a new benchmark gate or decoder.

Use the notation z=e2(p), w=e3(p), v=e4(p), b, q, H from
six-class-proof-v3.md. For the anonymous six-pool family lambda=90t-3,
the only changing empirical profile is(2,2,1,1), with

    big/big=1/6+t, big/small=1/12-t/2, small/small=t.

All other profiles stay as in the written law. The family is a valid
conditional pair law for0<=t<=1/6. Its centered population covariance is

    C_lambda=-sum_i D_lambda(p_i)b_i²
              +2lambda*(sum_i L_i b_i)²+R_lambda*q²,

where L_i=p_i(1-p_i-z)>=0, sum_i L_i=z, q=sum_i p_i b_i and

    D_lambda(x) = C_lambda0+[2(2-lambda)z+6lambda*w]x
                  +2(lambda-1)z*x²,
    C_lambda0=(6+2lambda)z²-(2+4lambda)w+4(lambda-1)v,
    R_lambda=2z+6z²+2(lambda-1)w+4(lambda-1)v.

Do not confuse the scalar C_lambda0 with the covariance form C_lambda.
This is just completion of the same exact law polynomial, not a new oracle.

## Endpoint lambda=3, t=1/15

Here R_3=2z+6z²+4w+8v>=0. The same two weighted Cauchy identities give

    C_3=-sum_i s_3i b_i²
        -6 sum_(i<j) L_i L_j(b_i-b_j)²
        -R_3 sum_(i<j) p_i p_j(b_i-b_j)².

For x=p_i, u=1-x and zi,wi,vi the remaining elementary polynomials,

    s_3i=2x²u²+12zi²-(6+8u)u wi+8u vi
         =2x²u²
          +(4+16u/3)*(zi²-3u wi/2)
          +(8-16u/3)*zi²+8u vi >0.

The last coefficient is >=8/3 since0<=u<=1. The non-obvious remainder
has the explicit counting expansion

    e2(y)²-(3/2)(sum y)e3(y)
      =sum_(j<k) y_j²y_k²
       +(1/2)sum_(j<k<l) y_jy_ky_l(y_j+y_k+y_l) >=0.

Thus this endpoint is strictly covariance-safe for every nonconstant class
mean. The proof does not assert lambda>=3 safe by extrapolation.

## Endpoint lambda=-3, t=0

Now

    D_-3(x)=10w-16v+(10z-18w)x-8zx²,
    R_-3=2z+6z²-8w-16v >0.

Indeed z²>=3w/2 by the preceding counting identity, and z²>=6v by the
elementary expansion of e2². Hence

    R_-3>=2z-2z²>0 for z>0,

using z<=1/2. Also w>=4v because (sum p)e3(p) contains4e4(p) plus
nonnegative terms. Complete the remaining weighted variance exactly:

    C_-3=-sum_i s_-3i b_i²-6*(sum_i L_i b_i)²
          -R_-3 sum_(i<j) p_i p_j(b_i-b_j)²,
    s_-3i=D_-3(x)-R_-3*x
          =u*(10w-16v)+2zx*(4u-3z)>0.

Both terms are nonnegative:10w-16v>=0 and z<=u (proved in the tower note).
The second is strictly positive for0<x<1 and z>0. This endpoint is safe.

## Consequence and limits

The full joint matrix and covariance form are AFFINE in t. Convexity between
these two safe endpoints proves universal covariance safety for

    0 <= t <= 1/15, equivalently -3<=lambda<=3.

This includes matching1/30, pivotal1/27 and A45 towers1/18. It is still
a PROVED SUBINTERVAL of the necessary interval[0,4/45] in A42 V8/V9.
The part(1/15,4/45] remains OPEN; the unsafe1/6 counterexample stays valid.
No full-interval characterization is claimed. All parameter choices have
the same optimal individual-atom diagonals; different members need not
dominate one another for every score projection. Current target-dependent
selection would need an independently justified protocol. No native model
evaluation, general-budget theorem or useful publication conclusion follows.
