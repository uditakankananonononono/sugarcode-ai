"""Row 965, Gene Therapy: reading the median expression.

A working therapy holds a patient's gene expression at the middle of
its range: the median reading tells the story better than any single
spike.  express() sorts each patient's readings, takes the median -
the lower of the two middle values when the count is even - and
reports which patients hold their median in the stable band.

Input rows: (patient 1-8, expression int 0-10).  Stable band is 4 to
6 inclusive.  Output: {'total', 'medians': {patient: median},
'stable': sorted patients with a median in the band}.  Reported:
readings 3, 5, 8 give median 5 and are stable; readings 3, 5 give
the lower middle 3, not 4; a median of exactly 4 or exactly 6 is
stable; a patient with one reading has that reading as median.
"""

from typing import Any

MAX_ROWS = 100
MAX_NAME = 8
MIN_EXPRESSION = 0
MAX_EXPRESSION = 10
BAND_LOW = 4
BAND_HIGH = 6

SCOPE = 'PARTIAL: median bookkeeping only; no gene regulation modeled'
NOT_CLAIMED = (
    'does not model expression over time',
    'does not compute a mean or mode',
    'does not take the upper middle on even counts',
    'does not adjust readings toward the median',
)


def _check_name(patient: Any, row: int) -> None:
    if not isinstance(patient, str) or type(patient) is not str:
        raise TypeError(
            f'row {row}: patient must be str, got {type(patient).__name__}')
    if not 1 <= len(patient) <= MAX_NAME:
        raise ValueError(f'row {row}: patient must be 1-8 chars')


def _check_expression(expression: Any, row: int) -> None:
    if type(expression) is not int:
        raise TypeError(
            f'row {row}: expression must be int, got {type(expression).__name__}')
    if not MIN_EXPRESSION <= expression <= MAX_EXPRESSION:
        raise ValueError(
            f'row {row}: expression must be {MIN_EXPRESSION}-{MAX_EXPRESSION}, got {expression}')


def express(rows: Any) -> dict:
    """Return the median summary for the supplied expression readings."""
    if type(rows) not in (list, tuple):
        raise TypeError(f'rows must be list or tuple, got {type(rows).__name__}')
    if len(rows) > MAX_ROWS:
        raise ValueError(f'rows must contain at most {MAX_ROWS} entries')
    readings: dict = {}
    for index, row in enumerate(rows, 1):
        if type(row) not in (list, tuple):
            raise TypeError(
                f'row {index}: expected (patient, expression) tuple, got {type(row).__name__}')
        if len(row) != 2:
            raise ValueError(
                f'row {index}: expected 2 fields, got {len(row)}')
        patient, expression = row
        _check_name(patient, index)
        _check_expression(expression, index)
        readings.setdefault(patient, []).append(expression)
    medians = {patient: sorted(values)[(len(values) - 1) // 2]
               for patient, values in readings.items()}
    stable = sorted(patient for patient, median in medians.items()
                    if BAND_LOW <= median <= BAND_HIGH)
    return {'total': len(rows), 'medians': medians, 'stable': stable}
