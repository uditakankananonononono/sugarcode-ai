"""First-bad-row pin for row 1894, Title: Corpus Linguistics.

Additive pin on top of the graded tests for row 1894: with two
bad rows, the error must name row 1 (kills validation wrapped
in reversed(list(enumerate(rows, 1)))). Depends on the graded
module and the graded test files; removes nothing.
"""
import pytest

from sugarcode.extra_doc import corpus_linguistics as mod


def test_first_bad_row_is_named():
    with pytest.raises(ValueError) as info:
        mod.analyze_corpus([('', 't', 1), ('', 't', 1)])
    assert str(info.value).startswith('row 1: ')
