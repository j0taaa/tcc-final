# Empirical rejective coupling: conditional theorem, unconditional CONJECTURE

Fix a source of M known addresses with unknown categorical labels. Draw a
uniform distinct B-pool, retaining its uniform first source literally.
Let p_i=r_i/B be EMPIRICAL positive class proportions. All labels are known
in this pool, not in the original source. Compare equally competent classical
full/lazy pivotal and rejective mechanisms; no novel principle is assumed.

If max p_i >=1/2, let h be a largest class and set J_hi=J_ih=p_i (i!=h),
J_hh=2p_h-1, all other entries zero. If max p_i <1/2, the maximum-entropy
zero-diagonal coupling has J_ij=a_i a_j (i!=j), J_ii=0, positive a with
a_i(A-a_i)=p_i, A=sum a_i. This is a classical conditional-Poisson size2
design, not a new categorical sampling rule. Boundary cases are explicit.

Keep the first original source X. Given its class i choose a companion class
with probabilities J_ij/p_i. Choose an original source uniformly in that
class, excluding X when j=i. The full empirical raw-source marginals are
uniform and every atom diagonal is max(0,2r_i/B-1), the Frechet minimum.
Same-class selection is possible only for a majority class with enough raw
sources, so no forced raw clone or token/latent-alias collapse occurs.

Conditional categorical covariance is negative semidefinite. For the
majority star, on centered class scores sum p_i f_i=0 its quadratic form
is -f_h^2. For the rank-one off-diagonal matrix J=aa^T-diag(a^2), inertia
has exactly one positive direction; after congruence by diag(p)^(-1/2),
sqrt(p) is the eigenvector of eigenvalue1. Subtracting its outer product
leaves all other eigenvalues negative. Lifting within classes adds only
zero or nonpositive within-class covariance. These are standard spectral
consequences, not a new negative-dependence principle.

The marginal target after averaging the uniform pool is the original
uniform source. Atom risk attains the all-budget hypergeometric frontier
g_B(M,t), independent of the unknown original class probabilities. That
is the A41/A39 written opacity frontier, NOT every transparent-noising lower
bound. Odd/even atom identities remain; arbitrary-score safety is separate.

UNPROVED: averaging the random pool yields a negative-semidefinite FULL
original-source covariance for every original class map and arbitrary score.
The pool mean itself fluctuates; conditional negativity alone proves no such
statement. Check the coarse class matrix E_pool J - pp^T against every class
score. Within each original class, exclusion of the identical raw source
gives a nonpositive residual component. A positive coarse eigenvalue with
certified arithmetic refutes the proposed universal extension. Do not call
a finite numerical absence of counterexamples a proof or publication result.

The maximum-entropy root solve can involve irrational weights. A finite
floating prototype searches for obstructions only, not exact sampling, exact
gradient variance or measured dLLM improvement. No current actual score can
determine the classifier. All first/source/teacher/solver/bit/NN costs count.
