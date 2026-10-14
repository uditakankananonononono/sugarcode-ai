"""First-bad-row pin for row 1907, Title: Art History.

Additive pin on top of the graded tests for row 1907: with two
bad rows, the error must name row 1 (kills validation wrapped
in reversed(list(enumerate(rows, 1)))). Depends on the graded
module and the graded test files; removes nothing.
"""
import pytest

from sugarcode.extra_doc import art_history as mod


def test_first_bad_row_is_named():
    with pytest.raises(ValueError) as info:
        mod.crown_periods([('', 't', 1), ('', 't', 1)])
    assert str(info.value).startswith('row 1: ')
