"""H69: one literal normalized invalid-code rejection."""

import pytest

from sugarcode.bio.motif import from_iupac


def test_lowercase_invalid_code_rejects_with_exact_normalized_diagnostic():
    with pytest.raises(ValueError) as caught:
        from_iupac("x")
    assert type(caught.value) is ValueError
    assert str(caught.value) == "invalid IUPAC code 'X'"
