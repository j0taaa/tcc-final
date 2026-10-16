# A53 primary reading before prototype

2026-10-16. Narrow scopes, not a priority confirmation or human review.

- Yin/Sheng/Zheng, SGLang compressed FSM,2024-02-05:
  https://www.lmsys.org/blog/2024-02-05-compressed-fsm/
  Read Background, jump-forward and tokenization-boundary sections. Grammar
  deterministic spans already skip neural work. Re-tokenization can affect
  later logits; A53 only returns terminally, with no further changed context.
- Mündler/Dekoninck/Vechev2025 v1:
  https://arxiv.org/html/2508.10111v1
  Read4.1/4.3 and discussion of completing aborted outputs. Grammar witness
  extraction/completion is prior work; arbitrary witness completion can
  change functional output, so A53 cannot claim that extraction as novel.
- Liu et al., VoidPadding2026 v1:
  https://arxiv.org/html/2606.17999v1
  Read4.1 Inference Design: EOS termination after every preceding position
  is unmasked is already explicit. A53 must compare against that stopping
  baseline and distinguish semantic absorption before complete first-EOS.
- Nagy et al., ChopChop2025 v1:
  https://arxiv.org/html/2509.00360v1
  Read2.1 and3.3--3.4: semantic completion/realizability and precise versus
  conservative checkers are known. A53's support certificate is an instance
  of semantic reasoning, not the invention of semantic constrained decoding.
- Tempest, CMWQ author-uploaded preprint2026-05-12:
  https://www.researchgate.net/publication/404780660_Certified_Minimal-Work_Quotient_Execution_for_Distribution-Preserving_Large_Language_Model_Serving
  Read author-uploaded abstract and displayed7.2--7.4. Generic quotient
  distribution preservation, singleton grammar bypass and relative minimality
  are explicit antecedents. Do not claim those principles or review status.
- Leroy2003, original author-hosted formalization:
  https://xavierleroy.org/publi/xlcompil-0.1.pdf
  Constant-propagation module11.1 explicitly distinguishes unreachable,
  constant and unknown in a flat domain. The flat analysis itself is classical.

A useful own terminal dLLM application remains unconfirmed. Searches failing
to find an exact match are NOT evidence that none exists. No theorem above
is promoted as new solely because its notation or consumer differs.
