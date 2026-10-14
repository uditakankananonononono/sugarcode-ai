"""Row 976, Vaccine Design: checking each vaccine's ladder.

A dose series that climbs without a backward step reads as a clean
prime-boost ladder.  prime() checks whether each vaccine's records
strictly increase from one to the next and reports the vaccines that
never break the climb.

Input rows: (vaccine 1-8, dose int 0-10).
Output: {'total', 'ladders': {vaccine: True while every step climbs},
'laddered': sorted vaccines whose records strictly increase}.
Reported: doses 1, 2, 3 ladder cleanly; 1, 3, 2 break the ladder at
the last step; 2, 2 break it because the climb must be strict; a
lone record is a ladder of one; one vaccine's stumble never breaks
another's ladder.
"""

from typing import Any

MAX_ROWS = 100
MAX_NAME = 8
MIN_DOSE = 0
MAX_DOSE = 10

SCOPE = 'PARTIAL: dose bookkeeping only; no immunology modeled'
NOT_CLAIMED = (
    'does not model immune memory',
    'does not weight doses by timing',
    'does not require a minimum record count',
    'does not compare vaccines against each other',
)


def _check_name(vaccine: Any, row: int) -> None:
    if not isinstance(vaccine, str) or type(vaccine) is not str:
        raise TypeError(
            f'row {row}: vaccine must be str, got {type(vaccine).__name__}')
    if not 1 <= len(vaccine) <= MAX_NAME:
        raise ValueError(f'row {row}: vaccine must be 1-8 chars')


def _check_dose(dose: Any, row: int) -> None:
    if type(dose) is not int:
        raise TypeError(
            f'row {row}: dose must be int, got {type(dose).__name__}')
    if not MIN_DOSE <= dose <= MAX_DOSE:
        raise ValueError(
            f'row {row}: dose must be {MIN_DOSE}-{MAX_DOSE}, got {dose}')


def prime(rows: Any) -> dict:
    """Return the ladder summary for the supplied dose records."""
    if type(rows) not in (list, tuple):
        raise TypeError(f'rows must be list or tuple, got {type(rows).__name__}')
    if len(rows) > MAX_ROWS:
        raise ValueError(f'rows must contain at most {MAX_ROWS} entries')
    previous: dict = {}
    ladders: dict = {}
    for index, row in enumerate(rows, 1):
        if type(row) not in (list, tuple):
            raise TypeError(
                f'row {index}: expected (vaccine, dose) tuple, got {type(row).__name__}')
        if len(row) != 2:
            raise ValueError(
                f'row {index}: expected 2 fields, got {len(row)}')
        vaccine, dose = row
        _check_name(vaccine, index)
        _check_dose(dose, index)
        if vaccine not in previous:
            ladders[vaccine] = True
        elif dose <= previous[vaccine]:
            ladders[vaccine] = False
        previous[vaccine] = dose
    laddered = sorted(vaccine for vaccine, ok in ladders.items() if ok)
    return {'total': len(rows), 'ladders': ladders, 'laddered': laddered}
