# Primary reading and novelty limits before code

2026-10-17. Limited reading scopes, not a systematic priority review.

- Original Koskela/Karvonen/Latuszynski/Spano, arXiv2510.01941v2,
  1September2026: abstract, introduction, Theorem2/Remark3, ALL Section4 and
  Section5 read. Non-adaptive bounded debiasing and implementation difficulties
  are explicit prior work. Their smoothness comment concerns THEIR estimator;
  do not present our different positive-mixture construction as refuting it.
  No claim that non-adaptivity or smooth-factory existence is new.
  https://arxiv.org/html/2510.01941v2
  PDF260511 bytes, SHA256
  85bc6a2ec6b57416f3b492bb6d45d5fe0cd5353061f77f95ac2a946cb95bca18.
- Original Lee/Doucet/Latuszynski, arXiv1407.5770: ALL AppendixC,
  Algorithm11/Proposition15/Corollary4 read. Signed integrands and absolute-
  value importance proposals precede us. The candidate only avoids unknown
  function-value normalization via a supplied smooth residual envelope; no
  invention of the general sign-problem/importance mechanism is claimed.
  https://arxiv.org/html/1407.5770
  PDF577479 bytes, SHA256
  5359ee8c7b9fe5ea2e79840e461faff3e35c7c276b71fdaa3bc679384df17392.
- Original Morina2021 thesis, Extending the Bernoulli Factory to a Dice
  Enterprise: Section2.4,2.4.1/Proposition2.5,2.4.2's distinction from
  single-term importance sampling, Remark2.8 and proof of2.5 read. This is a
  direct prior framework for our positive series. Not new debiasing theory.
  https://wrap.warwick.ac.uk/id/eprint/157145/1/WRAP_Theses_Morina_2021.pdf
  PDF1260426 bytes, SHA256
  9c85f7612fdff2115e3cbb366ef9821a459a413cedd061efc039e2b1383d782c.
- Original Sablonniere2004 Section2.2 already read in A67. The n-1 operator
  is classical and is explicitly ADOPTED; A67's withdrawal is unchanged.
  https://arxiv.org/pdf/math/0405033v1
- BernoulliFactory.jl author's current README read: interface and library
  functions, signedEstimate and reference to AppendixC above. This identifies
  a real library operation, not an audit of all its source or a missing-feature
  claim. https://github.com/awllee/BernoulliFactory.jl

Searches for function-query/Peano/Taylor/control-variate factory constructions
did not settle specific priority. Supplemental Peano/Taylor bounds and general
importance sampling are close antecedents. A mathematical query-count cap is
only a candidate useful specialization until comparisons/full cost establish
more; keyword absence is not a novelty certificate. No contacts or submission.
