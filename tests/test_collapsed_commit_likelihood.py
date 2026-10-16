"""Independent rational laws; no optional neural/GPU package imported."""

from importlib import import_module

CollapsedActionTests = import_module(
    "attempts.52-collapsed-commit-likelihood.work.test_reference"
).CollapsedActionTests

SmoothActionTests = import_module(
    "attempts.52-collapsed-commit-likelihood.work.test_smooth"
).SmoothActionTests

AnchorActionTests = import_module(
    "attempts.52-collapsed-commit-likelihood.work.test_anchor"
).AnchorActionTests

NumericConsumerTests = import_module(
    "attempts.52-collapsed-commit-likelihood.work.test_numeric_json"
).NumericConsumerTests

FloatingCPUConsumerTests = import_module(
    "attempts.52-collapsed-commit-likelihood.work.test_floating_cpu"
).FloatingCPUConsumerTests

ConsumerControlTests = import_module(
    "attempts.52-collapsed-commit-likelihood.work.test_consumer_controls"
).ConsumerControlTests

CompactPlannerTests = import_module(
    "attempts.52-collapsed-commit-likelihood.work.test_compact_planner"
).CompactPlannerTests

TwoStageTests = import_module(
    "attempts.52-collapsed-commit-likelihood.work.test_two_stage"
).TwoStageTests

VarianceGroupTests = import_module(
    "attempts.52-collapsed-commit-likelihood.work.test_variance_groups"
).VarianceGroupTests

StoppingTests = import_module(
    "attempts.52-collapsed-commit-likelihood.work.test_stopping"
).StoppingTests

PrefixAnchorTests = import_module(
    "attempts.52-collapsed-commit-likelihood.work.test_prefix_anchor"
).PrefixAnchorTests

PrefixFloatingTests = import_module(
    "attempts.52-collapsed-commit-likelihood.work.test_prefix_floating"
).PrefixFloatingTests

PrefixRuntimeTests = import_module(
    "attempts.52-collapsed-commit-likelihood.work.test_prefix_runtime"
).PrefixRuntimeTests

VisibleELBOTests = import_module(
    "attempts.52-collapsed-commit-likelihood.work.test_visible_elbo"
).VisibleELBOTests

LLaDASuffixTests = import_module(
    "attempts.52-collapsed-commit-likelihood.work.test_llada_suffix_v10"
).LLaDASuffixTests

CaptureOccupancyTests = import_module(
    "attempts.52-collapsed-commit-likelihood.work.test_capture_occupancy_v10"
).CaptureOccupancyTests

ProposalControlTests = import_module(
    "attempts.52-collapsed-commit-likelihood.work.test_proposal_control"
).ProposalControlTests

NumericProxyTests = import_module(
    "attempts.52-collapsed-commit-likelihood.work.test_numeric_proxy"
).NumericProxyTests
