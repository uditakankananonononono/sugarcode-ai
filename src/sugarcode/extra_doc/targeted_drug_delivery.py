"""Row 989, Targeted Drug Delivery: counting each target's courses.

A target is ready when its delivered doses add up to full courses,
not when one big dose arrives.  deliver() pools each target's own
doses, divides the pool into full courses, and reports the targets
holding enough courses.

Input rows: (target 1-8, dose int 0-10).  A course is 4 dose
units; ready is 2 courses.
Output: {'total', 'courses': {target: full courses its doses
buy}, 'ready': sorted targets holding 2 courses}.  Reported:
doses 3, 3, 3 pool to 9 and buy 2 courses, so the target is
ready; 4 buys 1; 4, 4 buy 2 and ready; 7 buys 1; 8 buys 2 and
readies; 3 alone buys 0; 3, 4 pool to 7 and buy 1; a zero dose
buys 0; leftovers never round up.
"""

from typing import Any

MAX_ROWS = 100
MAX_NAME = 8
MIN_DOSE = 0
MAX_DOSE = 10
COURSE = 4
READY = 2

SCOPE = 'PARTIAL: dose bookkeeping only; no pharmacokinetics modeled'
NOT_CLAIMED = (
    'does not model dose timing or intervals',
    'does not weight doses by record order',
    'does not round leftover units up to a course',
    'does not compare targets against each other',
)


def _check_name(target: Any, row: int) -> None:
    if not isinstance(target, str) or type(target) is not str:
        raise TypeError(
            f'row {row}: target must be str, got {type(target).__name__}')
    if not 1 <= len(target) <= MAX_NAME:
        raise ValueError(f'row {row}: target must be 1-8 chars')


def _check_dose(dose: Any, row: int) -> None:
    if type(dose) is not int:
        raise TypeError(
            f'row {row}: dose must be int, got {type(dose).__name__}')
    if not MIN_DOSE <= dose <= MAX_DOSE:
        raise ValueError(
            f'row {row}: dose must be {MIN_DOSE}-{MAX_DOSE}, got {dose}')


def deliver(rows: Any) -> dict:
    """Return the course summary for the supplied dose records."""
    if type(rows) not in (list, tuple):
        raise TypeError(f'rows must be list or tuple, got {type(rows).__name__}')
    if len(rows) > MAX_ROWS:
        raise ValueError(f'rows must contain at most {MAX_ROWS} entries')
    totals: dict = {}
    for index, row in enumerate(rows, 1):
        if type(row) not in (list, tuple):
            raise TypeError(
                f'row {index}: expected (target, dose) tuple, got {type(row).__name__}')
        if len(row) != 2:
            raise ValueError(
                f'row {index}: expected 2 fields, got {len(row)}')
        target, dose = row
        _check_name(target, index)
        _check_dose(dose, index)
        totals.setdefault(target, 0)
        totals[target] += dose
    courses = {target: tot // COURSE for target, tot in totals.items()}
    ready = sorted(target for target, c in courses.items() if c >= READY)
    return {'total': len(rows), 'courses': courses, 'ready': ready}
