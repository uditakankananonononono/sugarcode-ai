"""H62: one literal lower-min-samples diagnostic, not filter validation."""

import pytest

from sugarcode.bio.rnaseq import filter_genes


def test_zero_min_samples_rejects_with_literal_diagnostic():
    with pytest.raises(ValueError) as caught:
        filter_genes(
            {"genes": ["g"], "samples": ["s"], "counts": [[10]]},
            min_samples=0,
        )
    assert type(caught.value) is ValueError
    assert str(caught.value) == "min_samples must be 1..1, got 0"
