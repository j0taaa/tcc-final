# V1 — Bounded exact-rational audit, frozen before code

No model/import/neural head/training/dataset/timing study. New standalone
Fraction reference and independent oracles, no mutable prior-attempt imports.
Commit source BEFORE its one execution; preserve all failures/statuses.

1. K=3..8. For each use distinct q in {1/(K-1),2/(K-1),1/4,1/2,3/4,
   (2K-3)/(2K-2)} lying strictly between0 and1. Enumerate coarse subsets;
   verify nonnegative mass,total1, ALL one/two Bernoulli marginals. Independently
   enumerate ALL feasible moment-polytope vertices with supports of size<=3
   from0..K, solving the three linear moment equalities exactly. For EVERY
   j=0..K verify the candidate avoidance equals the largest vertex value.
2. For each same K/q cell, check32 fixed rational interior/boundary CDF vectors.
   Candidate coefficient-DP CDF must equal direct full-subset enumeration,
   dominate the independent product, and have product one/two projections.
   No sampling/selection of favorable vectors; generate the documented fixed
   modular pattern from {0,1/8,a/2,a,(1+a)/2,7/8,1}.
3. K=3, q=1/2, finite root gridQ=16, horizon3 with forced EOS at3. Four
   private adaptive kernel families, p1=(1+(i+family)%3)/4; p2 is1/4 or3/4
   according to the first private fair nonEOS letter (reverse for odd family).
   Conditional nonEOS letters A/B are fair. Enumerate the entire coarse/root/
   private-path joint law (two private bits per row). Compare every individual
   word probability and every pair's joint word probabilities to a SEPARATE
   recursive Markov tree enumeration. Compare full maximum-round CDF to iid
   and retain the differing full three-way law. No approximation tolerance.
4. Constructed two-point stopping family, K in{3,4,8,16,32,64}, r in{2,3}
   withr<K, H in{2,32,1024}. Compute exact rational expected maxima and ratios;
   retain all cases. Label constructed, not a real-model benchmark. Check
   the r=2 rare-tail identity at heterogeneous rational S_i<=1/(K-1).
5. Preserve the adverse K3 cost min(N,2): candidate3/2 > iid11/8. Also preserve
   all-one clocks' average Bernoulli-score variance inflationK, separating
   this relaxed-contract control from the pairwise-independent candidate.
6. Same-contract classical affine-field clocks: K3,Q17, root_i=(A+iB)%17,
   A,B independent uniform0..16. Enumerate all18^3 threshold grids and all
   17^2 root outcomes; retain first lexicographic cases where this control's
   CDF is BELOW or ABOVE iid, and where it is ABOVE the candidateq=1/2 CDF.
   Do not claim universal dominance against this legitimate control.

Record source/protocol hashes, actual producer/full Git/runtime, exact case/
coordinate counts and direct exit. Diagnostic elapsed is not a performance
comparison. A PASS validates these finite instances only. It does not prove
priority, full compiler/LLM integration, useful real stopping variability or
the positive user goal. Before neural work, reassess all eight criteria and
freeze actual input-only sources/model/controls/full-cost metrics and gates.
