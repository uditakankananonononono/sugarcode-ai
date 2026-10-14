"""Row 995, Neural Prosthetics: timing each nerve's calibration.

A nerve is trained when its early firings build on each other,
not when a late surge redeems a shaky start.  fire() walks each
nerve's own firing sequence from the beginning, measures how
long the initial non-decreasing run holds, and reports the
nerves whose calibration lasts.

Input rows: (nerve 1-8, firing int 0-10).  Trained is a
calibration prefix of 3.
Output: {'total', 'prefixes': {nerve: length of its initial
non-decreasing run}, 'trained': sorted nerves calibrated to 3}.
Reported: firings 3, 3, 5, 2, 7 hold for 3 - the later 7 does
not extend the prefix; 1, 0 hold for 1; 5, 5, 5 hold for 3 and
train; 2, 2 hold for 2; 1, 2 hold for 2; 1, 2, 3 hold for 3;
0, 0, 1 hold for 3; 2, 1 hold for 1; a lone firing holds for 1.
"""

from typing import Any

MAX_ROWS = 100
MAX_NAME = 8
MIN_FIRING = 0
MAX_FIRING = 10
TRAINED = 3

SCOPE = 'PARTIAL: firing bookkeeping only; no neural tissue modeled'
NOT_CLAIMED = (
    'does not model membrane potentials',
    'does not let a later rise extend a broken prefix',
    'does not require firings to increase, only not to drop',
    'does not compare nerves against each other',
)


def _check_name(nerve: Any, row: int) -> None:
    if not isinstance(nerve, str) or type(nerve) is not str:
        raise TypeError(
            f'row {row}: nerve must be str, got {type(nerve).__name__}')
    if not 1 <= len(nerve) <= MAX_NAME:
        raise ValueError(f'row {row}: nerve must be 1-8 chars')


def _check_firing(firing: Any, row: int) -> None:
    if type(firing) is not int:
        raise TypeError(
            f'row {row}: firing must be int, got {type(firing).__name__}')
    if not MIN_FIRING <= firing <= MAX_FIRING:
        raise ValueError(
            f'row {row}: firing must be {MIN_FIRING}-{MAX_FIRING}, got {firing}')


def fire(rows: Any) -> dict:
    """Return the calibration summary for the supplied firing records."""
    if type(rows) not in (list, tuple):
        raise TypeError(f'rows must be list or tuple, got {type(rows).__name__}')
    if len(rows) > MAX_ROWS:
        raise ValueError(f'rows must contain at most {MAX_ROWS} entries')
    values: dict = {}
    for index, row in enumerate(rows, 1):
        if type(row) not in (list, tuple):
            raise TypeError(
                f'row {index}: expected (nerve, firing) tuple, got {type(row).__name__}')
        if len(row) != 2:
            raise ValueError(
                f'row {index}: expected 2 fields, got {len(row)}')
        nerve, firing = row
        _check_name(nerve, index)
        _check_firing(firing, index)
        values.setdefault(nerve, []).append(firing)
    prefixes = {}
    for nerve, vals in values.items():
        length = 1
        for i in range(1, len(vals)):
            if vals[i] < vals[i - 1]:
                break
            length += 1
        prefixes[nerve] = length
    trained = sorted(nerve for nerve, length in prefixes.items()
                     if length >= TRAINED)
    return {'total': len(rows), 'prefixes': prefixes, 'trained': trained}
