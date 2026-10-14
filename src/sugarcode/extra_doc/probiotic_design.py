"""Row 982, Probiotic Design: weighing each culture's load.

A culture carrying a few heavy doses strains more than one spreading
the same total thinly, so the load is squared before it is summed.
brew() totals each culture's squared doses and reports the cultures
whose load stays inside the light limit.

Input rows: (culture 1-8, dose int 0-10).  Light limit is 30.
Output: {'total', 'loads': {culture: sum of squared doses},
'light': sorted cultures loading at most 30}.  Reported: doses 3,
4 load 9 + 16 = 25 and stay light; 4, 4 load 32 and tip over;
5, 2, 1 load exactly 30 and hold the edge; a lone dose loads its
own square; squaring makes big doses count more, so 5, 1 loads 26
while 3, 3 loads 18.
"""

from typing import Any

MAX_ROWS = 100
MAX_NAME = 8
MIN_DOSE = 0
MAX_DOSE = 10
LIGHT = 30

SCOPE = 'PARTIAL: dose bookkeeping only; no fermentation modeled'
NOT_CLAIMED = (
    'does not model bacterial growth',
    'does not weight doses by record order',
    'does not compare cultures against each other',
    'does not cap the load during accumulation',
)


def _check_name(culture: Any, row: int) -> None:
    if not isinstance(culture, str) or type(culture) is not str:
        raise TypeError(
            f'row {row}: culture must be str, got {type(culture).__name__}')
    if not 1 <= len(culture) <= MAX_NAME:
        raise ValueError(f'row {row}: culture must be 1-8 chars')


def _check_dose(dose: Any, row: int) -> None:
    if type(dose) is not int:
        raise TypeError(
            f'row {row}: dose must be int, got {type(dose).__name__}')
    if not MIN_DOSE <= dose <= MAX_DOSE:
        raise ValueError(
            f'row {row}: dose must be {MIN_DOSE}-{MAX_DOSE}, got {dose}')


def brew(rows: Any) -> dict:
    """Return the load summary for the supplied dose records."""
    if type(rows) not in (list, tuple):
        raise TypeError(f'rows must be list or tuple, got {type(rows).__name__}')
    if len(rows) > MAX_ROWS:
        raise ValueError(f'rows must contain at most {MAX_ROWS} entries')
    loads: dict = {}
    for index, row in enumerate(rows, 1):
        if type(row) not in (list, tuple):
            raise TypeError(
                f'row {index}: expected (culture, dose) tuple, got {type(row).__name__}')
        if len(row) != 2:
            raise ValueError(
                f'row {index}: expected 2 fields, got {len(row)}')
        culture, dose = row
        _check_name(culture, index)
        _check_dose(dose, index)
        if culture not in loads:
            loads[culture] = 0
        loads[culture] += dose * dose
    light = sorted(culture for culture, load in loads.items()
                   if load <= LIGHT)
    return {'total': len(rows), 'loads': loads, 'light': light}
