# Legitimate nonlinear noising counterexample, not a model benchmark

Written BEFORE the neural toy/enum oracle. Pure proof object,2026-10-11.

Take clean JSON `[0,0]`, grammar S->[ N , N ], N->0|1. The two scalar
slots are eligible for masking; the syntax scaffold is fixed. At t=1/2
the four original independent mask patterns have equal probability. Let
r be the number of masks and a=ReLU(r)-2ReLU(r-1)+ReLU(r-2). Thus a is1
exactly when ONE position is masked. A simple legitimate conditional neural
model has target-zero logit -theta*a+log(3)*(1-a), alternative-one logit0
at each eligible position. This is a scalar ReLU gate and softmax, with one
trainable parameter theta, not an arbitrary table of invented loss numbers.

The original masked-token cross entropy with P=2,t=1/2 is

 L(r)=r*softplus(theta*a-log(3)*(1-a)).

For r=0/1/2 it equals0,softplus(theta),2*log(4/3). Its ordinary gradient
is respectively0,sigmoid(theta),0. Write b=sigmoid(theta)>0. Then

 E G=b/2, Var(G)=b^2/4.

MIRROR at t=1/2 complements both masks. This leaves a and G unchanged.
Its TWO-evaluation mean therefore has variance b^2/4, versus b^2/8 for
TWO iid evaluations of the SAME original policy. It is not worse than one
evaluation; it is twice the variance of the cost-matched iid2 mean.
This refutes an unconditional rho<=0 claim for arbitrary nonlinear gradients.
It does NOT refute MIRROR's empirical value or its explicitly conditional
variance formula. The same example has positive loss covariance when
softplus(theta)>(1+sqrt(2))*log(4/3).

C4 with key a has class sizes2/2 among M=4 and selects opposite classes,
so the retained gradient mean is EXACTLY b/2 and has variance0. Uniform
source derangement gives variance b^2/12 and must be reported too.

MOST IMPORTANT countercontrol: flip ONE mask bit instead of both. This
known analytic source permutation preserves each mask marginal, flips a,
and also has ZERO mean-gradient variance with only TWO noising queries.
It is CHEAPER than C4 here. The key/probabilities/inverse are known in this
example, so A39's no-free-unqueried-label minimax bound does not apply.

Consequently this example is not a useful-performance win, novelty evidence
or dataset chosen for our benchmark. It only tests the necessity of a
non-monotonicity-free guarantee and records a stronger cheap sampler.
Real usefulness must survive actual model/noising/GLC inputs and controls.
