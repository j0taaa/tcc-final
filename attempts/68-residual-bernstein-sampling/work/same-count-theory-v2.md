# V2: the classical Peano slope bound removes the source-count penalty

2026-10-17, AFTER V1's successful audit, BEFORE V2 code/execution. V1 files,
sourceb5064b2 and raw data are unchanged. This refines a CLASSICAL numerical
differentiation error bound; it does not invent Peano kernels or claim that
the V1 experiment measured this tighter construction.

Use V1's definitions and all its hypotheses. For a forward three-point
quadratic first difference, Taylor's integral remainder gives

    S_m f(x)-f'(x)=integral_0^(2h) K_h(t) f'''(x+t) dt,
    K_h(t)=[4(h-t)_+^2-(2h-t)_+^2]/(4h).

On[0,h] the numerator is t(3t-4h)<=0; on[h,2h] it is
-(2h-t)^2<=0. Direct polynomial integration gives
integral|K_h|=h^2/3. Lipschitz f'' is absolutely continuous with an almost-
everywhere third derivative bounded by H; hence the integral formula applies
even across C2 spline knots. Reflection gives the backward case. Therefore

    |S_m f(x)-f'(x)|<=H/(3m),                           (1)

instead of V1's valid but loose H/m. This is the familiar sharper classical
finite-difference error constant, with its C2,1 justification written out.

The residual IDENTITY is unchanged. Replace only the known envelope by

    W*_m(z)=|z|/(3m)+z^2/(2sqrt(m))+|z|^3/6
                             +(|z|+2/sqrt(m))/[8(m-1)].

Now |g(Y)|<=H W*_m(Y-x) and the same moment calculation gives

    B*=H E W*_m <=[1/6+1/8+1/6+1/3]H/m^1.5
                       =19H/[24m^1.5].                 (2)

Keep |T|<=H/(21m^1.5). We can return to the tighter CLASSICAL delta_d=H/d^1.5,
initial degree d0 defined by M/[8(d0-1)]+17H/[15d0^1.5]<=epsilon, and

    w=2(delta_m-delta_(4m))=7H/[4m^1.5],
    a=w/2+T.

The safe margin is explicit:

    min(a,w-a)-B* >=[7/8-1/21-19/24]H/m^1.5
                               =H/[28m^1.5]>0.         (3)

Consequently V1's standard two-branch importance mixture is still valid,
now with B*,W*. Its conditional output law equals the normalized increment
of the SAME tighter H-gap classical coefficient factory. Its J distribution,
number N of p-coins, and complete Bernoulli(f(p)) output law are IDENTICAL
to that control, although auxiliary randomness/arithmetic differ.

    E N=d0+12H/sqrt(d0),
    total callback calls<=9,
    2B*/w<=19/21,
    E callback calls<=3+80H/[7d0^1.5].                  (4)

This removes V1's input-flip penalty rather than trading it away. It is not
yet a total latency/memory comparison. For the original spline d0=16,H=3/2,
the written input mean is41/2, exactly matching the tighter classical control;
the callback bound in(4) is183/56. Direct polynomial and analytic factories,
shared caching and other coefficient-free controls remain mandatory.

V1's exact-coefficient oracle lower-bound scope and theoretical fast-arithmetic
route are unchanged. Classical importance, control-variate and retrospective
sampling principles remain credited. The own candidate is a certified constant-
query implementation specialization with matched source count, not a new
quasi-interpolant or general Bernoulli-factory existence theorem. Specific
priority, useful complete cost and the full scientific goal remain OPEN.

V2 prospective audit: SAME six functions, old16/64 and ALL new k as V1,
with every residual/branch/law/callback/lower-bound check retained. Additionally
verify(1) against independently supplied analytic first derivatives at every
new x and old Y, including both switch directions and spline knots; check
mass19/24, branch19/21 and margin1/28 exactly. Refuse the same invalid/zero-H
inputs. Freeze new files BEFORE running once, no full sampler/NN/timing.
