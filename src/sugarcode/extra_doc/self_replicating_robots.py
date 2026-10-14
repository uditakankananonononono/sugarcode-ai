"""Row 950, Self-Replicating Robots: drifting off the parent code.

A self-replicating robot copies its code into each offspring, and a
replication whose code differs from the previous one is a mutation.
replicate() walks each robot's replication records in order, counts the
code changes between consecutive replications, and reports which
lineages stayed stable.

Input rows: (robot 1-8, code int 0-10).  Output: {'total', 'mutations':
{robot: code changes between consecutive records}, which lists only
robots with at least one change (a robot with no change is absent, not
zero), 'stable': sorted robots with at least 2 records and no change,
'drifted': sorted robots with at least 1 change}.  Reported: codes
1,2,1 drift twice even though
the first and last codes match - every consecutive pair counts, not the
endpoints; a robot seen once is neither stable nor drifted.
"""

from typing import Any

MAX_ROWS = 100
MAX_NAME = 8
MIN_CODE = 0
MAX_CODE = 10
MIN_RECORDS = 2

SCOPE = 'PARTIAL: copy-fidelity accounting only; no construction modeled'
NOT_CLAIMED = (
    'does not model physical self-assembly',
    'does not simulate resource gathering for replication',
    'does not model selection between lineages',
    'does not track offspring as separate robots',
)


def _check_name(robot: Any, row: int) -> None:
    if not isinstance(robot, str) or type(robot) is not str:
        raise TypeError(
            f'row {row}: robot must be str, got {type(robot).__name__}')
    if not 1 <= len(robot) <= MAX_NAME:
        raise ValueError(f'row {row}: robot must be 1-8 chars')


def _check_code(code: Any, row: int) -> None:
    if type(code) is not int:
        raise TypeError(
            f'row {row}: code must be int, got {type(code).__name__}')
    if not MIN_CODE <= code <= MAX_CODE:
        raise ValueError(
            f'row {row}: code must be {MIN_CODE}-{MAX_CODE}, got {code}')


def replicate(rows: Any) -> dict:
    """Return the copy-fidelity summary for the supplied records."""
    if type(rows) not in (list, tuple):
        raise TypeError(f'rows must be list or tuple, got {type(rows).__name__}')
    if len(rows) > MAX_ROWS:
        raise ValueError(f'rows must contain at most {MAX_ROWS} entries')
    last: dict = {}
    counts: dict = {}
    changes: dict = {}
    for index, row in enumerate(rows, 1):
        if type(row) not in (list, tuple):
            raise TypeError(
                f'row {index}: expected (robot, code) tuple, got {type(row).__name__}')
        if len(row) != 2:
            raise ValueError(
                f'row {index}: expected 2 fields, got {len(row)}')
        robot, code = row
        _check_name(robot, index)
        _check_code(code, index)
        if robot in last and code != last[robot]:
            changes[robot] = changes.get(robot, 0) + 1
        last[robot] = code
        counts[robot] = counts.get(robot, 0) + 1
    stable = sorted(
        robot for robot, count in counts.items()
        if count >= MIN_RECORDS and robot not in changes)
    drifted = sorted(changes)
    return {'total': len(rows), 'mutations': dict(changes),
            'stable': stable, 'drifted': drifted}
