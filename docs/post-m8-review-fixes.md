# Post-M8 review fixes

This focused change preserves all completed M7/M8 algorithms and immutable
evidence while tightening the production boundary before M9.

- complete Rust-backed CI now exercises the full suite and normal M6/M7 campaigns;
- adaptive total timeout has hard returned-status semantics;
- exact canvas mutation requires a typed validated result;
- the legacy ordinary-support solver is no longer presented as a peer production API;
- adaptive support is named as first-feasible rather than globally best across K;
- randomized campaigns and evidence generators moved to `mwpc_research`;
- completed M0--M8 details moved to the history archive;
- EOS policy and decoder data contracts were split from their operational modules.

Branch protection was intentionally not changed at the repository owner's request.
