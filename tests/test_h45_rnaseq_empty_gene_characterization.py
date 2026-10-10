"""H45: two literal empty-gene diagnostics, not format validation."""

import pytest

from sugarcode.bio.rnaseq import parse_counts


@pytest.mark.parametrize(
    "text",
    [
        "\n  \ngene,s1\ng1,2\n \n   ,3\n",
        "\n  \ngene\ts1\ng1\t2\n \n   \t3\n",
    ],
    ids=["csv", "tsv"],
)
def test_empty_gene_uses_nonblank_row_number(text):
    with pytest.raises(ValueError) as caught:
        parse_counts(text)
    assert type(caught.value) is ValueError
    assert str(caught.value) == "line 3: empty gene id"
