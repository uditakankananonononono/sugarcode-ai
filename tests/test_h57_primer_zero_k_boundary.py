"""One equality-zero guard diagnostic, not thermodynamic validation."""
import pytest

from sugarcode.bio.primer import tm_nn


def test_equal_half_template_rejects_zero_k():
    with pytest.raises(ValueError) as caught:
        tm_nn('ACGT', primer_nm=10, template_nm=20)
    assert type(caught.value) is ValueError
    assert str(caught.value) == 'primer_nm must exceed template_nm / 2'
