"""Read-only pinned generator boundary; do not alter native locals or tokens."""

from types import GeneratorType

from .native_state import Candidate


def step_done(iterator, complete):
    for _ in range(4):
        frame = iterator.gi_frame
        if frame is None:
            raise ValueError("missing suspended native frame")
        values = frame.f_locals
        if "_n_transfer_this_step" in values:
            if values["i"] != 0 or values["num_block"] != 0:
                raise ValueError("crossed first native neural step")
            committed = values["_regular_cover_committed"]
            remaining = values["_n_transfer_this_step"] - committed
            return complete or remaining == 0 or values.get("j", -1) == remaining - 1
        nested = values.get("gen")
        if not isinstance(nested, GeneratorType):
            raise ValueError("unknown native generator wrapper")
        iterator = nested
    raise ValueError("too many generator wrappers")


class StageCandidate(Candidate):
    def pause(self):
        """One RNG scope, snapshots at first/boundary only; no second forward."""
        if self.first is not None or self.ended:
            raise ValueError("first-step pause requires a fresh candidate")
        with self.streams():
            last = None
            for tokens, rejected, complete in self.iterator:
                if self.first is None:
                    self.first = tokens.clone(), tuple(tuple(x) for x in rejected), bool(complete)
                last = tokens, rejected, complete
                if step_done(self.iterator, bool(complete)):
                    break
            else:
                self.ended = True
            if last is not None:
                tokens, rejected, complete = last
                self.current = tokens.clone(), tuple(tuple(x) for x in rejected), bool(complete)
            return self.current


def body_key(snapshot, input_length):
    if snapshot is None:
        return ("NO_YIELD",)
    ids = snapshot[0][0, input_length:].tolist()
    return next(
        ((i, t) for i, t in enumerate(ids) if t not in (126336, 126081, 126348)), ("NO_BODY",)
    )
