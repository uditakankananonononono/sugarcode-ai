"""H67: literal whitespace-only consensus rejection only."""

import pytest

from sugarcode.bio.motif import from_iupac


def test_blank_consensus_rejects_with_exact_empty_diagnostic():
    with pytest.raises(ValueError) as caught:
        from_iupac(" \t\n")
    assert type(caught.value) is ValueError
    assert str(caught.value) == "empty consensus"
