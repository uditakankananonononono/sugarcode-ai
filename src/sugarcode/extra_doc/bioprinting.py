"""Row 960, Bioprinting: keeping the layers bottom-up.

A print head lays living tissue from the build plate upward: every
new layer must sit at or above the one before it, or the tissue
sags.  extrude() walks the supplied height records per head, counts
the layers that drop below the previous one, and reports which heads
printed cleanly.

Input rows: (head 1-8, height int 0-10).  Output: {'total', 'drops':
{head: count of layers below the previous layer}, 'layered': sorted
heads with no drop, 'tops': {head: final height}}.  Reported: heights
2, 5, 5, 3 drop once (the 3 below the 5); equal heights never count
as a drop; a head with one record always layers cleanly; a drop is
measured against the immediately previous record, not the peak.
"""

from typing import Any

MAX_ROWS = 100
MAX_NAME = 8
MIN_HEIGHT = 0
MAX_HEIGHT = 10

SCOPE = 'PARTIAL: layer-order bookkeeping only; no tissue biology modeled'
NOT_CLAIMED = (
    'does not model cell viability',
    'does not simulate bioink rheology',
    'does not plan print paths',
    'does not compare a layer to anything but the previous layer',
)


def _check_name(head: Any, row: int) -> None:
    if not isinstance(head, str) or type(head) is not str:
        raise TypeError(
            f'row {row}: head must be str, got {type(head).__name__}')
    if not 1 <= len(head) <= MAX_NAME:
        raise ValueError(f'row {row}: head must be 1-8 chars')


def _check_height(height: Any, row: int) -> None:
    if type(height) is not int:
        raise TypeError(
            f'row {row}: height must be int, got {type(height).__name__}')
    if not MIN_HEIGHT <= height <= MAX_HEIGHT:
        raise ValueError(
            f'row {row}: height must be {MIN_HEIGHT}-{MAX_HEIGHT}, got {height}')


def extrude(rows: Any) -> dict:
    """Return the layering summary for the supplied height records."""
    if type(rows) not in (list, tuple):
        raise TypeError(f'rows must be list or tuple, got {type(rows).__name__}')
    if len(rows) > MAX_ROWS:
        raise ValueError(f'rows must contain at most {MAX_ROWS} entries')
    drops: dict = {}
    previous: dict = {}
    for index, row in enumerate(rows, 1):
        if type(row) not in (list, tuple):
            raise TypeError(
                f'row {index}: expected (head, height) tuple, got {type(row).__name__}')
        if len(row) != 2:
            raise ValueError(
                f'row {index}: expected 2 fields, got {len(row)}')
        head, height = row
        _check_name(head, index)
        _check_height(height, index)
        drops.setdefault(head, 0)
        if head in previous and height < previous[head]:
            drops[head] += 1
        previous[head] = height
    layered = sorted(head for head in drops if drops[head] == 0)
    return {'total': len(rows), 'drops': dict(drops), 'layered': layered,
            'tops': dict(previous)}
