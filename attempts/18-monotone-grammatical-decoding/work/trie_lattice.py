"""Known proper-prefix token DAG; private closing arcs preserve original IDs.

Same representation as maintained CFG posterior, for best-derivation queries.
All supported ordinary tokens emit >=1 byte, so no epsilon arcs are necessary.
"""

from collections import defaultdict
from math import fsum, ldexp

from mwpc_exact.types import TerminalEdge, WeightedTerminalDAG


def trie_lattice(state, canvas, proposals):
    rewards = defaultdict(list)
    for j, (p, token, _) in enumerate(proposals):
        rewards[p, token].append((j, ldexp(1.0, len(proposals) - j - 1 - 1074)))
    edges, closes = [], {}
    vertices, boundary = 1, 0
    for p, row in enumerate(state.support.rows):
        words = {
            t: state.tokenizer_adapter.emissions[t]
            for t in row
            if (canvas[p] is None or canvas[p] == t)
            and state.tokenizer_adapter.emissions[t] is not None
        }
        prefixes = sorted(
            {word[:i] for word in words.values() for i in range(1, len(word))},
            key=lambda x: (len(x), x),
        )
        nodes = {b"": boundary}
        for prefix in prefixes:
            nodes[prefix] = vertices
            vertices += 1
            edges.append(TerminalEdge(len(edges), nodes[prefix[:-1]], nodes[prefix], prefix[-1]))
        end = vertices
        vertices += 1
        for token, word in words.items():
            parts = rewards[p, token]
            edge_id = len(edges)
            edges.append(
                TerminalEdge(
                    edge_id,
                    nodes[word[:-1]],
                    end,
                    word[-1],
                    weight=fsum(w for _, w in parts),
                    matched_proposal_ids=tuple(j for j, _ in parts),
                    weight_terms=tuple(w for _, w in parts),
                )
            )
            closes[edge_id] = (p, token)
        boundary = end
    return WeightedTerminalDAG(tuple(range(vertices)), 0, (boundary,), tuple(edges)), closes
