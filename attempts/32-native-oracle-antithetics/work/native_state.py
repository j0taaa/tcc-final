"""Unchanged A31v3 ModelHistory, copied from immutable0a27a24. See provenance."""


class ModelHistory:
    """Capture sufficient current input or preserve the full-history control.

    One proxy per label; immutable batch namespace must include model, grammar,
    tokenizer and ALL decoder settings. Model is frozen/eval and receives the
    same inputs as native EPIC. Capturing histories adds CPU transfers/cost.
    """

    def __init__(self, model, namespace, *, mode="state"):
        hash(namespace)
        if mode not in ("state", "history", "root"):
            raise ValueError("unknown native coordination mode")
        self.model, self.namespace, self.history, self.inputs = model, namespace, (), None
        self.mode, self.calls, self.noise_calls = mode, 0, 0

    def __getattr__(self, name):
        return getattr(self.model, name)

    def __call__(self, input_ids, *args, **kwargs):
        if args or kwargs:
            raise ValueError("audited native model boundary accepts only input_ids")
        if self.mode != "root" or self.calls == 0:
            self.inputs = tuple(tuple(row) for row in input_ids.detach().cpu().tolist())
        if self.mode == "history":
            self.history = (*self.history, ("forward", self.inputs))
        self.calls += 1
        return self.model(input_ids)
