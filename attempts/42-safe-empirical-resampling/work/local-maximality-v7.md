# Why a locally certified six-pool repair cannot give a large multiclass gain

Let J4(r) be the conditional class law of C4 on a uniform four-subpool of
the six-source pool, with anchor retained. Consider ANY symmetric conditional
joint law J(r) with the same marginal r/6, requiring the LOCAL covariance
gain D(r)=J4(r)-J(r) to be positive semidefinite for every count profile r.
This local certificate is a sufficient condition, not necessary for global
domination after averaging IID pools. It must not restrict practical controls.

If a class appears at most twice, J4(r)_ii=0. Nonnegativity of J(r)_ii
implies D(r)_ii<=0; positive semidefiniteness forces D(r)_ii=0 and its
entire row/column zero (the two-coordinate principal minors force this).
Both laws have the same marginal, so D(r)*1=0. Unless r=(3,3), at most
ONE class has count above two. All other rows are zero, and the zero row
sums force the last row zero. Thus D(r)=0 for those ten profiles.

At r=(3,3), a symmetric two-class joint law with marginal(1/2,1/2) is
determined by its diagonal q>=0. J4's diagonal is1/10. The maximal PSD
gain is achieved at q=0, exactly H6. Hence H6 is the maximal refinement
under this LOCAL certificate, for every original distribution and target.
Symmetrizing an asymmetric joint law leaves the scalar pair-mean covariance
unchanged, so asymmetry cannot evade this argument for that operation.

This proves a limitation of the proposed conservative repair, not a lower
bound for every universal six-query sampler. Globally averaged designs may
trade gains/losses across profiles. The fixed blend tried to do that and
was refuted exactly in blend-erratum-v7.md. Do not promote the small H6
multiclass improvement as the user's requested substantial contribution.
