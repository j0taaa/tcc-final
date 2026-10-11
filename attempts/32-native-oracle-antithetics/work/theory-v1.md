# Native sampler oracle coupling — written candidate, v1

No novelty claim is inferred from this proof. The oracle-access bound is
strictly delimited; Bernstein, Fréchet, conditional sampling and stationary
Dirichlet arguments are antecedents. No benchmark or semantic score is used.

## 1. Operation and exact finite law

Let P be ANY probability law on a finite set Omega, including complete native
finite-precision noisy token-ranking rows. A deterministic projection
c:Omega->{0,1} is fixed BEFORE draws. Put p=P(c=1), q=1-p. P is sampled, not
evaluated. All oracle calls below are fresh independent draws from EXACTLY P.

Draw X,Y iid P; retain X literally. If c(X)!=c(Y), return (X,Y). Otherwise
draw Z~P. If c(Z)==c(X), return (X,Y). Otherwise draw W~P and return (X,Z)
when c(W)==c(Z), or (X,Y) otherwise. The W payload is not returned.

This is bounded, not rejection until the opposite class appears. At most
four total oracle draws, including X/Y; no density or p enters the code.
The extra draws do not advance a model or discard ranking tails.

## 2. Marginals and signed energy

Write P0,P1 for conditional laws (empty zero-mass class handled by continuity).
Off-diagonal class probabilities are identical in both directions:

    J01=J10=pq+p²q².

For example, a new 0->1 flow occurs exactly when X,Y in class0 and Z,W in
class1, of mass q²p². Opposite flow has the same mass. Diagonal masses are
J00=q²-p²q², J11=p²-p²q². Thus BOTH class marginals are native p. Within a
class block, returned payloads are independent Pj/Pk: decisions inspect only
classes, and returned Z is independent of X conditional on their classes.
Therefore BOTH full marginals are P. Original aliases/IDs are not merged.

For any real f with finite second moment, let mu_j=E[f|c=j]. Independence
conditional on class blocks gives exactly

    Cov(f(X),f(Y_returned))=-p²q²(mu_1-mu_0)².                 (1)

For any event A with a_j=P(A|c=j), pair coverage consequently is

    Pr(X in A or Y_returned in A)
      =2P(A)-P(A)²+p²q²(a_1-a_0)².                           (2)

Hence universal weak pass@2 dominance and universal nonincrease of mean
variance, strict exactly if 0<p<1 and conditional means differ. No theorem
of semantic correctness, pass@1 improvement or domination over known-p CDF.

Expected AUXILIARY draws are

    (p²+q²)+(p²q+q²p)=1-pq in[3/4,1].                       (3)

The first term triggers Z; the second triggers W. Worst-case two. At p=.5
and A={c=1}, coverage=.8125 versus iid .75. Expected verifier calls under
independent retry pairs that stop after the first success are (2-P(A))/c_A;
in this illustration 24/13 versus2. This is not neural evidence/timing.

## 3. A sharp oracle-budget bound

Competitor class: algorithms do NOT know p, receive at most n iid Bernoulli(p)
bits and external randomness independent of p, leave the FIRST bit B1 as X,
and output Y~Bernoulli(p) for EVERY p in[0,1]. Algorithms may stop early:
pad with unused independent bits to n. Payload/known-density information is
outside this bound. The class-bit theorem even allows inventing output bits,
so restricting to a returned oracle payload does not weaken the bound.

Let M=sum(B_i), and a_m=E[Y|M=m]. Because the conditional bit vector is
uniform over weight-m strings, a_m is independent of p. Marginal preservation
is the polynomial identity

    sum_m binom(n,m) a_m p^m(1-p)^(n-m)=p.

Uniqueness of the Bernstein basis implies a_m=m/n. Also
E[X|M=m]=m/n. Conditional Fréchet then bounds

    Pr(X=1,Y=0|M=m)<=min(m/n,1-m/n).

Consequently every admitted algorithm satisfies

    J10 <= B_n(p):=E[min(M/n,1-M/n)], M~Binomial(n,p).         (4)

This is attained: given m, draw Y using the maximum-disagreement conditional
kernel with BOTH marginals m/n, while leaving B1 unchanged. If payloads are
needed, choose uniformly one of B2..Bn with class Y. The requested class
always exists whenever its transition probability is positive (n>=2).
The returned payload then has its original conditional Pj law.

For n=2 and n=3, B_n(p)=pq: NO universally correct p-blind algorithm with
three or fewer oracle draws improves the pair coverage of c. For n=4,

    B_4(p)=pq+p²q².                                        (5)

Thus the adaptive four-draw operation in1 attains the sharp bound for ALL p
simultaneously, with fewer than one auxiliary draw EXPECTED. This is a bound
on worst-case draws, not optimal expected complexity across all algorithms.
It is not a lower bound on EPIC parsing, dLLM forwards or methods knowing p.

General n trades more sampler work for B_n(p)->min(p,q); n=2r and n=2r+1
have the same bound. This limiting convergence is not an unbounded-budget
algorithm used secretly in the four-draw implementation.

## 4. Adaptive dLLM/CFG consequence

Let a finite-horizon frozen decoder have a genuinely sufficient Markov state
s at phase t. All model/policy/grammar/tokenizer/EOS/rejection-budget choices
are identical across labels. At equal (t,s) couple a fresh selected ranking
row by1; remaining noise rows stay independent. At unequal states use
independent native draws. Phase/ordinal prohibit using the same node twice
within a trajectory. First label keeps every native draw literally. No
global unique-forward cap or physical timer changes the kernel.

Let f be any terminal output score and g_t(s)=E_native[f|s at t]. Conditional
on a selected full ranking R, average over ALL other randomness in this step
to obtain h_t(s,R). Let mu_j(t,s)=E[h_t(s,R)|c_s(R)=j]. The finite martingale
product telescope (conditioning on the paired state before each fresh node)
gives

    Cov(f(final1),f(final2))
      =-sum_t E[1_{s1=s2} p_s²(1-p_s)²(mu_1-mu_0)²].        (6)

Marginals remain the original native whole-trajectory law by induction;
equation1 supplies each local decrement, and unequal-state decrements are0.
Use f=1_A for ANY unknown terminal verifier A to get pass@2>=native iid.
This proof does not assume next logits unchanged after different commitments.
CFG recovery is deterministic/postprocessing of the complete noisy order,
so it is part of h_t, not dropped from the law. FAIL is an output event;
conditioning after dropping FAIL changes the comparison and is not claimed.

## 5. Cost and failure modes

Extra ranking draws require frozen logits, not model calls. A V-ID row uses
O(V) finite arithmetic/storage per draw; the deterministic draw bound adds
at most2 row draws per equal-state encounter. Expected <=1 per such node.
Caching head/keys/classification and CPU/GPU conversion all count. Increased
diversity may increase UNIQUE forwards; equations1--6 cannot bound wall time.
This is useful only if informative class transitions survive the CFG/model
trajectory and the gain pays this full cost. Known-p inverse-CDF antithetics
can give larger gain at less work; report them as competent alternatives,
with their different exactness assumptions. Four complete iid generations
are another cost/quality competitor, not four frozen-head row draws.

The class map may be chosen from logits/lexer BEFORE noise, never gold or
the observed winners. Reordering keys by a sample-dependent classifier can
invalidate the block factorization. A p estimate plugged into a coupling
is not exact marginal preservation. Simply resampling collisions until
opposite changes Y's marginal when p!=.5. Coupling all raw coordinates does
not imply equation1. Tests must find these failures, not merely show JSON.
