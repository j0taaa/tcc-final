# V7 addendum — Original head softmax and variable occupancy, before code

This clarifies prefix-anchor-v7.md's required TRUE head chain rule. Its eight
criteria/limited oracle scope remain unchanged. No new model/update/result.

Let mu_iv and nu_iv be prior and action-conditional active prefix occupancy
counts; row sums mu_i* and nu_i* can differ. The score with respect to formal
independent log(c_iv) factors is D_iv=nu_iv-mu_iv. But c is an ORIGINAL full-V
softmax, so its actual model-logit score contribution is

    D_iv - c_iv * sum_u D_iu.

For gates h_iv=alpha_i+beta*log(c_iv)-log(tau), let J_iv be their logodds score
from V7. The additional contribution is

    beta * (J_iv - c_iv * sum_u J_iu).

Sum both, with r treated independent of the head. If r itself depends on c,
its chain must also be added. Fixed original IDs have constant singleton
factors and no active gate derivative. Unlike fixed-length unconditioned
words, prefix occupancy is not always1; dropping the row-sum term can bias
the gradient. This is ordinary softmax differentiation, not new theory.

The independent minimal oracle should differentiate full rational prefix/
anchor/mask masses with dual numbers, recomputing ORIGINAL row normalization
and confidence gates, and compare to these projected adjoints. A finite
numeric difference or detached confidence must not replace that check.
