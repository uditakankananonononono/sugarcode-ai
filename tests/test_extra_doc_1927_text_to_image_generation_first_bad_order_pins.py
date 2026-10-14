"""Additive first-bad-row validation-order pins for row 1927 (text_to_image_generation).

The landed battery pins every single-bad-row position and the field order
within one row, but every multi-row invalid case had exactly one bad row, so
a reversed-enumeration mutant (last bad row raised first) survived. These
pins use two differently-bad rows so the FIRST bad row's error must surface.
New file only; the module and the landed tests are unchanged.
"""

import pytest

from sugarcode.extra_doc import text_to_image_generation as mod


def _raises(exc, message, *args):
    with pytest.raises(exc) as info:
        mod.reduce_steps(*args)
    assert str(info.value) == message


def test_first_bad_row_wins_over_later_bad_row():
    # row 1 bad prompt beats row 3 bad steps; a reversed loop would raise the steps error
    _raises(ValueError, 'row 1: prompt must be a string of 1 to 16 characters',
            [('', 'b', 1), ('c', 'd', 1), ('e', 'f', 0)])
    # row 1 bad steps beats row 3 bad prompt; a reversed loop would raise the prompt error
    _raises(ValueError, 'row 1: steps must be a nonbool integer between 1 and 9',
            [('a', 'b', 0), ('c', 'd', 1), ('', 'f', 1)])


def test_middle_bad_row_wins_over_later_bad_row():
    # row 2 bad prompt beats row 3 bad steps
    _raises(ValueError, 'row 2: prompt must be a string of 1 to 16 characters',
            [('a', 'b', 1), ('', 'd', 1), ('e', 'f', 0)])
    # bad row 2 alone still reports row 2 (sanity that the pins above are order-driven)
    _raises(ValueError, 'row 3: steps must be a nonbool integer between 1 and 9',
            [('a', 'b', 1), ('c', 'd', 1), ('e', 'f', 0)])
