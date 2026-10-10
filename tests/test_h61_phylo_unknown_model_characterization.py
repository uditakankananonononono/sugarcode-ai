"""H61: one literal unknown-model diagnostic, not model validation."""

import pytest

from sugarcode.bio.phylo import distance_matrix


def test_unknown_model_rejects_even_with_empty_alignment():
    with pytest.raises(ValueError) as caught:
        distance_matrix({}, "bad")
    assert type(caught.value) is ValueError
    assert str(caught.value) == (
        "model must be one of ['jc69', 'k80', 'pdistance'], got 'bad'"
    )
