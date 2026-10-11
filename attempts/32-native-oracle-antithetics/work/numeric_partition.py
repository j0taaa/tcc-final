"""Pre-noise numerical-prefix projection; no grammar filtering or gold."""

import hashlib
import json
import re


class NumericPartition:
    def __init__(self, pieces):
        candidates = [
            (text.lstrip(" \t\r\n"), i)
            for i, text in enumerate(pieces)
            if re.match(r"-?[0-9]", text.lstrip(" \t\r\n"))
        ]
        candidates.sort()
        if len(candidates) < 2:
            raise ValueError("at least two numerical-prefix original IDs required")
        self.ids = tuple(i for _, i in candidates)
        self.signature = hashlib.sha256(json.dumps(candidates).encode()).hexdigest()
        self.tensors = {}

    def tensor(self, device):
        import torch

        key = str(device)
        if key not in self.tensors:
            self.tensors[key] = torch.tensor(self.ids, dtype=torch.long, device=device)
        return self.tensors[key]

    def split(self, values, temperature):
        import torch

        indices = self.tensor(values.device)
        probs = torch.softmax(values.index_select(0, indices) / temperature, dim=0)
        cumulative = probs.cumsum(0)
        if not bool(torch.isfinite(cumulative).all()):
            raise ValueError("nonfinite partition estimate")
        cutoff = int((cumulative[:-1] - 0.5).abs().argmin())

        def project(row):
            return int(row.index_select(0, indices).argmax()) > cutoff

        # Only the approximate known-p control consumes this probability.
        # Walk/pool decisions read classes alone, never this estimate.
        return cutoff, project, float(probs[cutoff + 1 :].sum())
