from __future__ import annotations

import json
from collections.abc import Mapping

import pytest

from mwpc_exact import (
    CommitStrategy,
    DecoderStrategyConfig,
    ExactBackend,
    FailureFallbackStrategy,
    ProposalWeightMode,
    build_commit_strategy_parser,
    decoder_strategy_config_from_namespace,
    dispatch_commit_strategy,
)
from mwpc_exact.strategy import main


def _config(
    arguments: tuple[str, ...],
    *,
    epic_enabled: bool = False,
) -> DecoderStrategyConfig:
    parser = build_commit_strategy_parser()
    namespace = parser.parse_args(arguments)
    environment = {"CONSTRAINED_DIFFUSION_REGULAR_COVER_BATCH": "1" if epic_enabled else "0"}
    return decoder_strategy_config_from_namespace(namespace, environ=environment)


def test_omitted_strategy_preserves_legacy_serial_and_epic_environment_switch() -> None:
    serial = _config(())
    epic = _config((), epic_enabled=True)

    assert serial.strategy is CommitStrategy.SERIAL
    assert serial.exact is None
    assert epic.strategy is CommitStrategy.EPIC
    assert epic.exact is None


@pytest.mark.parametrize(
    ("strategy", "expected"),
    (("serial", "serial"), ("epic", "epic")),
)
def test_baseline_dispatch_invokes_only_the_selected_unchanged_callback(
    strategy: str,
    expected: str,
) -> None:
    calls: list[str] = []
    config = _config(("--commit-strategy", strategy), epic_enabled=True)

    result = dispatch_commit_strategy(
        config,
        serial=lambda: calls.append("serial") or "serial",
        epic=lambda: calls.append("epic") or "epic",
        exact=lambda _config: calls.append("exact") or "exact",
    )

    assert result == expected
    assert calls == [expected]


def test_exact_configuration_resolves_every_scientific_control_and_dispatches() -> None:
    config = _config(
        (
            "--commit-strategy",
            "exact",
            "--exact-support-top-k",
            "4",
            "--exact-support-k-max",
            "16",
            "--exact-weight-mode",
            "unit",
            "--exact-timeout-seconds",
            "2.5",
            "--exact-eos-policy",
            "required",
            "--exact-eos-token-id",
            "3",
            "--exact-eos-token-id",
            "4",
            "--exact-pad-token-id",
            "5",
            "--exact-backend",
            "python",
            "--exact-fallback",
            "epic",
        )
    )

    assert config.strategy is CommitStrategy.EXACT
    assert config.exact is not None
    assert config.exact.adaptive_support.initial_k == 4
    assert config.exact.adaptive_support.k_max == 16
    assert config.exact.adaptive_support.total_timeout_seconds == 2.5
    assert config.exact.weight_mode is ProposalWeightMode.UNIT
    assert config.exact.eos_policy.termination_token_ids == (3, 4)
    assert config.exact.eos_policy.pad_token_id == 5
    assert config.exact.backend is ExactBackend.PYTHON
    assert config.exact.failure_fallback_strategy is FailureFallbackStrategy.EPIC
    exact_payload = config.to_dict()["exact"]
    assert isinstance(exact_payload, Mapping)
    assert exact_payload["exactness_scope"] == "exact_on_support"

    observed = dispatch_commit_strategy(
        config,
        serial=lambda: "serial",
        epic=lambda: "epic",
        exact=lambda exact_config: exact_config,
    )
    assert observed is config.exact


def test_exact_defaults_are_explicit_and_do_not_affect_baseline_modes() -> None:
    config = _config(
        (
            "--commit-strategy",
            "exact",
            "--exact-support-top-k",
            "2",
            "--exact-eos-policy",
            "absent",
        )
    )

    assert config.exact is not None
    assert config.exact.adaptive_support.k_max == 2
    assert config.exact.weight_mode is ProposalWeightMode.CONFIDENCE
    assert config.exact.backend is ExactBackend.RUST
    assert config.exact.failure_fallback_strategy is FailureFallbackStrategy.SERIAL


@pytest.mark.parametrize(
    ("arguments", "message"),
    (
        (
            ("--commit-strategy", "serial", "--exact-support-top-k", "2"),
            "exact-only options",
        ),
        (("--commit-strategy", "exact", "--exact-eos-policy", "absent"), "support-top-k"),
        (
            (
                "--commit-strategy",
                "exact",
                "--exact-support-top-k",
                "2",
            ),
            "eos-policy",
        ),
        (
            (
                "--commit-strategy",
                "exact",
                "--exact-support-top-k",
                "2",
                "--exact-support-k-max",
                "1",
                "--exact-eos-policy",
                "absent",
            ),
            "greater than or equal",
        ),
        (
            (
                "--commit-strategy",
                "exact",
                "--exact-support-top-k",
                "2",
                "--exact-eos-policy",
                "required",
            ),
            "require termination and PAD",
        ),
    ),
)
def test_incompatible_or_incomplete_options_fail_before_model_loading(
    arguments: tuple[str, ...],
    message: str,
) -> None:
    with pytest.raises(ValueError, match=message):
        _config(arguments)


def test_help_and_resolved_json_document_exact_on_support(
    capsys: pytest.CaptureFixture[str],
) -> None:
    help_text = build_commit_strategy_parser().format_help()

    assert "--commit-strategy {serial,epic,exact}" in help_text
    assert "exact_on_support" in help_text
    assert "not a full-vocabulary" in help_text

    assert (
        main(
            (
                "--commit-strategy",
                "exact",
                "--exact-support-top-k",
                "2",
                "--exact-eos-policy",
                "absent",
            ),
            environ={},
        )
        == 0
    )
    payload = json.loads(capsys.readouterr().out)
    assert payload["commit_strategy"] == "exact"
    assert payload["exact"]["exactness_scope"] == "exact_on_support"
