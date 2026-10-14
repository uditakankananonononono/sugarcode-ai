"""Row 975, Antibody Design: measuring each antibody's churn.

An antibody whose affinity jumps around is hard to trust, so the
total ground it covers matters more than where it ends.  bind() sums
each antibody's absolute affinity changes between its consecutive
records and reports the antibodies whose churn stays inside the calm
limit.

Input rows: (antibody 1-8, affinity int 0-10).  Calm limit is 4.
Output: {'total', 'churn': {antibody: sum of absolute consecutive
changes}, 'calm': sorted antibodies churning at most 4}.  Reported:
affinities 2, 5, 1 churn 3 + 4 = 7 and lose calm; 3, 3, 3 churn 0
and stay calm; a lone record churns 0; a churn of exactly 4 still
counts calm; the order matters, so 1, 5, 2 churns 7 while 1, 2, 5
churns 4.
"""

from typing import Any

MAX_ROWS = 100
MAX_NAME = 8
MIN_AFFINITY = 0
MAX_AFFINITY = 10
CALM = 4

SCOPE = 'PARTIAL: affinity bookkeeping only; no binding chemistry modeled'
NOT_CLAIMED = (
    'does not model epitope recognition',
    'does not decay affinity between records',
    'does not compare antibodies against each other',
    'does not cap the churn during accumulation',
)


def _check_name(antibody: Any, row: int) -> None:
    if not isinstance(antibody, str) or type(antibody) is not str:
        raise TypeError(
            f'row {row}: antibody must be str, got {type(antibody).__name__}')
    if not 1 <= len(antibody) <= MAX_NAME:
        raise ValueError(f'row {row}: antibody must be 1-8 chars')


def _check_affinity(affinity: Any, row: int) -> None:
    if type(affinity) is not int:
        raise TypeError(
            f'row {row}: affinity must be int, got {type(affinity).__name__}')
    if not MIN_AFFINITY <= affinity <= MAX_AFFINITY:
        raise ValueError(
            f'row {row}: affinity must be {MIN_AFFINITY}-{MAX_AFFINITY}, got {affinity}')


def bind(rows: Any) -> dict:
    """Return the churn summary for the supplied affinity records."""
    if type(rows) not in (list, tuple):
        raise TypeError(f'rows must be list or tuple, got {type(rows).__name__}')
    if len(rows) > MAX_ROWS:
        raise ValueError(f'rows must contain at most {MAX_ROWS} entries')
    last: dict = {}
    churn: dict = {}
    for index, row in enumerate(rows, 1):
        if type(row) not in (list, tuple):
            raise TypeError(
                f'row {index}: expected (antibody, affinity) tuple, got {type(row).__name__}')
        if len(row) != 2:
            raise ValueError(
                f'row {index}: expected 2 fields, got {len(row)}')
        antibody, affinity = row
        _check_name(antibody, index)
        _check_affinity(affinity, index)
        if antibody not in last:
            churn[antibody] = 0
        else:
            churn[antibody] += abs(affinity - last[antibody])
        last[antibody] = affinity
    calm = sorted(antibody for antibody, total in churn.items()
                  if total <= CALM)
    return {'total': len(rows), 'churn': churn, 'calm': calm}
