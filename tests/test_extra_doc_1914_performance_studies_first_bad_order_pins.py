"""Additive first-bad-row validation-order pins for row 1914 (performance_studies).

The landed battery pins every single-bad-row position and the field order
within one row, but every multi-row invalid case had exactly one bad row, so
a reversed-enumeration mutant (last bad row raised first) survived. These
pins use two differently-bad rows so the FIRST bad row's error must surface.
New file only; the module and the landed tests are unchanged.
"""

import pytest

from sugarcode.extra_doc import performance_studies as mod


def _raises(exc, message, *args):
    with pytest.raises(exc) as info:
        mod.break_records(*args)
    assert str(info.value) == message


def test_first_bad_row_wins_over_later_bad_row():
    # row 1 bad act beats row 3 bad energy; a reversed loop would raise the energy error
    _raises(ValueError, 'row 1: act must be a string of 1 to 16 characters',
            [('', 'b', 1), ('c', 'd', 1), ('e', 'f', 0)])
    # row 1 bad energy beats row 3 bad act; a reversed loop would raise the act error
    _raises(ValueError, 'row 1: energy must be a nonbool integer between 1 and 9',
            [('a', 'b', 0), ('c', 'd', 1), ('', 'f', 1)])


def test_middle_bad_row_wins_over_later_bad_row():
    # row 2 bad act beats row 3 bad energy
    _raises(ValueError, 'row 2: act must be a string of 1 to 16 characters',
            [('a', 'b', 1), ('', 'd', 1), ('e', 'f', 0)])
    # bad row 2 alone still reports row 2 (sanity that the pins above are order-driven)
    _raises(ValueError, 'row 3: energy must be a nonbool integer between 1 and 9',
            [('a', 'b', 1), ('c', 'd', 1), ('e', 'f', 0)])
