"""H76: one literal empty-list rejection only."""

import pytest

from sugarcode.bio.pwm import build_pwm


def test_empty_sequence_list_rejects_with_exact_diagnostic():
    with pytest.raises(ValueError) as caught:
        build_pwm([])
    assert type(caught.value) is ValueError
    assert str(caught.value) == "no sequences"
