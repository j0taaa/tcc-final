"""Execution-level comparison against the unmodified baseline schedule."""

import pytest

from mwpc_research.matched_schedule import transfer_schedule

torch = pytest.importorskip("torch")
baseline = pytest.importorskip("constrained_diffusion.eval.dllm.models.llada.generate_constrained")


def test_live_observer_keeps_logits_mutable_for_upstream_resampling():
    from scripts.exact_commit.run_nonliteral_live import observed_forward

    result = observed_forward(torch, lambda _: torch.ones(2, requires_grad=True) * 2, None)
    assert not result.requires_grad
    assert not result.is_inference()
    result[0] = -float("inf")
    assert result[0] == -float("inf")


@pytest.mark.parametrize("slots,steps", [(16, 8), (12, 6), (32, 16), (7, 3)])
def test_schedule_equals_the_actual_upstream_transfer_counts(slots: int, steps: int) -> None:
    actual = baseline.get_num_transfer_tokens(torch.ones((1, slots), dtype=torch.bool), steps)
    expected = transfer_schedule(slots, steps)
    assert tuple(actual[0].tolist()) == expected
    assert sum(expected) == slots


def test_exact_driver_passes_each_scheduled_budget_to_the_model_hook(monkeypatch) -> None:
    from types import SimpleNamespace

    from scripts.exact_commit import run_q5_end_to_end as driver

    parameters = driver._configuration_parameters(
        driver.load_experiment_config(
            driver.REPOSITORY_ROOT / "configs/experiments/q5_structured_publication_v4.toml"
        ).parameters,
        publication_mode=True,
    )
    real_tensor = torch.tensor
    # Exercise run_step itself with CPU tensors and a fake hook. Stop only
    # after all eight requests have been observed; no GPU/model is needed.
    fake_torch = SimpleNamespace(
        tensor=lambda *args, **kw: real_tensor(*args, **{**kw, "device": "cpu"}),
        long=torch.long,
        float64=torch.float64,
        inference_mode=torch.inference_mode,
        softmax=torch.softmax,
        isfinite=torch.isfinite,
    )
    budgets = []

    def hook(*args, **kwargs):
        budgets.append(kwargs["k_s"])
        return SimpleNamespace()

    def drive(run_step, *, max_steps):
        for _ in range(max_steps):
            run_step()
        raise StopIteration

    monkeypatch.setattr(driver, "run_llada_exact_step", hook)
    monkeypatch.setattr(driver, "_run_exact_generation_steps", drive)
    call = driver._prepare_exact_call(
        torch=fake_torch,
        model=lambda tokens: SimpleNamespace(logits=torch.zeros((*tokens.shape, 2))),
        tokenizer=SimpleNamespace(decode=lambda *a, **kw: ""),
        prompt_ids=(0,),
        tokenizer_adapter=None,
        grammar=None,
        parameters=parameters,
        support_initial_k=8,
        support_k_max=32,
        solver_timeout_seconds=1,
    )
    with pytest.raises(StopIteration):
        call()
    baseline_budgets = baseline.get_num_transfer_tokens(torch.ones((1, 16), dtype=torch.bool), 8)
    assert budgets == baseline_budgets[0].tolist() == [2] * 8
