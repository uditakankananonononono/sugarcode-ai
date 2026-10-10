"""One literal empty-query exception-type finding, authored NOT RUN."""
import pytest

from sugarcode.bio.newick import mrca


def test_literal_empty_mrca_query_raises_exact_indexerror_type():
    with pytest.raises(IndexError) as caught:
        mrca({'name': 'A', 'length': None, 'children': []}, [])
    assert type(caught.value) is IndexError
