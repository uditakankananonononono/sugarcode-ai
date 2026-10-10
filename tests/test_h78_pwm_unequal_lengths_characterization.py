"""H78: one literal unequal-length rejection only."""

import pytest

from sugarcode.bio.pwm import build_pwm


def test_longer_second_sequence_rejects_with_exact_diagnostic():
    with pytest.raises(ValueError) as caught:
        build_pwm(["A", "AC"])
    assert type(caught.value) is ValueError
    assert str(caught.value) == "sequences must be aligned to equal length"
