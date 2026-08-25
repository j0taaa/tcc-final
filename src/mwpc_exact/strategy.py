"""Validated decoder-strategy configuration and model-independent dispatch."""

from __future__ import annotations

import argparse
import json
import os
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from enum import StrEnum
from typing import TypeVar

from mwpc_exact.adaptive import AdaptiveSupportConfig
from mwpc_exact.backend import ExactBackend
from mwpc_exact.decoder_types import FailureFallbackStrategy
from mwpc_exact.eos_policy import EOSMode, EOSPolicy
from mwpc_exact.proposal_policy import ProposalWeightMode

LEGACY_EPIC_ENVIRONMENT_VARIABLE = "CONSTRAINED_DIFFUSION_REGULAR_COVER_BATCH"
EXACTNESS_SCOPE_HELP = (
    "Exact mode is exact_on_support for the represented finite top-K support; "
    "it is not a full-vocabulary or future-trajectory optimality claim."
)


class CommitStrategy(StrEnum):
    """Mutually exclusive token-commit paths exposed by the integration layer."""

    SERIAL = "serial"
    EPIC = "epic"
    EXACT = "exact"


@dataclass(frozen=True, slots=True)
class ExactStrategyConfig:
    """Exact-only controls after CLI defaults and invariants are resolved."""

    adaptive_support: AdaptiveSupportConfig
    weight_mode: ProposalWeightMode
    eos_policy: EOSPolicy
    backend: ExactBackend
    failure_fallback_strategy: FailureFallbackStrategy | None

    def __post_init__(self) -> None:
        if not isinstance(self.adaptive_support, AdaptiveSupportConfig):
            raise TypeError("adaptive_support must be an AdaptiveSupportConfig")
        if not isinstance(self.weight_mode, ProposalWeightMode):
            raise TypeError("weight_mode must be a ProposalWeightMode")
        if not isinstance(self.eos_policy, EOSPolicy):
            raise TypeError("eos_policy must be an EOSPolicy")
        if not isinstance(self.backend, ExactBackend):
            raise TypeError("backend must be an ExactBackend")
        if self.failure_fallback_strategy is not None and not isinstance(
            self.failure_fallback_strategy,
            FailureFallbackStrategy,
        ):
            raise TypeError("failure_fallback_strategy must be a FailureFallbackStrategy or None")

    def to_dict(self) -> dict[str, object]:
        return {
            "exactness_scope": "exact_on_support",
            "adaptive_support": self.adaptive_support.to_dict(),
            "weight_mode": self.weight_mode.value,
            "eos_policy": self.eos_policy.to_dict(),
            "backend": self.backend.value,
            "failure_fallback_strategy": (
                None
                if self.failure_fallback_strategy is None
                else self.failure_fallback_strategy.value
            ),
        }


@dataclass(frozen=True, slots=True)
class DecoderStrategyConfig:
    """Resolved baseline or exact strategy; exact controls never leak into baselines."""

    strategy: CommitStrategy
    exact: ExactStrategyConfig | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.strategy, CommitStrategy):
            raise TypeError("strategy must be a CommitStrategy")
        if self.strategy is CommitStrategy.EXACT:
            if not isinstance(self.exact, ExactStrategyConfig):
                raise ValueError("exact strategy requires exact configuration")
        elif self.exact is not None:
            raise ValueError("serial and EPIC strategies cannot carry exact configuration")

    def to_dict(self) -> dict[str, object]:
        return {
            "commit_strategy": self.strategy.value,
            "exact": None if self.exact is None else self.exact.to_dict(),
        }


def legacy_commit_strategy(environ: Mapping[str, str] | None = None) -> CommitStrategy:
    """Resolve the unmodified EPIC environment convention when no new flag is set."""

    environment = os.environ if environ is None else environ
    return (
        CommitStrategy.EPIC
        if environment.get(LEGACY_EPIC_ENVIRONMENT_VARIABLE, "0") == "1"
        else CommitStrategy.SERIAL
    )


def add_commit_strategy_arguments(parser: argparse.ArgumentParser) -> None:
    """Add reusable T900 arguments without importing a model or EPIC module."""

    if not isinstance(parser, argparse.ArgumentParser):
        raise TypeError("parser must be an argparse.ArgumentParser")
    parser.add_argument(
        "--commit-strategy",
        choices=tuple(strategy.value for strategy in CommitStrategy),
        default=None,
        help=(
            "token commitment strategy; omitted preserves the legacy EPIC environment "
            "switch (default upstream behavior is serial)"
        ),
    )
    parser.add_argument(
        "--exact-support-top-k",
        type=int,
        default=None,
        help="initial represented top-K width; exact_on_support, never globally exact",
    )
    parser.add_argument(
        "--exact-support-k-max",
        type=int,
        default=None,
        help="maximum adaptive top-K width (exact default: initial width)",
    )
    parser.add_argument(
        "--exact-weight-mode",
        choices=tuple(mode.value for mode in ProposalWeightMode),
        default=None,
        help="proposal objective weights (exact default: confidence)",
    )
    parser.add_argument(
        "--exact-timeout-seconds",
        type=float,
        default=None,
        help=(
            "total adaptive deadline; Rust attempts are bounded, while a Python reference "
            "attempt already running is classified after it returns"
        ),
    )
    parser.add_argument(
        "--exact-eos-policy",
        choices=tuple(mode.value for mode in EOSMode),
        default=None,
        help="required explicit EOS/PAD policy for exact mode",
    )
    parser.add_argument(
        "--exact-eos-token-id",
        action="append",
        type=int,
        default=None,
        help="termination token ID; repeat for alternate EOS/EOT IDs",
    )
    parser.add_argument(
        "--exact-pad-token-id",
        type=int,
        default=None,
        help="canonical PAD token ID for required/optional EOS policies",
    )
    parser.add_argument(
        "--exact-backend",
        choices=tuple(backend.value for backend in ExactBackend),
        default=None,
        help="exact parser backend (exact default: rust)",
    )
    parser.add_argument(
        "--exact-fallback",
        choices=("none", *(strategy.value for strategy in FailureFallbackStrategy)),
        default=None,
        help="non-exact progress fallback after timeout/error (exact default: serial)",
    )


def build_commit_strategy_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="mwpc-commit-config",
        description="Validate serial, EPIC, or exact decoder commitment configuration.",
        epilog=EXACTNESS_SCOPE_HELP,
    )
    add_commit_strategy_arguments(parser)
    return parser


_EXACT_NAMESPACE_FIELDS = (
    "exact_support_top_k",
    "exact_support_k_max",
    "exact_weight_mode",
    "exact_timeout_seconds",
    "exact_eos_policy",
    "exact_eos_token_id",
    "exact_pad_token_id",
    "exact_backend",
    "exact_fallback",
)


def decoder_strategy_config_from_namespace(
    namespace: argparse.Namespace,
    *,
    environ: Mapping[str, str] | None = None,
) -> DecoderStrategyConfig:
    """Resolve and validate one parser namespace before model loading begins."""

    if not isinstance(namespace, argparse.Namespace):
        raise TypeError("namespace must be an argparse.Namespace")
    raw_strategy = getattr(namespace, "commit_strategy", None)
    strategy = (
        legacy_commit_strategy(environ) if raw_strategy is None else CommitStrategy(raw_strategy)
    )
    supplied_exact_fields = tuple(
        field_name
        for field_name in _EXACT_NAMESPACE_FIELDS
        if getattr(namespace, field_name, None) is not None
    )
    if strategy is not CommitStrategy.EXACT:
        if supplied_exact_fields:
            rendered = ", ".join(
                field_name.replace("_", "-") for field_name in supplied_exact_fields
            )
            raise ValueError(f"exact-only options require --commit-strategy exact: {rendered}")
        return DecoderStrategyConfig(strategy=strategy)

    raw_top_k = getattr(namespace, "exact_support_top_k", None)
    if raw_top_k is None:
        raise ValueError("exact strategy requires --exact-support-top-k")
    raw_k_max = getattr(namespace, "exact_support_k_max", None)
    adaptive_support = AdaptiveSupportConfig(
        initial_k=raw_top_k,
        k_max=raw_top_k if raw_k_max is None else raw_k_max,
        total_timeout_seconds=getattr(namespace, "exact_timeout_seconds", None),
    )

    raw_eos_mode = getattr(namespace, "exact_eos_policy", None)
    if raw_eos_mode is None:
        raise ValueError("exact strategy requires --exact-eos-policy")
    eos_policy = EOSPolicy(
        mode=EOSMode(raw_eos_mode),
        termination_token_ids=tuple(getattr(namespace, "exact_eos_token_id", None) or ()),
        pad_token_id=getattr(namespace, "exact_pad_token_id", None),
    )

    raw_fallback = getattr(namespace, "exact_fallback", None)
    fallback = (
        FailureFallbackStrategy.SERIAL
        if raw_fallback is None
        else None
        if raw_fallback == "none"
        else FailureFallbackStrategy(raw_fallback)
    )
    exact = ExactStrategyConfig(
        adaptive_support=adaptive_support,
        weight_mode=ProposalWeightMode(
            getattr(namespace, "exact_weight_mode", None) or ProposalWeightMode.CONFIDENCE.value
        ),
        eos_policy=eos_policy,
        backend=ExactBackend(getattr(namespace, "exact_backend", None) or ExactBackend.RUST.value),
        failure_fallback_strategy=fallback,
    )
    return DecoderStrategyConfig(strategy=strategy, exact=exact)


T = TypeVar("T")


def dispatch_commit_strategy(
    config: DecoderStrategyConfig,
    *,
    serial: Callable[[], T],
    epic: Callable[[], T],
    exact: Callable[[ExactStrategyConfig], T],
) -> T:
    """Invoke exactly one strategy callback without modifying baseline functions."""

    if not isinstance(config, DecoderStrategyConfig):
        raise TypeError("config must be a DecoderStrategyConfig")
    for callback, name in ((serial, "serial"), (epic, "epic"), (exact, "exact")):
        if not callable(callback):
            raise TypeError(f"{name} callback must be callable")
    if config.strategy is CommitStrategy.SERIAL:
        return serial()
    if config.strategy is CommitStrategy.EPIC:
        return epic()
    if config.exact is None:
        raise AssertionError("validated exact strategy omitted its configuration")
    return exact(config.exact)


def main(
    argv: Sequence[str] | None = None,
    *,
    environ: Mapping[str, str] | None = None,
) -> int:
    """Validate and print the resolved strategy configuration as JSON."""

    parser = build_commit_strategy_parser()
    namespace = parser.parse_args(argv)
    try:
        config = decoder_strategy_config_from_namespace(namespace, environ=environ)
    except (TypeError, ValueError) as error:
        parser.error(str(error))
    print(json.dumps(config.to_dict(), sort_keys=True))
    return 0


__all__ = [
    "EXACTNESS_SCOPE_HELP",
    "CommitStrategy",
    "DecoderStrategyConfig",
    "ExactStrategyConfig",
    "add_commit_strategy_arguments",
    "build_commit_strategy_parser",
    "decoder_strategy_config_from_namespace",
    "dispatch_commit_strategy",
    "legacy_commit_strategy",
    "main",
]
