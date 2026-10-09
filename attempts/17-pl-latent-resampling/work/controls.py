"""One offline, smoke-tested constructor registry for both utility harnesses."""

from functools import partial

from replay import EnumeratedTarget
from resampling import BaseRejection, RoundedProfiles, SingleTilt, TangentMixture


def iid_controls(strengthened=False, fast_forced=False):
    methods = {
        "mixture": partial(
            TangentMixture,
            dyadic_unaries=True,
            tight_bounds=True,
            dyadic_coefficients=True,
            certify_scale=strengthened,
            fast_forced=fast_forced,
        ),
        "base": partial(BaseRejection, tight_bounds=True, fast_forced=fast_forced),
        "single": partial(
            SingleTilt,
            dyadic_coefficients=True,
            precise_envelope=strengthened,
            fast_forced=fast_forced,
        ),
        "enumeration": partial(EnumeratedTarget, fast_forced=fast_forced),
    }
    if strengthened:
        methods["profiles"] = partial(RoundedProfiles, dyadic_root=True, fast_forced=fast_forced)
    return methods


def neural_controls(strengthened=False, fast_forced=False):
    methods = iid_controls(strengthened, fast_forced)
    names = [
        ("base_iid", "base"),
        ("single_iid", "single"),
        ("mixture_iid", "mixture"),
        ("base_imh_rb", "base"),
        ("single_imh_rb", "single"),
        ("conditional_mean", "enumeration"),
    ]
    if strengthened:
        names.append(("profiles_iid", "profiles"))
    return [(label, methods[key]) for label, key in names]
