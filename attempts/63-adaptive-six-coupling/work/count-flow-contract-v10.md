# V10 — A classical count-flow reduction and a candidate stopped-work family

2026-10-17. BEFORE new code, LP solve or family observation. All earlier
certificates, controls, cost objections and application gaps remain preserved.

## 1. Eight scientific decision criteria

1. Same opaque original-payload operator, three ALLOWED fixed keys and retained
   literal first; now vary the source cap B. Return the SAME known symmetric
   empirical pair law averaged over iid sources. A real useful downstream
   consumer is still not established; V9's field examples are only leads.
2. Possible own consequence: a nontrivial family of sharp stopped-source-work
   bounds/explicit achievers, instead of only the cap-six constant. Fixed
   empirical antithetics and their all-budget three-class safety are A44
   antecedents, not a new decoder or new theorem claimed here.
3. A stopped law-preserving rule could reduce expensive source calls relative
   to competent full-pool/common-part/rank methods, while giving a cost/diversity
   choice. NO benefit or universal optimum is presumed for higher B. The
   current positive6 result remains separate if this extension fails.
4. Write the full conditional count kernel, a COMPLETE count-flow LP, standard
   Markovization argument and a general compulsory-prefix lower bound before
   solving. A possible3B/4 asymptotic U3 attainment is ONLY A CONJECTURE.
5. Minimal exact proof computation: ALL caps4,5,6,7,8,9,10,11. Freeze source
   first, regress4..7 against known31/9,31/9,386/81,386/81 before new8..11.
   Preserve all statuses. Numerical candidates count only after independent
   exact primal/dual and named-tail operational checks with zero gap.
6. Source queries are optimized, not wall time/whole-dLLM efficiency. Optional
   SciPy remains isolated with existing pins. Preparation, rational bit work,
   state-table memory, RNG, raw payload storage and downstream work are charged.
   V8/addendum's cost objections still apply; no artificial two-output consumer.
7. Count-state optimization is a direct classical reduction. The2009 original
   reverse-martingale paper Section3 already avoids exponential string sets
   through hypergeometric coefficients. Ordinary MDP occupation flows and LP
   duality are known. Finding constants does not prove sufficient novelty.
   Cap-odd work need not equal previous even work merely because laws agree.
8. Need a substantive own family consequence, primary priority audit and
   useful real full-cost operation. No new neural/semantic/training/latency or
   publication claim; no large implementation justified by a correct solver.

## 2. The known target law

For B>=4, counts n0+n1+n2=B, set D_i=max(0,2n_i-B). A symmetric conditional
joint key matrix has diagonal D_i/B and offdiagonal

    H_ij(n)=(n_i+n_j-n_k-D_i-D_j+D_k)/(2B).

Its rows are n_i/B and it is nonnegative. This is A44's known three-class
empirical law; even B also equals the minimum-repeat matching law. At odd B
the final iid-averaged law equals the preceding even law by degree elevation.
Do not assume an odd perfect matching of positions exists.

Given first key0 and nonfirst counts k=n-e0, the conditional partner coefficients
are

    Q0(k)=D0/n0,
    Qj(k)=(n0+nj-nl-D0-Dj+Dl)/(2n0), j!=0.

The target unconditional raw pair law is FIXED here. Unlike the old cap-six
LP, the family lower bound initially concerns exact simulators of this full
ordered pair law, not all possible atom maximizers with an antisymmetric part.
The old broader cap-six/seven lower bounds are not retroactively weakened.

## 3. Standard Markovization by prefix counts is complete

Condition on first key0. For h further draws let k=(k0,k1,k2), sum k=h.
Every named prefix with those counts has the SAME p0^k0 p1^k1 p2^k2 probability.
Consequently its conditional distribution over orders, including the policy's
integrated internal randomization/survival, does NOT depend on unknown p.
Average an arbitrary policy's decisions among surviving histories with each
fixed count. The resulting randomized Markov policy on k preserves, for EVERY
p, stopping/output probabilities and expected work. This is ordinary sufficient-
statistic/occupation-measure reduction, not a new compression principle.

At U3, symmetrize any universal rule by all label permutations. Its expected
work is unchanged and each first-key conditional subproblem has the same
cost. Thus optimizing the first0 count policy lower-bounds the full exact-law
class at U3. A key-only achiever extends to arbitrary raw laws by selecting
a literal NONFIRST representative using keys alone. No density/score side
information is hidden when a practical source actually supplies it.

Write M(k)=h!/(k0!k1!k2!). Let c(k) be probability of still continuing after
depth h conditional on counts; s_j(k) the probability of stopping NOW with j;
a_j(k) probability of having stopped with j by that depth. These are normalized
Bernstein coefficients, not probabilities conditional on reaching the state.
Set c(0)=1,a_j(0)=0; no output is allowed before any nonfirst draw.

For h>=1 put w_l=k_l/h. With missing terms zero, the exact recurrences are

    c(k)+sum_j s_j(k)=sum_l w_l*c(k-e_l),
    a_j(k)=s_j(k)+sum_l w_l*a_j(k-e_l).

All variables are nonnegative. Stops s_j and cumulative a_j are zero if k_j=0:
there must be a nonfirst representative, including for first key0. At h=B-1
set c(k)=0 and a_j(k)=Qj(k). Independent coefficient uniqueness makes these
terminal equalities exactly the universal ordered-law constraints. Each is an
average over ALL tail orders; it does NOT impose Q on each individual tape.

Conversely define reach r(k)=sum_l w_l*c(k-e_l). On reaching k, stop with
j with probability s_j(k)/r(k), continue with c(k)/r(k). Reach-zero nodes
are not visited. By induction this realizes the specified normalized flows;
no unknown probability enters the action rule. This establishes completeness
of the rational LP under the stated information/target contract.

The U3 expected source cost is

    1 + sum_(h=0)^(B-2) sum_(|k|=h) M(k)*3^(-h)*c(k).

There are binom(B+2,3) count states, O(B^3) variables/rows/nonzeros for fixed
three keys. This is arithmetic-operation scaling; rational coefficient/output
bit lengths and solver complexity are separate. Do not claim a new generic
polynomial factory optimizer or polynomial bit complexity from this count.

For any resulting policy optionally average the two mappings of nonfirst
actual keys into labels1/2. This preserves target/U3 cost and makes its total
work symmetric in population masses. A U3 optimum is NOT a minimax work theorem
until the maximum over all p is separately bounded. Record the five original
rational laws as proof checks, not independent benchmark wins.

## 4. A general necessary prefix bound, written without code

Put m=floor(B/2), and consider a prefix of total length n, retained first0.
Let C1,C2 be the counts of the other two keys. If

    C1>=n-m AND C2>=n-m,                                  (1)

NO universal atom-maximizing sampler can stop at this prefix. Completing all
B-n unseen slots with key1 would give that class at least ceil(B/2) occurrences.
Optimal diagonal plus both conditional margins then force every first-not1
tape to return key1. Completing instead with key2 forces key2. The same finite
prefix cannot have any positive stop event satisfying both completions.
Nonnegative Bernstein coefficients make this a tape-level contradiction;
cloning first or auxiliary bits do not avoid it. In particular N>=m+1.

At U3, conditional on the first, Cj is Binomial(n-1,1/3). For fixed0<eps<1/4
take n=floor((3/4-eps)B). If eps*B>=5, its mean exceeds n-m by at least
eps*B/2. Hoeffding and a union bound give

    P(N>n)>=1-2*exp(-eps^2*B/2).

Therefore liminf_(B->infinity) inf_A E_U3 N_A/B >=3/4, and likewise a
minimax lower bound. This uses classical clipping/concentration. It is not
a positive application or a claimed optimal asymptotic constant: a matching
3B/4+o(B) upper construction remains an OPEN conjecture. The finite solves
are only for4..11 and cannot themselves prove an asymptotic assertion.

## 5. Exact implementation/verification gates

Use the existing isolated NumPy2.2.6/SciPy1.15.3 environment. Sparse equality
LP, nonnegative variables, HiGHS-ds60s per cap. Reconstruct proposed primal/
equality dual with denominator<=100000000, rounding numerical magnitudes below
1e-10 to0 BEFORE rational reconstruction. This only proposes a certificate;
every rational row, reduced cost and ZERO exact dual gap must then hold.
Any failure is INCONCLUSIVE, never approximate proof or a discarded case.

An independent stdlib verifier must rebuild count rows/objective without
importing the solver; additionally enumerate ALL3^(B-1) named tail words,
realize the Markov conditional probabilities and verify every terminal-count
output coefficient and U3 mean. Guard1000000 prefix/action steps PER CAP;
failure/refusal is preserved. For larger caps the fixed first0 subproblem is
justified by the written symmetry argument, not mislabeled3^B word coverage.

First run4..7 and require the known exact costs. If those regressions fail,
preserve8..11 as NOT_RUN and correct the model before expanding. If they pass,
execute ALL8..11, including any inconclusive reconstruction. No selecting the
best cap/result to claim generality. Sources/commands/certificates/verification
counts stay separate from old results and from any later operational adapter.
