import pytest
from sugarcode.extra_doc.ubiquitous_language673 import audit as glossary
from sugarcode.extra_doc.aggregate_design674 import audit as aggregate


def test_duplicate_context_term_different_definition():
    with pytest.raises(ValueError) as exc:glossary([('c','t','d1'),('c','t','d2')])
    assert str(exc.value)=='context-term pairs must be unique'


def test_transactions_101_rejected():
    with pytest.raises(ValueError) as exc:aggregate({'a':'x'},[['a']]*101)
    assert str(exc.value)=='transactions must be an exact list with 0..100 entries'
