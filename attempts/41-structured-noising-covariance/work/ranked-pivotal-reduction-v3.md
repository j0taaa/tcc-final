# Direct classical reductions before any real-model campaign

2026-10-11. Written BEFORE the comparison oracle/model outputs. These are
mathematical comparison objects, NOT favourable empirical benchmarks.

## Sources actually read

* [Takahasi and Wakimoto1968](https://www.ism.ac.jp/editsec/aism/pdf/020_1_0001.pdf):
  scanned original pp1--4, viewed as images; setup and Eq2.8--2.9. PDF SHA256
  99a42c522a6d5a4130c929df2b766134951cbad25ddcf1618b8dea881b332bf5.
  Ordering-cheap/measurement-expensive and variance decomposition are OLD.
  This paper's perfect-order assumptions are not the imperfect-ranking claim.
* [Chen, Stasny and Wolfe2006](https://academic.oup.com/biometrics/article/62/1/150/7306420):
  original Introduction and Sections2.1--2.3 read, not their entire data study.
  Imperfect ranked-set sampling's iid variance guarantee and binary Neyman
  improvements are explicit predecessors; known/train-estimated allocation
  information cannot be withheld from a competent control.
* [Jafari Jozani and Perron, Antithetic Sampling, author report](https://www.usherbrooke.ca/mathematiques/fileadmin/sites/mathematiques/documents/Recherche/Publications/Rapports_de_recherche/rr64.pdf):
  actual original introduction, Section2 theorem/proof and Section3 inclusion
  law/Theorem3.1 read; not all simulations. SHA256
  8e7a94cb5f672bddf62b79ccc5fd6c6eadb5d7a427c3fe77e3bfe7dfd55ba097.
  Pool-based randomized selection reducing variance is NOT new.
* [Olofsson, Grafstroem and Lundstroem2023, actual v1](https://arxiv.org/html/2305.02446v1):
  Introduction and Sections2/2.1/2.2 read. Their Algorithm1/Eq2 has the
  pivotal update, arbitrary auxiliary distance and cheap iid pool thinning.
  It already composes with importance sampling without evaluating every pool
  trait. NOT a new principle of our work. No full experimental reproduction.
* [Pohjankukka and Heikkonen2026](https://arxiv.org/html/2606.27171v1):
  Introduction, Sections2.2--2.3 and Algorithm1 read. Model-assisted gradient
  correction and its covariance are antecedents. Their global predictor sum
  is not assumed free for a huge implicit corruption source. No measured win
  against their actual implementation or whole experiments.

## A stronger ranked-set control, not only MIRROR

First consider iid source queries (NOT the finite without-replacement source
of A39). Let class probabilities p_i, full-result class means mu_i, global
mu, g_i=mu_i-mu, sum p_i*g_i=0, S2=sum p_i^2,
A=sum p_i^2*g_i*g_i^T, h=sum p_i^2*g_i. Classifier is fixed before sources.

For a fixed ordering of classes, draw two independent pairs. Select the
minimum proxy class from the first pair and maximum from the second; ties
are random or chosen by draw-order, independent of the full result. Evaluate
only those two sources. Randomly orient the selected outputs, so EACH
individual source marginal is the original distribution. Four cheap sources,
two expensive evaluations. Literal original first source need not be retained
by this control; A41's MC scorer does not require that extra restriction.

Put d_i=p_i*(mass strictly above i - mass strictly below i),
D=sum d_i*g_i. Minimum and maximum result means are mu+D and mu-D.
The selected pools are independent. After orientation, full cross covariance
is -D*D^T. Thus its mean covariance is (Sigma-D*D^T)/2 <= Sigma/2 for EVERY
result vector, even if proxy order is unrelated to it. The generic universal
Loewner/iid guarantee in A41 is therefore also available classically.

If the class order is uniform random independently before each pair, then

 B_RSS := -C_RSS = [(1+S2)*A-h*h^T]/3.                  (1)

Proof: write D as a sum of edge vectors
p_i*p_j*(g_i-g_j) with random ordering signs. Disjoint-edge signs have
zero correlation; sharing-vertex signs have correlation +/-1/3. Equivalently
their covariance is (I+incidence^T*incidence)/3. The vertex vector sum is
p_i*g_i because sum p_j*g_j=0. The squared edge sum is S2*A-h*h^T.
Adding the vertex squared sum A gives(1). This is a direct elementary
comparison derivation, not a claimed new ranked-set principle.

The iid four-pool C4 law (A38, also finite-law limit) gives

 B_C4 := -C_C4 = (1-S2)*A+h*h^T.                       (2)

Hence B_C4-B_RSS = [(2-4*S2)*A+4*h*h^T]/3. If S2<=1/2,
C4's covariance is no worse in EVERY projection than this RANDOM-ORDER RSS
control. This condition and order randomization MUST stay explicit.
For three equal classes and sum g_i=0: B_C4=(2/27)*sum g_i*g_i^T,
B_RSS=(4/81)*sum g_i*g_i^T. This is a proof specialization, not model data.

Two necessary objections:

* A good FIXED order can beat C4: equal three classes with scalar results
  (-1,0,1) has B_RSS=16/81 versus B_C4=4/27. Include an order learned from
  development, not only randomized meaningless categories in a benchmark.
* If S2>1/2 the random-order advantage can reverse. For p=(4/5,1/10,1/10)
  and g=(0,1,-1), B_C4=17/2500, B_RSS=83/7500. C4 is worse. No discarded
  case or universal superiority over all RSS configurations.

An independent-pair finite WITHOUT-replacement RSS control is also legitimate.
Its order-dependent D is multiplied by M/(M-1). Equation(1) then receives
the square of this factor; do NOT apply the iid comparison blindly. Sampling
all four sources jointly without replacement is another stronger admissible
control, requiring its actual joint law rather than independence assertions.

## Exact reduction to a symmetrized class-first pivotal pool

Take FOUR distinct source slots as a uniform pool, each inclusion probability
1/2, retain two. Among the three perfect matchings of the slots choose
uniformly one maximizing the number of pairs with identical class keys.
Perform the classical pivotal update on each matched pair: select one element
uniformly from each. This is a class-first special case of the old pivotal
procedure; all inclusion probabilities remain1/2. Finally uniformly orient
the two outputs. No population class mass or inverse sampler is required.

For every unordered four-pool multiplicity pattern:

* 4: uniform selection of two sources in the sole class;
* 3+1: one or two sources from the majority, each with probability1/2;
* 2+2: exactly one from each class;
* 2+1+1: exactly one from the doubled class and one singleton uniformly;
* 1+1+1+1: uniform unordered pair of distinct sources.

These are exactly C4's conditional class and original-source pair laws after
averaging the ordering of the OTHER three pool sources, keeping first source
literal. To retain the first source, use the pivotal pair distribution
conditional on including it (inclusion probability1/2); then orient it first.
This is a distributional conditional construction, not rejection required by
the original implementation. Its companion law matches C4. Source aliases
remain separate slots. For iid pools the same argument concerns DRAW slots,
not deduplication of repeated source addresses.

This reduction means empirical balancing, unknown-mass thinning and the
full four-pool law CANNOT be claimed as an exclusively new invention.
The independent oracle must compare whole original-source joint laws, not
only selected counts or favourable class examples.

## What distinct result can still be investigated

A39's potential contribution is the explicit sharp query frontier and
minimal expected class lookup cost, including adaptive source-address choices
and a first source kept literal: at most4 opaque label queries, robust optimum
for all permitted atoms, worst-placement expectation4-2c2+c3. The same-law
full pivotal pool requires four prepared/classified sources in its direct
form. C4 decides branches after three and sometimes omits the fourth, with
a proved sharp lower bound under A39's information assumptions.

A control is allowed to implement the SAME safe short circuits. If it becomes
the same optimal tree, it is another realization of that theorem, not a
weakened adversary or a competing new joint law. Labels/masses/inverses or
predictor sums available analytically fall outside the opaque-lookup bound.
Whether this sharp cost theorem is new, substantial enough for publication
and practically useful to structured-dLLM scoring remains OPEN.

IMPORTANT interface distinction: A39 queries materialize BOTH payload and
label. A41 can return an UNCLASSIFIED raw mask. Its surrogate-call count is
not bounded by A39's preparation count. `label-cost-v3.md` specifies the
new pool-design operation and separate sharp label bound before a prototype.

## Reassessment of the eight criteria for v3

1. The operation stays fixed-input dLLM noising score/gradient, CFG-valid target.
2. Generic ranked/pivotal balancing is known; only a sharp oracle frontier can
   be the distinctive mathematical protagonist. Its priority is not confirmed.
3. Compare full pivotal same-law, learned-order and random-order RSS, MIRROR,
   analytic/control-variate/importance and extra iid; no broad win asserted.
4. The written laws/cost proof are independent of code; this reduction removes
   a false novelty claim, rather than replacing a comparative benefit with tests.
5. Oracle objects are correctness/reduction checks, NOT dataset performance.
6. Full costs still include all cheap-class work and real neural evaluations;
   a query saving can be a tiny fraction of total time and does not prove20%.
7. An equally good lazy pivotal implementation or inexpensive exact surrogate
   expectation can remove a practical advantage. Those controls remain allowed.
8. Need closest cost/lower-bound priority audit plus a meaningful external
   effect before article promotion. No real model/training was run for A41.
