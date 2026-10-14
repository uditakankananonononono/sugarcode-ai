"""Additive first-bad-row validation-order pins for row 1963 (ai_assurance_coverage).

The landed battery pins each failure class and the cross-class order
(rows type, size, parameter, shape, label, x, y, duplicates), but every
invalid case had exactly one bad row, so a reversed validation loop (last
bad row raised first) survived. Error messages carry no row index, so the
pins use two differently-bad rows whose classes differ. Also pins that
Fraction values (Fraction(0) == 0) are not ints. New file only.
"""

import pytest
from fractions import Fraction

from sugarcode.extra_doc import ai_assurance_coverage as mod

LA = 'label must be a printable ASCII string of 1 to 12 characters'
X = 'x must be a nonbool integer between 0 and 10'
Y = 'y must be a nonbool integer between 0 and 10'
PA = 'percent must be a nonbool integer between 0 and 100'


def _raises(exc, message, *args):
    with pytest.raises(exc) as info:
        mod.ai_assurance_coverage(*args)
    assert str(info.value) == message


def test_first_bad_row_wins_over_later_bad_row():
    # forward: row 1 bad x; reversed would raise row 2's label error
    _raises(ValueError, X, [('a', None, 10), (None, 0, 10)])
    # forward: row 1 bad label; reversed would raise row 2's x error
    _raises(ValueError, LA, [(None, 0, 10), ('a', None, 10)])
    # forward: row 1 bad y; reversed would raise row 3's label error
    _raises(ValueError, Y, [('a', 0, None), ('b', 0, 10), (None, 0, 10)])


def test_fraction_values_are_not_ints():
    # Fraction(0) == 0 and Fraction(1) == 1, but type() is not int
    _raises(ValueError, X, [('a', Fraction(0, 1), 10)])
    _raises(ValueError, Y, [('a', 0, Fraction(1, 1))])
