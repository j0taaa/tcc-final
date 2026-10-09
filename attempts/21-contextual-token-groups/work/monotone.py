"""Classical decremental AND/OR propagation on the maintained token forest.

Quimper/Walsh grammar propagation is the antecedent, not an invention here.
Contract: decomposable acyclic forest, finite original-token support, only
monotonic commitments. Predictions/ranks can change arbitrarily between steps.
"""

from collections import defaultdict, deque


class Monotone:
    def __init__(self, plan):
        self.plan = plan
        self.canvas = list(plan.state.canvas)
        self.terms = []
        self.by_node = [[] for _ in plan.terms]
        self.by_child = [[] for _ in plan.terms]
        self.by_choice = defaultdict(list)
        for node, terms in enumerate(plan.terms):
            for term in terms:
                tid = len(self.terms)
                self.terms.append((node, term.children, term.choice))
                self.by_node[node].append(tid)
                for child in term.children:
                    self.by_child[child].append(tid)
                if term.choice is not None:
                    self.by_choice[term.choice].append(tid)
        self.active = [False] * len(self.terms)
        self.live = [0] * len(plan.terms)
        for node in plan.order:
            for tid in self.by_node[node]:
                _, children, choice = self.terms[tid]
                enabled = choice is None or (
                    self.canvas[choice[0]] is None
                    or self.canvas[choice[0]] == plan.state.support.rows[choice[0]][choice[1]]
                )
                self.active[tid] = enabled and all(self.live[c] for c in children)
                self.live[node] += self.active[tid]
        if plan.root is None or not self.live[plan.root]:
            raise ValueError("infeasible_on_support")
        self.reach = [0] * len(plan.terms)
        self.reach[plan.root] = 1
        self.flow = [False] * len(self.terms)
        self.supported = defaultdict(int)
        for node in reversed(plan.order):
            if not self.reach[node]:
                continue
            for tid in self.by_node[node]:
                if not self.active[tid]:
                    continue
                self.flow[tid] = True
                _, children, choice = self.terms[tid]
                for child in children:
                    self.reach[child] += 1
                if choice is not None:
                    self.supported[choice] += 1
        self.index = [dict((t, i) for i, t in enumerate(row)) for row in plan.state.support.rows]
        self.deactivated = 0
        self.flow_removed = 0

    def feasible(self, position, token):
        if type(position) is not int or not 0 <= position < len(self.canvas):
            raise ValueError("invalid position")
        if type(token) is not int:
            raise ValueError("invalid original token id")
        index = self.index[position].get(token)
        return index is not None and bool(self.supported[position, index])

    def _remove_flow(self, tid, queue):
        if not self.flow[tid]:
            return
        self.flow[tid] = False
        self.flow_removed += 1
        _, children, choice = self.terms[tid]
        if choice is not None:
            self.supported[choice] -= 1
        for child in children:
            self.reach[child] -= 1
            if not self.reach[child]:
                queue.append((False, child))

    def commit(self, position, token):
        if not self.feasible(position, token):
            raise ValueError("incompatible commitment")
        if self.canvas[position] is not None:
            return
        self.canvas[position] = token
        queue = deque()
        for index, alternative in enumerate(self.plan.state.support.rows[position]):
            if alternative != token:
                queue.extend((True, tid) for tid in self.by_choice[position, index])
        while queue:
            deactivate, item = queue.popleft()
            if not deactivate:
                for tid in self.by_node[item]:
                    self._remove_flow(tid, queue)
                continue
            if not self.active[item]:
                continue
            self.active[item] = False
            self.deactivated += 1
            self._remove_flow(item, queue)
            node = self.terms[item][0]
            self.live[node] -= 1
            if not self.live[node]:
                queue.extend((True, tid) for tid in self.by_child[node])
        if not self.live[self.plan.root]:
            raise RuntimeError("a supported commitment removed every completion")

    def transition(self, proposals, *, threshold=0.8, cap=None):
        """Observable greedy transition; avoid speculative below-threshold commits.

        Proposals are (position, token, confidence), ordered by descending
        confidence, then position/token. Independent of confidence magnitudes.
        """
        validate_order(proposals)
        if cap is None:
            cap = len(self.canvas)
        if type(cap) is not int or cap < 1:
            raise ValueError("cap must be a positive integer")
        updates = []
        for position, token, confidence in proposals:
            if confidence < threshold or len(updates) == cap:
                break
            if self.canvas[position] is None and self.feasible(position, token):
                self.commit(position, token)
                updates.append((position, token))
        if updates:
            return tuple(updates)
        # The first accepted proposal is identical to the full greedy fallback.
        for position, token, _ in proposals:
            if self.canvas[position] is None and self.feasible(position, token):
                self.commit(position, token)
                return ((position, token),)
        position = self.canvas.index(None)
        token = min(t for t in self.index[position] if self.feasible(position, t))
        self.commit(position, token)
        return ((position, token),)


def validate_order(proposals):
    from math import isfinite

    if any(not isfinite(w) or not 0 <= w <= 1 for _, _, w in proposals):
        raise ValueError("confidence must be a finite probability")
    if list(proposals) != sorted(proposals, key=lambda p: (-p[2], p[0], p[1])):
        raise ValueError("proposals must follow the declared stable order")
