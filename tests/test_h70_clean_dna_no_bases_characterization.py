"""H70: one literal no-valid-base diagnostic, not general cleaning accuracy."""

import pytest

from sugarcode.bio.sequence import clean_dna


def test_digits_and_hyphen_reject_with_exact_diagnostic():
    with pytest.raises(ValueError) as caught:
        clean_dna('123-')
    assert type(caught.value) is ValueError
    assert str(caught.value) == 'sequence contains no valid DNA bases'
