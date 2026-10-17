# Adaptive typed-read mean: written audit before code

2026-10-17. Classical optional sampling/conditioning; no priority claim.

## Target and actual controller

Condition on a fixed prompt, template, model configuration and any shared
thought. Let Z_1,...,Z_m be iid TOTAL read packets and X_i=x(Z_i) their
concatenated probability vectors, in a product of simplexes. Let A(z) be the
same global predicate as the controller: at least one question's returned
entropy is strictly above the threshold. It may depend on more than X.
Write a=P(A), mu_H=E[X|A], mu_L=E[X|not A], mu=E[X]. At a=0/1 omit the
unused conditional quantities. Assume finite m>=1.

Native policy: N=1 when A(Z_1) is false, N=m otherwise; m=1 always returns
one packet. The native mean is B=(X_1+...+X_N)/N. Independence gives

    E[B] - mu = a(1-a)(m-1)/m * (mu_L - mu_H).

Proof: on the first low event the mean is mu_L. On the first high event its
conditional mean is (mu_H+(m-1)mu)/m. Expand and subtract mu. Thus adaptive
averaging need not estimate the original single-read mean without bias.
This is not a proof of miscalibration to task golds or a violation of an
explicit unbiasedness promise by vLLM.

For m=4, equal mixture of binary forecasts (eps,1-eps) and (1/2,1/2),
eps=1/1024, the default entropy threshold0.1 separates them. The original
yes mean is513/2048, native expected yes is2571/16384, bias=-1533/16384
(about -9.36 percentage points). All coordinates are positive. These are
an analytical packet law, NOT observed model frequencies. Mirror the vectors
for the opposite sign. With m=1 or a in{0,1} the bias is zero.

## Classical no-extra-read correction

On N=1 return X_1. On N=m>1 let I={i<=m:A(Z_i)} (nonempty because1 is in I)
and return T=sum_{i in I}X_i/|I|. Use the GLOBAL predicate on each complete
packet, not a different selection set for each question. Each question's
probabilities remain a convex average of valid probability vectors.

Let S consist of N and the unordered multiset of the observed packets. On
N=1 the first packet is known. On N=m>1 exchangeability implies that every
permutation compatible with a high first packet has equal conditional
weight. Every eligible indexed occurrence appears first equally often, even
when packet values repeat. Hence T=E[X_1|S]. Conditional expectation and
Jensen yield E[T]=mu and E[ell(T,y)]<=E[ell(X_1,y)] for every fixed y and
convex loss with existing expectations. This is the standard stopped-sample
Rao--Blackwell argument. The conditional-order classical control gives the
IDENTICAL estimator; no separating generic algorithm is asserted.

For a>0 and m>1 let Sigma_H=Cov(X|A). On the high branch the number of high
packets is R=1+Binomial(m-1,a). Their values conditional on R are iid from
the high law, so the conditional covariance of T is Sigma_H/R. Low branch
and between-branch means equal those of X_1. The binomial identity

    E[1/R] = [1-(1-a)^m]/(ma)

therefore gives the exact matrix identity

    Cov(X_1)-Cov(T) = [a-(1-(1-a)^m)/m] Sigma_H >= 0.

For m=1 or a=0 the reduction is zero. At a=1 it is(1-1/m)Cov(X).
Squared Euclidean risk falls by the trace of this matrix for EVERY fixed
gold vector y relative to X_1; this does not assert that mu is calibrated.

## Controls and limitations

The native biased B can have SMALLER MSE about mu than T. An unbiased point
estimate is an explicit target, not universal statistical optimality.
The fixed-m mean is unbiased with covariance Cov(X)/m but always costs m
reads. An independent K in{1,m} with P(K=m)=a has the same expected count
1+(m-1)a and covariance (1-a+a/m)Cov(X). Knowing a is an oracle advantage;
retain favorable and unfavorable comparisons. Pilot splitting is classical:
use the first read only to choose the count, then average independent new
reads, at an extra read relative to the original schedule. None is excluded
merely for having a better variance or semantic score.

No corrected standard-error or confidence-interval formula is provided.
The native stderr must not be reused for T, whose effective count and
mixture law differ. Failure-conditioned inference, adaptive changes to the
prompt/thought/template, dependent seeds or extra quality-dependent selection
do not inherit the iid theorem. A replay of deterministic stubs verifies the
source controller and request accounting, not these statistical hypotheses.

## Whole operation and costs

Leave the native stopping/controller/requests unchanged and replace ONLY
the successful aggregation. Thus every actual request/seed and server status
can be retained, with O(Nd) predicate/accumulator work and O(d) extra working
memory for d returned probability coordinates. Entropies already exist in
each packet; no logit, grammar mass or additional forward is required for the
correction. Existing packet storage and serialization remain charged.
Neither unbiasedness nor this accounting is a measured latency advantage.
The controller's finite-label templates are a regular structured-output case;
there is no new CFG algorithm, decoder law or trained dJev model here.
