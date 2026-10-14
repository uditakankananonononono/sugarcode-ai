"""Row 949, Self-Reconfiguring Robots: settling into symmetric shapes.

A self-reconfiguring robot snaps segments into place one at a time, and
a shape is settled when it reads the same from either end - the robot no
longer needs to move.  reconfigure() builds each robot's segment
sequence in record order and reports which robots settled.

Input rows: (robot 1-8, segment int 0-9).  A robot's shape is its
sequence of supplied segments.  Output: {'total', 'shapes': {robot:
shape length}, 'symmetric': sorted robots whose shape is a palindrome
of length at least 2, 'longest': longest shape length}.  Reported:
segments 1,2,1 settle; 1,1 settles; 1,2 does not; a single segment is
not yet a shape and does not settle.
"""

from typing import Any

MAX_ROWS = 100
MAX_NAME = 8
MIN_SEGMENT = 0
MAX_SEGMENT = 9
MIN_SHAPE = 2

SCOPE = 'PARTIAL: shape symmetry only; no motion planning modeled'
NOT_CLAIMED = (
    'does not plan reconfiguration moves',
    'does not model segment actuation or latching',
    'does not simulate 3D geometry',
    'does not detect shapes shorter than two segments as settled',
)


def _check_name(robot: Any, row: int) -> None:
    if not isinstance(robot, str) or type(robot) is not str:
        raise TypeError(
            f'row {row}: robot must be str, got {type(robot).__name__}')
    if not 1 <= len(robot) <= MAX_NAME:
        raise ValueError(f'row {row}: robot must be 1-8 chars')


def _check_segment(segment: Any, row: int) -> None:
    if type(segment) is not int:
        raise TypeError(
            f'row {row}: segment must be int, got {type(segment).__name__}')
    if not MIN_SEGMENT <= segment <= MAX_SEGMENT:
        raise ValueError(
            f'row {row}: segment must be {MIN_SEGMENT}-{MAX_SEGMENT}, got {segment}')


def reconfigure(rows: Any) -> dict:
    """Return the shape summary for the supplied segment records."""
    if type(rows) not in (list, tuple):
        raise TypeError(f'rows must be list or tuple, got {type(rows).__name__}')
    if len(rows) > MAX_ROWS:
        raise ValueError(f'rows must contain at most {MAX_ROWS} entries')
    shapes: dict = {}
    for index, row in enumerate(rows, 1):
        if type(row) not in (list, tuple):
            raise TypeError(
                f'row {index}: expected (robot, segment) tuple, got {type(row).__name__}')
        if len(row) != 2:
            raise ValueError(
                f'row {index}: expected 2 fields, got {len(row)}')
        robot, segment = row
        _check_name(robot, index)
        _check_segment(segment, index)
        shapes.setdefault(robot, []).append(segment)
    symmetric = sorted(
        robot for robot, shape in shapes.items()
        if len(shape) >= MIN_SHAPE and shape == shape[::-1])
    longest = max((len(shape) for shape in shapes.values()), default=0)
    return {'total': len(rows),
            'shapes': {robot: len(shape) for robot, shape in shapes.items()},
            'symmetric': symmetric, 'longest': longest}
