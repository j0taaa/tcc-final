"""First-stage V4 operations for the preregistered NEGATIVE-only cost audit."""

from fractions import Fraction
from random import Random

import torch

from ..certificate import CounterTable, conditional_error
from ..consumer_v2.query import BoundaryWeights, sample
from .layered_fa_control import LayeredFA
from .prefix_cache import PrefixCache
from .ranking import ranked_commits
from .sparse_fa_control import SparseFA
from .termination import CPUCache, prepare_graph, terminated_graph


def gpu_result(word, confidence, selected, canvas):
    tokens = torch.as_tensor(word, dtype=torch.long, device="cuda")
    marginal = torch.as_tensor(confidence, dtype=torch.float64, device="cuda")
    mask = torch.zeros(len(canvas), dtype=torch.bool, device="cuda")
    mask[list(selected)] = True
    return dict(tokens=tokens, confidence=marginal, commit_mask=mask)


class CPUQuery:
    def __init__(self, method, table, partition, canvas, protocol):
        if method not in ("handoff_cpu", "closed_cpu", "exact_stack_cpu"):
            raise ValueError("unknown first-stage CPU method")
        self.method, self.table, self.partition = method, table, partition
        self.canvas, self.protocol = tuple(canvas), protocol
        self.free = tuple(p for p, t in enumerate(canvas) if t is None)
        self.free_tensor = torch.tensor(self.free, device="cuda")
        self.counter = None if method == "exact_stack_cpu" else CounterTable(table)
        self.caches = {}

    def level(self, depth):
        if depth not in self.caches:
            limits = {
                key: self.protocol["resources"][key]
                for key in ("max_cells", "max_edges", "max_terms")
            }
            limits["timeout_seconds"] = self.protocol["resources"]["seconds_per_operation"]
            if depth is None:
                prefix = None
                graph = terminated_graph(
                    self.table, self.canvas, None, 50256, 50256, symbolic=True, **limits
                )
            else:
                prefix = PrefixCache(self.table, self.canvas, depth, **limits)
                graph = prefix.terminated_graph(50256, 50256)
            self.caches[depth] = prefix, CPUCache(graph, self.table, **limits)
        return self.caches[depth]

    def evaluate(self, depth, weights):
        prefix, cache = self.level(depth)
        post = cache.reweight(weights)
        if depth is None:
            return post, Fraction(), True
        if not post.total:
            return post, None, True
        frontier = prefix.frontier(weights)
        upper = frontier.mass
        tolerance = Fraction(self.protocol["query_tv_budget"])
        tightened = conditional_error(post.mass, upper) > tolerance
        if tightened:
            upper = self.closure(depth, weights, frontier)
        return post, upper, tightened

    def closure(self, depth, weights, frontier=None):
        if frontier is None:
            frontier = self.caches[depth][0].frontier(weights)
        if self.method == "handoff_cpu":
            return frontier.handoff(self.counter)[0]
        return min(frontier.mass, self.counter.tail(weights, depth, sums=weights.sums)[0])

    def query(self, probabilities, seed):
        # Cold/warm both pay NEW transfer, exact sums, beta/outside and draws.
        head = probabilities.index_select(0, self.free_tensor).cpu().numpy()
        weights = BoundaryWeights(self.table, head, self.canvas, self.partition)
        depths = (None,) if self.method == "exact_stack_cpu" else self.protocol["depths"]
        sampled, draw_delta, draw_depth, refinements = None, None, None, []
        draw_mass = draw_upper = None
        for depth in depths:
            post, upper, tightened = self.evaluate(depth, weights)
            if not post.total:
                refinements.append(dict(depth=depth, status="zero_mass"))
                continue
            delta = conditional_error(post.mass, upper)
            refinements.append(dict(depth=depth, delta=str(delta)))
            if sampled is None:
                if delta > Fraction(self.protocol["query_tv_budget"]):
                    continue
                sampled = sample(post, weights, Random(seed))
                draw_delta, draw_depth = delta, depth
                draw_mass, draw_upper = post.mass, upper
            ranking = ranked_commits(post, sampled, upper, min(4, len(self.free)))
            if ranking["selected"] is None and not tightened and upper:
                # Tighten the SAME-depth certificate before compiling a deeper
                # graph. The sampled word and its ORIGINAL TV charge stay put.
                upper = self.closure(depth, weights)
                delta = conditional_error(post.mass, upper)
                refinements.append(dict(depth=depth, confidence_closure_delta=str(delta)))
                ranking = ranked_commits(post, sampled, upper, min(4, len(self.free)))
            if ranking["selected"] is None:
                continue
            confidence = [1.0] * len(self.canvas)
            for p, numerator in ranking["numerators"].items():
                confidence[p] = float(Fraction(numerator, post.total))
            return dict(
                status="complete",
                **gpu_result(sampled, confidence, ranking["selected"], self.canvas),
                draw_delta=draw_delta,
                draw_depth=draw_depth,
                draw_mass=draw_mass,
                draw_upper=draw_upper,
                confidence_depth=depth,
                confidence_delta=delta,
                true_shallow_mass=post.mass,
                upper_mass=upper,
                refinements=refinements,
                exact_common_ranking=True,
            )
        raise RuntimeError("full exact fallback failed to resolve ranking")


class SparseQuery:
    def __init__(self, method, table, canvas, protocol):
        if method not in ("sparse_fa_fp32", "sparse_fa_fp64", "layered_fa_fp32", "layered_fa_fp64"):
            raise ValueError("unknown first-stage GPU control")
        self.method, self.canvas = method, tuple(canvas)
        limits = {
            key: protocol["resources"][key] for key in ("max_cells", "max_edges", "max_terms")
        }
        limits["timeout_seconds"] = protocol["resources"]["seconds_per_operation"]
        graph = terminated_graph(table, canvas, None, 50256, 50256, symbolic=True, **limits)
        dtype = torch.float64 if method.endswith("fp64") else torch.float32
        if method.startswith("layered_"):
            self.sampler = LayeredFA(prepare_graph(graph, table, canvas, **limits), dtype=dtype)
        else:
            self.sampler = SparseFA(graph, table, dtype=dtype)
        self.free_tensor = torch.tensor(
            [p for p, t in enumerate(canvas) if t is None], device="cuda"
        )

    def query(self, probabilities, seed):
        result = self.sampler.query(probabilities, self.canvas)
        free = self.free_tensor
        order = result["confidence"][free].argsort(descending=True, stable=True)
        selected = free[order[: min(4, len(free))]]
        mask = torch.zeros(len(self.canvas), dtype=torch.bool, device="cuda")
        mask[selected] = True
        return dict(
            status="complete",
            tokens=result["tokens"],
            confidence=result["confidence"],
            commit_mask=mask,
            draw_delta=Fraction(),
            draw_depth=None,
            confidence_depth=None,
            confidence_delta=Fraction(),
            stats=result["stats"],
            exact_common_ranking=False,
            floating_law=True,
        )
