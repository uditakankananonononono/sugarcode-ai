"""H68: one direct invalid-frame diagnostic, not translation accuracy."""

import pytest

from sugarcode.bio.sequence import translate


def test_frame_three_rejects_with_exact_diagnostic():
    with pytest.raises(ValueError) as caught:
        translate('ATG', reading_frame=3)
    assert type(caught.value) is ValueError
    assert str(caught.value) == 'reading_frame must be 0, 1 or 2'
