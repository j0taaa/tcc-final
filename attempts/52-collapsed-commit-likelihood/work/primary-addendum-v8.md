# V8 — Additional primary reading while the GPU is occupied

2026-10-16, AFTER runner freeze fb9b763 but BEFORE any V8 pretrained call.
No capture contract/source changes, updates or human review. PDF SHA256/bytes
are in evidence/stopped-foundation-v8-final/new-primary-sources.json. Narrow
reading scopes below do not claim whole-paper verification or priority.

- [Planner Aware Path Learning v1](https://arxiv.org/html/2509.23405v1),
  Sections3.1--3.4 and AppendixA.4.1, equations4--5 and31--32: the effective
  transition explicitly marginalizes the discarded proposal, including
  subset-valued planners. This is a DIRECT antecedent, beyond generic RB.
  A52 cannot claim to introduce visible-transition marginalization. Its
  possible distinction is a tractable grammar-conditioned, variable-prefix
  readout for the declared restricted policy, implemented with classical
  weighted inference. That distinction still needs useful own evidence.
  Practical PAPL replaces difficult corrections/path simulation with weighted
  cross entropy; this is a competent training alternative, not an erroneous
  implementation of A52 or a baseline to dismiss for using another objective.
- [Adaptive Order Policies v1](https://arxiv.org/html/2606.00295v1),
  Sections2.2--2.3,3 setup and AppendixC: a policy can be trained on a frozen
  denoiser using supervised per-position cross entropy, without downstream
  RL rollouts. Joint training adds ordinary denoising loss and detaches the
  opposite parameter block. AppendixC relates the approximation to PAPL's
  effective-planner term. Such cheap supervised policy adaptation is an
  obligatory behavioral/training control whenever labeled data are used;
  REINFORCE alone is insufficient. No numerical results are inherited.
- [Learning Unmasking Policies v4](https://arxiv.org/html/2512.09106v4),
  Sections3.1--3.3 and AppendixC.1 EOS paragraph: Bernoulli policies,
  no-progress fallback caveats, frozen-model learning and wasted work after
  EOS were already studied. Proper termination is not A52 novelty. Their
  greedy-token training has a different transition law from positive-
  temperature grammar-conditioned proposals; do not identify the contracts.
- [Liu et al.2019](https://proceedings.mlr.press/v97/liu19c/liu19c.pdf),
  Sections2--3 including Propositions1--2: partial exact summation plus
  conditional-tail sampling, standard conditional-variance decomposition and
  equal-evaluation minibatching comparisons are established antecedents.
  This extends the earlier excerpt-only reading, not a whole-paper audit.

The bounded V8 resource/signal screen is unchanged. Even a positive screen
would leave own sufficient distinction, complete-cost variance, useful policy
updates and strong independent behavioral confirmation unresolved. No new
implementation/measurement branch is opened merely by these readings.
