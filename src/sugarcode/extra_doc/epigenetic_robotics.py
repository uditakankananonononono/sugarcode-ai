"""Row 944, Epigenetic Robotics: crossing an expression threshold.

Development through interaction: each supplied record adds its signal
value to a robot's running expression, minus a resting decay, and a
robot's development is reported at the first step where the running
expression reaches the crossing level.  interact() returns, per robot,
the 1-based record index of that first crossing.

Input rows: (robot 1-8, signal int 0-10).  Each record contributes
signal - 2 to the robot's running expression.  Output:
{'total', 'crossed': {robot: first crossing step}, 'uncrossed': sorted
robots that never cross}.  Reported: signals of 4 then 3 cross at step 2
(2, then 3 with the decay applied); a signal of 2 is neutral and never
crosses on its own; once crossed, a robot keeps its first crossing step.
"""

from typing import Any

MAX_ROWS = 100
MAX_NAME = 8
MIN_SIGNAL = 0
MAX_SIGNAL = 10
DECAY = 2
CROSS = 3

SCOPE = 'PARTIAL: threshold crossing only; no methylation dynamics modeled'
NOT_CLAIMED = (
    'does not model gene regulatory networks',
    'does not implement reversible silencing marks',
    'does not couple expression back into the signals',
    'does not model development after the first crossing',
)


def _check_name(robot: Any, row: int, field: str) -> None:
    if not isinstance(robot, str) or type(robot) is not str:
        raise TypeError(
            f'row {row}: {field} must be str, got {type(robot).__name__}')
    if not 1 <= len(robot) <= MAX_NAME:
        raise ValueError(f'row {row}: {field} must be 1-8 chars')


def _check_signal(signal: Any, row: int) -> None:
    if type(signal) is not int:
        raise TypeError(
            f'row {row}: signal must be int, got {type(signal).__name__}')
    if not MIN_SIGNAL <= signal <= MAX_SIGNAL:
        raise ValueError(
            f'row {row}: signal must be {MIN_SIGNAL}-{MAX_SIGNAL}, got {signal}')


def interact(rows: Any) -> dict:
    """Return the first-crossing summary for the supplied interactions."""
    if type(rows) not in (list, tuple):
        raise TypeError(f'rows must be list or tuple, got {type(rows).__name__}')
    if len(rows) > MAX_ROWS:
        raise ValueError(f'rows must contain at most {MAX_ROWS} entries')
    running: dict = {}
    crossed: dict = {}
    for index, row in enumerate(rows, 1):
        if type(row) not in (list, tuple):
            raise TypeError(
                f'row {index}: expected (robot, signal) tuple, got {type(row).__name__}')
        if len(row) != 2:
            raise ValueError(
                f'row {index}: expected 2 fields, got {len(row)}')
        robot, signal = row
        _check_name(robot, index, 'robot')
        _check_signal(signal, index)
        running[robot] = running.get(robot, 0) + signal - DECAY
        if running[robot] >= CROSS and robot not in crossed:
            crossed[robot] = index
    uncrossed = sorted(
        robot for robot in running if robot not in crossed)
    return {'total': len(rows), 'crossed': dict(crossed), 'uncrossed': uncrossed}
