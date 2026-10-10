"""H80: one literal sequence-longer-than-matrix rejection."""

import pytest

from sugarcode.bio.pwm import score


def test_sequence_longer_than_empty_matrix_rejects_with_exact_diagnostic():
    with pytest.raises(ValueError) as caught:
        score("A", [])
    assert type(caught.value) is ValueError
    assert str(caught.value) == "sequence length must equal PWM length"
