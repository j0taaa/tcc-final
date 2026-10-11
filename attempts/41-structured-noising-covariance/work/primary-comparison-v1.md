# Primary predecessor: masked-diffusion training variance

[Mengni Jia et al., Bringing Stability to Diffusion, current v2,2026-05-21](https://arxiv.org/html/2511.18159v2),
HTML SHA256356d37a5e1aded804c8bdcc6ad04d250ecaed6ede45c4a15db8ae9cd0c27ad88.
Actually read introduction/related work, Sections3.1.1--3.1.3/3.2.1--3.2.2,
AppendixA.3 gradient/loss distinction and complete result-table discussion.
OpenReview PDF/forum challenge browser access; do not claim full PDF reading.

They already propose P-POTS importance timestep sampling and MIRROR
complementary masks, discussing score/loss variance and structured-data
syntax eligibility. MIRROR preserves marginals and assumes useful negative
loss correlation for its half-variance comparison; complementarity alone
does not prove negative covariance of every nonlinear loss/gradient. They
explicitly distinguish gradient from loss variance and report limitations
of their observed variance proxy. Their structured-data/noising focus is a
DIRECT predecessor, not peripheral background. The claim that changing a
mask sampler or adding CFG metadata is novel is unavailable.

A41 must compare their actual operation, keep importance weights and source
noise intact, include fixed-time and whole-time effects, and separate same-
example from different-data controls. Its proposed universal Loewner order
is elementary from A39's scalar law; no independent novel theorem is claimed
for that lift. The possible advance is the query frontier/cheap implementation
with useful gradient/score geometry. Specific priority remains unresolved.
