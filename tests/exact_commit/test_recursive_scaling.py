import pytest

from mwpc_research.branching_study import evaluate_branching_instance
from mwpc_research.recursive_scaling import scaling_instance


@pytest.mark.parametrize("width", [2, 4, 8])
@pytest.mark.parametrize("depth", [0, 1])
def test_scaling_family_small_instances_agree_with_exhaustive_oracle(width, depth):
    instance = scaling_instance(4, width, depth)
    row = evaluate_branching_instance(instance, maximum_paths=4096)
    assert not row["failures"]


def test_scaling_rejects_impossible_fixed_depth():
    with pytest.raises(ValueError):
        scaling_instance(4, 2, 2)
