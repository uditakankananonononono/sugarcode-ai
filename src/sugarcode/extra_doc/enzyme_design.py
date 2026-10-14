"""Row 974, Enzyme Design: fielding each enzyme's runner-up rate.

A catalyst that only fired once might have been lucky, so the second
best record says more about repeatable form than the best one.
catalyze() takes each enzyme's second best rate - its sole rate when
it has only one record - and reports the enzymes whose runner-up
clears the depth floor.

Input rows: (enzyme 1-8, rate int 0-10).  Depth floor is 6.
Output: {'total', 'runners': {enzyme: second best rate, sole rate
when there is only one record}, 'deep': sorted enzymes whose
runner-up is at least 6}.  Reported: rates 9, 5 give a runner of 5;
rates 5, 9, 7 give a runner of 7; a lone rate fields itself as its
own runner; two equal rates 9, 9 give a runner of 9; a runner of
exactly 6 still counts deep.
"""

from typing import Any

MAX_ROWS = 100
MAX_NAME = 8
MIN_RATE = 0
MAX_RATE = 10
DEPTH = 6

SCOPE = 'PARTIAL: rate bookkeeping only; no catalytic mechanism modeled'
NOT_CLAIMED = (
    'does not model substrate affinity',
    'does not weight rates by record order',
    'does not average the rates',
    'does not compare enzymes against each other',
)


def _check_name(enzyme: Any, row: int) -> None:
    if not isinstance(enzyme, str) or type(enzyme) is not str:
        raise TypeError(
            f'row {row}: enzyme must be str, got {type(enzyme).__name__}')
    if not 1 <= len(enzyme) <= MAX_NAME:
        raise ValueError(f'row {row}: enzyme must be 1-8 chars')


def _check_rate(rate: Any, row: int) -> None:
    if type(rate) is not int:
        raise TypeError(
            f'row {row}: rate must be int, got {type(rate).__name__}')
    if not MIN_RATE <= rate <= MAX_RATE:
        raise ValueError(
            f'row {row}: rate must be {MIN_RATE}-{MAX_RATE}, got {rate}')


def catalyze(rows: Any) -> dict:
    """Return the runner-up summary for the supplied rate records."""
    if type(rows) not in (list, tuple):
        raise TypeError(f'rows must be list or tuple, got {type(rows).__name__}')
    if len(rows) > MAX_ROWS:
        raise ValueError(f'rows must contain at most {MAX_ROWS} entries')
    rates: dict = {}
    for index, row in enumerate(rows, 1):
        if type(row) not in (list, tuple):
            raise TypeError(
                f'row {index}: expected (enzyme, rate) tuple, got {type(row).__name__}')
        if len(row) != 2:
            raise ValueError(
                f'row {index}: expected 2 fields, got {len(row)}')
        enzyme, rate = row
        _check_name(enzyme, index)
        _check_rate(rate, index)
        if enzyme not in rates:
            rates[enzyme] = []
        rates[enzyme].append(rate)
    runners: dict = {}
    for enzyme, values in rates.items():
        ordered = sorted(values, reverse=True)
        runners[enzyme] = ordered[1] if len(ordered) > 1 else ordered[0]
    deep = sorted(enzyme for enzyme, runner in runners.items()
                  if runner >= DEPTH)
    return {'total': len(rows), 'runners': runners, 'deep': deep}
