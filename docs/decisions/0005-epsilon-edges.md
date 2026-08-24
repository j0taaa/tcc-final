# ADR 0005: Weighted epsilon edges in terminal DAGs

- Status: Accepted
- Date: 2026-08-23

## Context

Tokenizer and lexical constructions may need graph transitions that emit no
grammar terminal. Treating epsilon as a normal terminal would change the
language, while allowing the max-plus parser to relax epsilon transitions
implicitly would obscure termination and certificate provenance.

## Decision

The external `WeightedTerminalDAG` accepts an explicit `EpsilonEdge` type.
`None`, an empty string, and sentinel integers are not epsilon labels. The core
CFG-on-DAG parser accepts only `TerminalEdge` and raises
`EpsilonNormalizationRequired` if an epsilon edge reaches it.

Before parsing, `normalize_epsilon_edges`:

1. validates acyclicity over terminal and epsilon edges together;
2. computes maximum-weight epsilon-only paths for every reachable endpoint
   pair in topological order;
3. saturates each terminal edge with every compatible leading and trailing
   epsilon closure;
4. records the complete ordered original-edge path for every generated edge;
   and
5. records the best start-to-final epsilon-only path separately.

For fixed endpoints, two epsilon-only paths emit the same empty string and
have exactly the same possible left and right graph contexts. Under max-plus,
the lower-weight path therefore cannot improve an optimum and is safely
dominated. Keeping only the maximum-weight closure path is exact. Equal
weights use the lexicographically smallest stable edge-ID sequence solely as
a deterministic tie-break; only weight is theorem-level.

The normalized graph never contains epsilon edges. A winning normalized path
is expanded back to its ordered original edge IDs before it is certified. The
objective is re-summed from those original edges, the emitted terminal string
is independently recognized, and matched proposal IDs must not repeat on one
path. Epsilon-only paths compete with terminal-emitting paths only when the
grammar explicitly derives the empty string.

All graph cycles are rejected before closure, including cycles made only of
epsilon edges. No iterative relaxation or timeout-dependent convergence is
used.

## Consequences

- Epsilon acceptance is explicit and cannot be confused with an empty label.
- Closure cannot duplicate an epsilon edge's reward within a reconstructed
  path.
- The parser remains a terminating epsilon-free dynamic program.
- Saturation can enlarge the graph; performance optimization is deferred
  until after differential correctness gates.
- The public token-level result remains the responsibility of the later
  finite-lattice layer; M4 certificates are graph-local and never invent token
  IDs.
