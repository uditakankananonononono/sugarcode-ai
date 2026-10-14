"""Row 959, 4D Printing: settling toward the programmed shape.

A 4D-printed panel contracts toward its programmed shape: each
observed extension that beats every earlier one marks a settling
event, and the panel keeps settling until no new low appears.
settle() walks the supplied extension records per panel, counts the
strict new lows, and reports each panel's final floor.

Input rows: (panel 1-8, extension int 0-10).  Output: {'total',
'lows': {panel: count of strict new lows}, 'floor': {panel: lowest
extension seen}}.  Reported: extensions 5, 3, 3, 1 settle 3 times (at
5, then 3, then 1) with floor 1; a repeat of the current floor does
not count, only strictly lower extensions do; a single record is
always exactly one low.
"""

from typing import Any

MAX_ROWS = 100
MAX_NAME = 8
MIN_EXTENSION = 0
MAX_EXTENSION = 10

SCOPE = 'PARTIAL: settling bookkeeping only; no shape transformation modeled'
NOT_CLAIMED = (
    'does not model the printed geometry',
    'does not simulate stimulus response over time',
    'does not raise a floor once set',
    'does not predict future extensions',
)


def _check_name(panel: Any, row: int) -> None:
    if not isinstance(panel, str) or type(panel) is not str:
        raise TypeError(
            f'row {row}: panel must be str, got {type(panel).__name__}')
    if not 1 <= len(panel) <= MAX_NAME:
        raise ValueError(f'row {row}: panel must be 1-8 chars')


def _check_extension(extension: Any, row: int) -> None:
    if type(extension) is not int:
        raise TypeError(
            f'row {row}: extension must be int, got {type(extension).__name__}')
    if not MIN_EXTENSION <= extension <= MAX_EXTENSION:
        raise ValueError(
            f'row {row}: extension must be {MIN_EXTENSION}-{MAX_EXTENSION}, got {extension}')


def settle(rows: Any) -> dict:
    """Return the settling summary for the supplied extension records."""
    if type(rows) not in (list, tuple):
        raise TypeError(f'rows must be list or tuple, got {type(rows).__name__}')
    if len(rows) > MAX_ROWS:
        raise ValueError(f'rows must contain at most {MAX_ROWS} entries')
    lows: dict = {}
    floor: dict = {}
    for index, row in enumerate(rows, 1):
        if type(row) not in (list, tuple):
            raise TypeError(
                f'row {index}: expected (panel, extension) tuple, got {type(row).__name__}')
        if len(row) != 2:
            raise ValueError(
                f'row {index}: expected 2 fields, got {len(row)}')
        panel, extension = row
        _check_name(panel, index)
        _check_extension(extension, index)
        if panel not in floor or extension < floor[panel]:
            floor[panel] = extension
            lows[panel] = lows.get(panel, 0) + 1
    return {'total': len(rows), 'lows': dict(lows), 'floor': dict(floor)}
