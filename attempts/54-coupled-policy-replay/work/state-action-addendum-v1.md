# V1 pre-prototype precision: canonical action and variance counterexample

2026-10-16, before ANY A54 implementation or real-data statistic.

The prefix-work statement identifies actions by their COMPLETE next-state
increment: for fixed s, T(s,a) must be injective on those canonical actions.
If different action records map to the same next state, push K forward to
that state first. Maximizing equality of unnecessarily distinguished action
records is not maximal state reuse. In A52's monotone contract, the newly
fixed original IDs/positions plus deterministic ordinal/control update have
this property. Further equivalence of model inputs can permit more caching;
the theorem does not forbid that stronger comparator.

No semantic-score variance dominance follows from atom agreement. For example,
p=(1/2,49/100,1/100),q=(1/2,1/100,49/100), score f=(0,-1,1). Maximal coupling
with independent residuals puts1/2,1/100,1/100 on the diagonal and48/100 on
(a,b). The difference-of-scores variance is .9984, versus .5392 for independent
sampling. Every marginal remains correct. This is a useful mandatory oracle,
not a claimed benefit or a flaw in the classical maximal-coupling theorem.

The real operation is producing a FIXED predeclared number of rollouts per
configuration with their own laws; marginal score estimates keep their own
sampling law across independent paired replicates. If promoting a claim about
comparison precision, rankings or cost-times-variance, the actual coupled
covariance must be included and this counterexample cannot be ignored.
