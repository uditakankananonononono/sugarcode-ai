"""One thirteen-field BED literal, source-derived diagnostic pin only."""
import hashlib
from pathlib import Path
import pytest
from sugarcode.bio import bed


def test_literal_thirteen_fields_exact_error():
    print("LOADED_SOURCE=" + bed.__file__)
    print("LOADED_SOURCE_SHA256=" + hashlib.sha256(Path(bed.__file__).read_bytes()).hexdigest())
    with pytest.raises(ValueError) as caught:
        bed.parse_bed('chr1\t0\t9\tg\t0\t+\t0\t9\t0\t1\t9\t0\textra')
    assert type(caught.value) is ValueError
    assert str(caught.value) == 'line 1: BED record has 13 fields, max 12'
