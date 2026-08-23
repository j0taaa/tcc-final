# Architecture

## Boundary principle

The pinned EPIC submodule is a reproducible baseline, not the working source tree. New logic is developed in this repository and integrated through adapters. This avoids silently changing a baseline while the exact method is still being verified.

## Layers

1. `src/mwpc_exact/types.py`: theorem-facing API contracts and statuses.
2. `src/mwpc_exact/reference/`: transparent Python CKY/DAG solvers and exhaustive oracles.
3. `crates/mwpc_parser/`: optimized Rust weighted CFG-on-DAG parser, created only after the Python correctness gate.
4. `crates/mwpc_parser_py/`: thin PyO3 conversion layer.
5. `src/mwpc_exact/`: finite token support, tokenizer adapter, EOS/PAD product construction, certificate validation and orchestration.
6. `src/mwpc_exact/epic_adapter/`: model-loop and baseline integration without editing the submodule.
7. `experiments/`: reproducible offline and end-to-end evaluation drivers, created in later milestones.

## Data flow

```text
dLLM logits + finite canvas + candidate policy
                     |
                     v
          weighted token-slot lattice
                     |
        token emission / lexical interface
                     |
                     v
            weighted terminal DAG + CFG
                     |
                     v
           max-plus CFG-on-DAG parser
                     |
                     v
 witness path + token IDs + selected proposals + score
                     |
                     v
          independent certificate validator
```

## Baseline policy

The execution interface must eventually support `serial`, `epic` and `exact`. All three receive the same recorded canvas, proposal set and weights in offline comparisons. The exact method may be slower; correctness and the exactness scope must never be weakened to hide overhead.
