"""Classical deterministic JSON stack expansion, exact weights and strong guards.

Different inference kernel from the CFG forest. Same contextual lexical sums,
bidirectional lexical trimming, fixed frame and original-token law. Explicit
stacks may be exponentially numerous; no artificial small-state ceiling.
"""

from bisect import bisect_right
from fractions import Fraction
from math import prod
from time import monotonic

from mwpc_exact.cfg_posterior import CompilationLimit

from .forest import coaccessible_layers
from .lexer import NUMBER, OUT, STRING, finish
from .posterior import Posterior, class_weights, lift_marginals


def depth_effect(word):
    height = low = high = 0
    for terminal in word:
        height += 1 if terminal in (0, 2) else -1 if terminal in (1, 3) else 0
        low, high = min(low, height), max(high, height)
    return height, low, high


def consume(stack, word):
    """LL(1) JSON terminal recognition, without the forest's CNF normalizer."""
    for terminal in word:
        if stack and stack[0] == "V" and STRING <= terminal <= NUMBER:
            stack = stack[1:]
            continue
        while stack and isinstance(stack[0], str):
            head, rest = stack[0], stack[1:]
            if head == "V":
                body = (
                    (terminal,)
                    if STRING <= terminal <= 10
                    else ((2, "I", 3) if terminal == 2 else (0, "M", 1) if terminal == 0 else None)
                )
            elif head == "I":
                body = () if terminal == 3 else ("V", "MI")
            elif head == "MI":
                body = (5, "V", "MI") if terminal == 5 else () if terminal == 3 else None
            elif head == "M":
                body = () if terminal == 1 else (STRING, 4, "V", "MM")
            elif head == "MM":
                body = (5, STRING, 4, "V", "MM") if terminal == 5 else () if terminal == 1 else None
            else:
                raise RuntimeError("unknown predictive grammar symbol")
            if body is None:
                return None
            stack = (*body, *rest)
        if not stack or stack[0] != terminal:
            return None
        stack = stack[1:]
    return stack


class StackPrepared:
    def __init__(
        self,
        table,
        canvas,
        *,
        max_edges,
        max_cells,
        max_terms,
        timeout_seconds,
        max_depth=None,
        track_overflow=False,
    ):
        if max_depth is not None and (type(max_depth) is not int or max_depth < 0):
            raise ValueError("depth bound must be a nonnegative integer or None")
        if track_overflow and max_depth is None:
            raise ValueError("overflow tracking requires a finite depth bound")
        self.max_depth = max_depth
        self.table, self.canvas, self.kind = table, tuple(canvas), "local"
        self.members, self.layers, self.arcs = {}, [((OUT, ("V",)),)], []
        deadline = monotonic() + timeout_seconds
        allowed = coaccessible_layers(table, canvas, deadline=deadline)
        memo, requirements, edges, nodes = {}, {}, 0, 1
        peaks = (
            tuple(depth_effect(group[2])[2] for group in table.groups)
            if max_depth is not None
            else ()
        )
        self.overflow_arcs = [] if track_overflow else None
        suffix_terms, suffix_closes = [0] * (len(canvas) + 1), [0] * (len(canvas) + 1)
        suffix_terms[-1] = 1  # possible final NUMBER flush; never a closing delimiter
        for p in reversed(range(len(canvas))):
            words = [
                table.groups[g][2]
                for q in allowed[p]
                for g in (
                    table.by_state[q] if canvas[p] is None else (table.by_token[q][canvas[p]],)
                )
                if g >= 0 and table.groups[g][1] in allowed[p + 1]
            ]
            suffix_terms[p] = suffix_terms[p + 1] + max(map(len, words), default=0)
            suffix_closes[p] = suffix_closes[p + 1] + max(
                (sum(x in (1, 3) for x in word) for word in words), default=0
            )
            if monotonic() > deadline:
                raise CompilationLimit("suffix preparation deadline; mass unresolved")
        for p, fixed in enumerate(canvas):
            targets, layer_arcs, layer_overflows = {}, [], []
            for q, stack in self.layers[-1]:
                grouped, overflows = {}, []
                height = sum(x in (1, 3) for x in stack) if max_depth is not None else 0
                if q not in allowed[p]:
                    layer_arcs.append([])
                    if track_overflow:
                        layer_overflows.append([])
                    continue
                groups = table.by_state[q] if fixed is None else (table.by_token[q][fixed],)
                for gid in groups:
                    if gid < 0:
                        continue
                    _, target, word, members = table.groups[gid]
                    if target not in allowed[p + 1]:
                        continue
                    exceeded = max_depth is not None and height + peaks[gid] > max_depth
                    if exceeded and not track_overflow:
                        continue
                    key = stack, word
                    if key not in memo:
                        memo[key] = consume(stack, word)
                    after = memo[key]
                    if after is None:
                        continue
                    # Safe necessary suffix conditions, not guessed depth caps.
                    if after not in requirements:
                        requirements[after] = (
                            sum(type(x) is int or x == "V" for x in after),
                            sum(x in (1, 3) for x in after),
                        )
                    needed_terms, needed_closes = requirements[after]
                    if needed_terms > suffix_terms[p + 1]:
                        continue
                    if needed_closes > suffix_closes[p + 1]:
                        continue
                    if exceeded:
                        overflows.append((target, needed_closes, gid))
                        continue
                    state = target, after
                    index = targets.get(state)
                    if index is None:
                        if nodes >= max_cells:
                            raise CompilationLimit("explicit stack state budget; mass unresolved")
                        index = len(targets)
                        targets[state] = index
                        nodes += 1
                    grouped.setdefault(index, []).append(gid)
                    self.members[p, gid] = (fixed,) if fixed is not None else members
                    if len(memo) % 128 == 0 and monotonic() > deadline:
                        raise CompilationLimit("explicit stack deadline; mass unresolved")
                outgoing = [(b, tuple(gids)) for b, gids in grouped.items()]
                edges += len(outgoing) + len(overflows)
                if edges > min(max_edges, max_terms):
                    raise CompilationLimit("explicit stack arc budget; mass unresolved")
                layer_arcs.append(outgoing)
                if track_overflow:
                    layer_overflows.append(overflows)
            self.arcs.append(layer_arcs)
            if track_overflow:
                self.overflow_arcs.append(layer_overflows)
            self.layers.append(tuple(targets))
            memo.clear()  # past-layer parser transitions need not occupy memory
            requirements.clear()
            if monotonic() > deadline:
                raise CompilationLimit("explicit stack deadline; mass unresolved")
        self.accepting = tuple(
            finish(q) is not None and consume(stack, finish(q)) == ()
            for q, stack in self.layers[-1]
        )
        # These prefixes may have no bounded completion but a positive deep tail.
        if track_overflow:
            self.prefix_layers, self.prefix_arcs = self.layers, self.arcs
        # Classical backward trimming also applies to the grammar-stack DAG.
        # Retain all valid paths, not only a witness or nonzero model weights.
        live = [set() for _ in self.layers]
        live[-1] = {i for i, accepted in enumerate(self.accepting) if accepted}
        for p in reversed(range(len(self.arcs))):
            live[p] = {
                a
                for a, outgoing in enumerate(self.arcs[p])
                if any(b in live[p + 1] for b, _ in outgoing)
            }
        # Keep the initial zero-mass state so beta[0][0] remains well-defined.
        live[0].add(0)
        mappings = [{old: new for new, old in enumerate(sorted(layer))} for layer in live]
        trimmed_arcs, used_members = [], set()
        for p, layer in enumerate(self.arcs):
            kept = []
            for a in sorted(live[p]):
                outgoing = [(mappings[p + 1][b], gids) for b, gids in layer[a] if b in live[p + 1]]
                used_members.update((p, g) for _, gids in outgoing for g in gids)
                kept.append(outgoing)
            trimmed_arcs.append(kept)
        self.layers = [
            tuple(layer[i] for i in sorted(live[p])) for p, layer in enumerate(self.layers)
        ]
        self.accepting = tuple(self.accepting[i] for i in sorted(live[-1]))
        self.arcs = trimmed_arcs
        self.members = {key: value for key, value in self.members.items() if key in used_members}
        self.retained_nodes = sum(map(len, self.layers))
        self.retained_edges = sum(len(outgoing) for layer in self.arcs for outgoing in layer)
        self.graph_nodes, self.graph_edges = nodes, edges


class StackPosterior:
    def __init__(self, prepared, weights, *, sums=None):
        if weights.vocabulary_size != prepared.table.adapter.vocabulary_size:
            raise ValueError("weights changed original vocabulary")
        if len(weights.canvas) != len(prepared.canvas):
            raise ValueError("weights changed physical slots")
        if any(t is not None and t != weights.canvas[p] for p, t in enumerate(prepared.canvas)):
            raise ValueError("weights changed initial fixed original frame")
        self.prepared, self.weights, self.cdf = prepared, weights, {}
        sums = class_weights(prepared.table, weights) if sums is None else sums
        self.leaf = {
            (p, g): sum(sums[p][cid] for cid in prepared.table.local_to_class[g])
            for p, g in prepared.members
        }
        self.beta = [[0] * len(layer) for layer in prepared.layers]
        self.beta[-1] = list(map(int, prepared.accepting))
        self.arc_weights = [
            [[sum(self.leaf[p, g] for g in gids) for _, gids in outgoing] for outgoing in layer]
            for p, layer in enumerate(prepared.arcs)
        ]
        for p in reversed(range(len(prepared.arcs))):
            for a, outgoing in enumerate(prepared.arcs[p]):
                self.beta[p][a] = sum(
                    weight * self.beta[p + 1][b]
                    for (b, _), weight in zip(outgoing, self.arc_weights[p][a], strict=True)
                )
        self.total = self.beta[0][0]
        self.mass = Fraction(self.total, prod(weights.denominators))
        if not 0 <= self.mass <= 1:
            raise RuntimeError("stack probability outside [0,1]")

    def sample(self, rng):
        if not self.total:
            raise ValueError("zero_valid_mass")
        tokens, state = [], 0
        for p, layer in enumerate(self.prepared.arcs):
            outgoing = layer[state]
            target, gids = outgoing[
                Posterior.choose(
                    [
                        weight * self.beta[p + 1][b]
                        for (b, _), weight in zip(outgoing, self.arc_weights[p][state], strict=True)
                    ],
                    rng,
                )
            ]
            gid = gids[Posterior.choose([self.leaf[p, g] for g in gids], rng)]
            fixed = self.weights.canvas[p]
            if fixed is not None:
                token = fixed
            else:
                key = p, gid
                if key not in self.cdf:
                    members = self.prepared.members[key]
                    cumulative, total = [], 0
                    for t in members:
                        total += self.weights.at(p, t)
                        cumulative.append(total)
                    self.cdf[key] = members, cumulative
                members, cumulative = self.cdf[key]
                token = (
                    members[0]
                    if len(members) == 1
                    else members[bisect_right(cumulative, rng.randrange(cumulative[-1]))]
                )
            tokens.append(token)
            state = target
        return tuple(tokens)

    def marginals(self):
        if not self.total:
            raise ValueError("zero_valid_mass")
        alpha, coefficients = [1], {key: 0 for key in self.prepared.members}
        conservation = [0] * len(self.prepared.canvas)
        for p, layer in enumerate(self.prepared.arcs):
            following = [0] * len(self.prepared.layers[p + 1])
            for a, outgoing in enumerate(layer):
                if not alpha[a]:
                    continue
                for (b, gids), weight in zip(outgoing, self.arc_weights[p][a], strict=True):
                    for gid in gids:
                        coefficients[p, gid] += alpha[a] * self.beta[p + 1][b]
                    following[b] += alpha[a] * weight
            alpha = following
        for key, coefficient in coefficients.items():
            conservation[key[0]] += self.leaf[key] * coefficient
        return lift_marginals(
            self.prepared,
            self.weights,
            self.leaf,
            coefficients,
            self.total,
            fixed_conservation=conservation,
        )
