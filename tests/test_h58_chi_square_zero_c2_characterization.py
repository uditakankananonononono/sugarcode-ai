"""H58: one literal zero-second-column diagnostic, not accuracy validation."""

import pytest

from sugarcode.bio.gstats import chi_square_2x2


def test_zero_second_column_rejects_with_literal_diagnostic():
    with pytest.raises(ValueError) as caught:
        chi_square_2x2(1, 0, 1, 0)
    assert type(caught.value) is ValueError
    assert str(caught.value) == "degenerate table (zero margin)"
