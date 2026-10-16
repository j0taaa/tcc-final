"""All-length and retained-anchor conditional score readouts, FP64 only."""

import numpy as np

from .actor_coordinates import actor_vector
from .length_readout import readout


def support(planner, action, features):
    full = planner.statistics(action)
    visible = actor_vector(full, features)
    lengths = []
    zeros = []
    for length in range(1, planner.n + 1):
        value = readout(planner, action, length)
        if value is None:
            zeros.append(length)
            continue
        mass = float(np.exp(value["log_probability"] - full["log_probability"]))
        if not mass > 0 or not np.isfinite(mass):
            raise ValueError("positive conditional length mass underflow/nonfinite")
        lengths.append(
            {
                "length": length,
                "probability_given_action": mass,
                "actor": actor_vector(value, features).tolist(),
                "log_joint_probability": value["log_probability"],
            }
        )
    total = sum(r["probability_given_action"] for r in lengths)
    mixture = sum(r["probability_given_action"] * np.asarray(r["actor"]) for r in lengths)
    error = float(np.max(np.abs(mixture - visible)))
    if abs(total - 1) > 1e-7 or error > 1e-7:
        raise ValueError("length mass/score mixture differs from observed action")
    terms = {i: 1 / planner.gates[i, v] for i, v in action}
    rho = {i: v / sum(terms.values()) for i, v in terms.items()}
    anchors = []
    for anchor in rho:
        aa = full["alpha"].copy()
        rr = full["anchor"].copy()
        bb = full["beta"]
        for i, v in action:
            correction = (rho[i] - int(i == anchor)) * (1 - planner.gates[i, v])
            aa[i] += correction
            bb += correction * planner.logc[i, v]
        rr[anchor] += 1
        for i in rho:
            rr[i] -= rho[i]
        vec = actor_vector({"alpha": aa, "anchor": rr, "beta": bb}, features)
        anchors.append(
            {
                "anchor": anchor,
                "probability_given_action": float(rho[anchor]),
                "actor": vec.tolist(),
            }
        )
    anchor_error = float(
        np.max(
            np.abs(
                sum(r["probability_given_action"] * np.asarray(r["actor"]) for r in anchors)
                - visible
            )
        )
    )
    if anchor_error > 1e-7:
        raise ValueError("anchor score mixture differs from observed action")
    return {
        "collapsed_actor": visible.tolist(),
        "lengths": lengths,
        "structural_zero_lengths": zeros,
        "anchors": anchors,
        "length_mass_error": abs(total - 1),
        "length_score_error": error,
        "anchor_score_error": anchor_error,
        "action_log_probability": float(full["log_probability"]),
    }
