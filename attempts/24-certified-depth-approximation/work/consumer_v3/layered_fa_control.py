"""Classical sparse fixed-canvas DAG control; opt-in Torch, no new theorem."""

import torch

from .sparse_fa_control import draw, scatter_logsumexp


class LayeredFA:
    def __init__(self, prepared, *, device="cuda", dtype=torch.float64):
        self.device, self.dtype = torch.device(device), dtype
        self.canvas = tuple(prepared.canvas)
        table = prepared.table
        self.classes, self.vocabulary_size = table.classes, table.adapter.vocabulary_size
        self.class_of_cpu = tuple(table.class_of)
        self.class_of = torch.tensor(self.class_of_cpu, dtype=torch.long, device=device)
        self.node_counts = tuple(map(len, prepared.layers))
        self.accepting = torch.tensor(prepared.accepting, dtype=dtype, device=device)
        src, dst, labels, incidence_pointer, layer_pointer = [], [], [], [0], [0]
        self.out_bounds, self.edge_classes_cpu = [], []
        length, count = len(prepared.arcs), len(table.classes)
        for p, layer in enumerate(prepared.arcs):
            bounds = []
            for a, outgoing in enumerate(layer):
                bounds.append(len(src))
                for b, gids in outgoing:
                    cids = tuple(sorted({c for g in gids for c in table.local_to_class[g]}))
                    src.append(a)
                    dst.append(b)
                    self.edge_classes_cpu.append(cids)
                    labels.extend(p * count + c for c in cids)
                    incidence_pointer.append(len(labels))
            bounds.append(len(src))
            self.out_bounds.append(bounds)
            layer_pointer.append(len(src))
        self.layer_pointer = layer_pointer
        self.source = torch.tensor(src, dtype=torch.long, device=device)
        self.target = torch.tensor(dst, dtype=torch.long, device=device)
        self.edge_ids = torch.arange(len(src), dtype=torch.long, device=device)
        incidence = torch.sparse_csr_tensor(
            torch.tensor(incidence_pointer),
            torch.tensor(labels),
            torch.ones(len(labels), dtype=dtype),
            size=(len(src), length * count),
            check_invariants=True,
        )
        self.incidence = incidence.to(device)
        self.incidence_T = incidence.transpose(0, 1).to_sparse_csr().to(device)
        self.edge_offsets = incidence_pointer
        self.edge_labels = torch.tensor(labels, dtype=torch.long, device=device) % count
        self.token_offsets, flat = [0], []
        for members in table.classes:
            flat.extend(members)
            self.token_offsets.append(len(flat))
        self.tokens = torch.tensor(flat, dtype=torch.long, device=device)
        self.target_cpu = tuple(dst)
        self.stats = dict(
            nodes=sum(self.node_counts),
            edges=len(src),
            memberships=len(labels),
            classes=count,
            dense_transition_allocated=False,
            dense_flow_allocated=False,
            dense_original_emission_allocated=False,
            repeated_merged_states=False,
        )

    @torch.no_grad()
    def query(self, original_weights, canvas, *, return_all_marginals=False):
        if len(canvas) != len(self.canvas) or any(
            t is not None and canvas[p] != t for p, t in enumerate(self.canvas)
        ):
            raise ValueError("layered cache changed initial fixed original canvas")
        weights = torch.as_tensor(original_weights, dtype=self.dtype, device=self.device).clone()
        if weights.shape != (len(canvas), self.vocabulary_size):
            raise ValueError("layered original head shape changed")
        if not torch.isfinite(weights).all() or weights.min() < 0:
            raise ValueError("layered control needs nonnegative finite weights")
        for p, token in enumerate(canvas):
            if token is not None:
                weights[p].zero_()
                weights[p, token] = 1
        row_total = weights.sum(1, keepdim=True)
        if (row_total <= 0).any():
            raise ValueError("zero original row")
        weights /= row_total
        length, count = len(canvas), len(self.classes)
        class_weights = weights.new_zeros((length, count))
        class_weights.scatter_add_(1, self.class_of.expand(length, -1), weights)
        edge_weights = torch.sparse.mm(self.incidence, class_weights.reshape(-1, 1)).squeeze(1)
        log_edges = edge_weights.log()
        beta = [None] * (length + 1)
        beta[-1] = self.accepting.log()
        for p in range(length - 1, -1, -1):
            start, end = self.layer_pointer[p : p + 2]
            src, dst = self.source[start:end], self.target[start:end]
            beta[p] = scatter_logsumexp(
                log_edges[start:end] + beta[p + 1][dst], src, self.node_counts[p]
            )
        normalizer = beta[0][0]
        if not torch.isfinite(normalizer):
            raise ValueError("zero/nonfinite layered accepting mass; no sample returned")
        alpha, coefficients = [weights.new_zeros(1)], []
        for p in range(length):
            start, end = self.layer_pointer[p : p + 2]
            src, dst = self.source[start:end], self.target[start:end]
            coefficient = alpha[p][src] + beta[p + 1][dst]
            shift = coefficient.max()
            coefficients.append((coefficient - shift).exp())
            alpha.append(
                scatter_logsumexp(
                    alpha[p][src] + log_edges[start:end], dst, self.node_counts[p + 1]
                )
            )
        coefficient = torch.sparse.mm(self.incidence_T, torch.cat(coefficients)[:, None])
        class_marginal = class_weights * coefficient.reshape(length, count)
        class_marginal /= class_marginal.sum(1, keepdim=True)
        if not torch.isfinite(class_marginal).all():
            raise ValueError("nonfinite layered marginal; no sample returned")
        word, selected_classes, state = [], [], 0
        for p, fixed in enumerate(canvas):
            start, end = self.out_bounds[p][state : state + 2]
            if fixed is not None:
                cid = self.class_of_cpu[fixed]
                choices = [e for e in range(start, end) if cid in self.edge_classes_cpu[e]]
                if len(choices) != 1:
                    raise ValueError("fixed original ID has no unique layered arc")
                edge, token = choices[0], fixed
            else:
                candidates = self.edge_ids[start:end]
                logits = log_edges[candidates] + beta[p + 1][self.target[candidates]]
                edge = int(candidates[draw(logits.softmax(0))].item())
                cids = self.edge_labels[self.edge_offsets[edge] : self.edge_offsets[edge + 1]]
                cid = int(cids[draw(class_weights[p, cids])].item())
                ids = self.tokens[self.token_offsets[cid] : self.token_offsets[cid + 1]]
                token = int(ids[draw(weights[p, ids])].item())
            word.append(token)
            selected_classes.append(cid)
            state = self.target_cpu[edge]
        word = torch.tensor(word, dtype=torch.long, device=self.device)
        cids = torch.tensor(selected_classes, dtype=torch.long, device=self.device)
        positions = torch.arange(length, device=self.device)
        confidence = (
            class_marginal[positions, cids]
            * weights[positions, word]
            / class_weights[positions, cids]
        )
        result = dict(
            tokens=word, confidence=confidence, log_normalizer=normalizer, stats=self.stats
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
