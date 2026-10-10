"""One unrecognized first-attribute literal, no parser behavior change."""
import pytest
from sugarcode.bio.gff import parse_gff


def test_literal_unrecognized_bad_exact_error():
    with pytest.raises(ValueError) as caught:
        parse_gff('chr1\ta\tgene\t1\t9\t.\t+\t.\tbad')
    assert type(caught.value) is ValueError
    assert str(caught.value) == "line 1: unrecognized attribute syntax 'bad'"
