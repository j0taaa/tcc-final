"""Opt-in classical sparse-HMM control, independent of native Mosaic samplers.

Real-arithmetic word law is written in consumer-v4-sparse-fa-control-proof.md.
Torch floating sparse sums/draws are approximate, not rational-exact sampling.
"""

import torch


def scatter_logsumexp(values, index, size):
    maxima = values.new_full((size,), -float("inf"))
    maxima.scatter_reduce_(0, index, values, reduce="amax", include_self=True)
    shifted = (values - maxima[index]).exp().nan_to_num(nan=0.0)
    sums = values.new_zeros(size)
    sums.scatter_add_(0, index, shifted)
    return torch.where(sums > 0, maxima + sums.log(), sums.new_full((), -float("inf")))


def draw(values):
    if not torch.isfinite(values).all() or values.min() < 0 or values.sum() <= 0:
        raise ValueError("sparse control has invalid categorical weights")
    return int(torch.multinomial(values, 1).item())


class SparseFA:
    def __init__(self, graph, table, *, device="cuda", dtype=torch.float64):
        if graph.get("alphabet") != "global_class":
            raise ValueError("sparse control needs the symbolic global-class graph")
        if dtype not in (torch.float32, torch.float64):
            raise ValueError("sparse control supports fp32/fp64")
        self.device, self.dtype = torch.device(device), dtype
        self.initial, self.canvas = graph["initial_state"], tuple(graph["canvas"])
        self.nodes, self.classes = graph["num_nodes"], table.classes
        self.vocabulary_size = table.adapter.vocabulary_size
        self.class_of = torch.tensor(table.class_of, dtype=torch.long, device=device)
        self.accepting = torch.zeros(self.nodes, dtype=dtype, device=device)
        self.accepting[graph["accept_states"]] = 1
        edges = sorted((u, v, tuple(cids)) for u, v, cids in graph["edges"] if cids)
        if not edges:
            raise ValueError("sparse graph has no positive edge")
        self.source = torch.tensor([u for u, _, _ in edges], device=device)
        self.target = torch.tensor([v for _, v, _ in edges], device=device)
        self.edge_ids = torch.arange(len(edges), dtype=torch.long, device=device)
        counts = [0] * self.nodes
        for u, _, _ in edges:
            counts[u] += 1
        self.out_offsets = [0]
        for count in counts:
            self.out_offsets.append(self.out_offsets[-1] + count)
        pointer, labels = [0], []
        for _, _, cids in edges:
            labels.extend(cids)
            pointer.append(len(labels))
        # Build sparse indices/transposition on CPU, then transfer once.
        incidence = torch.sparse_csr_tensor(
            torch.tensor(pointer),
            torch.tensor(labels),
            torch.ones(len(labels), dtype=dtype),
            size=(len(edges), len(table.classes)),
            check_invariants=True,
        )
        self.incidence = incidence.to(device)
        self.incidence_T = incidence.transpose(0, 1).to_sparse_csr().to(device)
        self.edge_labels = torch.tensor(labels, dtype=torch.long, device=device)
        self.edge_offsets = pointer
        flat, offsets = [], [0]
        for members in table.classes:
            flat.extend(members)
            offsets.append(len(flat))
        self.tokens = torch.tensor(flat, dtype=torch.long, device=device)
        self.token_offsets = offsets
        self.stats = dict(
            nodes=self.nodes,
            edges=len(edges),
            classes=len(table.classes),
            memberships=len(labels),
            dense_transition_allocated=False,
            dense_flow_allocated=False,
            dense_original_emission_allocated=False,
        )

    @torch.no_grad()
    def query(self, original_weights, canvas, *, return_all_marginals=False):
        if len(canvas) != len(self.canvas) or any(
            t is not None and canvas[p] != t for p, t in enumerate(self.canvas)
        ):
            raise ValueError("sparse cache changed initial fixed original canvas")
        weights = torch.as_tensor(original_weights, dtype=self.dtype, device=self.device).clone()
        if weights.shape != (len(canvas), self.vocabulary_size):
            raise ValueError("sparse original head shape changed")
        if not torch.isfinite(weights).all() or weights.min() < 0:
            raise ValueError("sparse control needs finite nonnegative original weights")
        for p, token in enumerate(canvas):
            if token is not None:
                weights[p].zero_()
                weights[p, token] = 1
        row_total = weights.sum(1, keepdim=True)
        if (row_total <= 0).any():
            raise ValueError("zero original row")
        weights /= row_total
        length = len(canvas)
        class_weights = weights.new_zeros((length, len(self.classes)))
        class_weights.scatter_add_(1, self.class_of.expand(length, -1), weights)
        edge_weights = torch.sparse.mm(self.incidence, class_weights.T.contiguous()).T
        log_edges = edge_weights.log()
        beta = weights.new_full((length + 1, self.nodes), -float("inf"))
        beta[-1] = self.accepting.log()
        for p in range(length - 1, -1, -1):
            beta[p] = scatter_logsumexp(
                log_edges[p] + beta[p + 1, self.target], self.source, self.nodes
            )
        log_normalizer = beta[0, self.initial]
        if not torch.isfinite(log_normalizer):
            raise ValueError("zero/nonfinite sparse accepting mass; no sample returned")
        alpha = weights.new_full(beta.shape, -float("inf"))
        alpha[0, self.initial] = 0
        for p in range(length):
            alpha[p + 1] = scatter_logsumexp(
                alpha[p, self.source] + log_edges[p], self.target, self.nodes
            )
        edge_coefficient = alpha[:-1, self.source] + beta[1:, self.target]
        shift = edge_coefficient.max(1, keepdim=True).values
        scaled = (edge_coefficient - shift).exp()
        coefficient = torch.sparse.mm(self.incidence_T, scaled.T.contiguous()).T
        class_marginal = class_weights * coefficient
        class_marginal /= class_marginal.sum(1, keepdim=True)
        if not torch.isfinite(class_marginal).all():
            raise ValueError("nonfinite sparse marginals; no sample returned")
        selected, selected_classes, state = [], [], self.initial
        for p in range(length):
            candidates = self.edge_ids[self.out_offsets[state] : self.out_offsets[state + 1]]
            logits = log_edges[p, candidates] + beta[p + 1, self.target[candidates]]
            edge = int(candidates[draw(logits.softmax(0))].item())
            cids = self.edge_labels[self.edge_offsets[edge] : self.edge_offsets[edge + 1]]
            cid = int(cids[draw(class_weights[p, cids])].item())
            ids = self.tokens[self.token_offsets[cid] : self.token_offsets[cid + 1]]
            token = int(ids[draw(weights[p, ids])].item())
            selected.append(token)
            selected_classes.append(cid)
            state = int(self.target[edge].item())
        word = torch.tensor(selected, dtype=torch.long, device=self.device)
        cids = torch.tensor(selected_classes, dtype=torch.long, device=self.device)
        positions = torch.arange(length, device=self.device)
        confidence = (
            class_marginal[positions, cids]
            * weights[positions, word]
            / class_weights[positions, cids]
        )
        result = dict(
            tokens=word, confidence=confidence, log_normalizer=log_normalizer, stats=self.stats
        )
        if return_all_marginals:
            denominators = class_weights[:, self.class_of]
            result["marginals"] = torch.where(
                denominators > 0,
                class_marginal[:, self.class_of]
                * weights
                / denominators.masked_fill(denominators == 0, 1),
                weights.new_zeros(()),
            )
        return result
