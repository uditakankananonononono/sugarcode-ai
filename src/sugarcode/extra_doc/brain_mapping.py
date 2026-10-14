"""Row 1002, Brain Mapping: sounding each region's middle.

A region is hollow when signals keep landing strictly inside
its own span, not at the edges.  chart() counts each region's
signals that sit strictly between its own minimum and maximum
and reports the regions with a crowded middle.

Input rows: (region 1-8, signal int 0-10).  Hollow is 2
interior signals.
Output: {'total', 'interior': {region: signals strictly
inside its own span}, 'hollow': sorted regions with 2
interior signals}.  Reported: signals 1, 5, 3, 2 crowd 2
and read hollow; 5, 5 crowd 0; 1, 2, 3 crowd 1; 1, 1, 2
crowd 0; 1, 3, 3 crowd 0; 0, 10, 5, 5 crowd 2; 0, 5, 10
crowd 1; a lone signal crowds 0.
"""

from typing import Any

MAX_ROWS = 100
MAX_NAME = 8
MIN_SIGNAL = 0
MAX_SIGNAL = 10
HOLLOW = 2

SCOPE = 'PARTIAL: signal bookkeeping only; no atlas projection modeled'
NOT_CLAIMED = (
    'does not model coordinate systems',
    'does not count signals at the edges of the span',
    'does not weight interior signals by depth',
    'does not compare regions against each other',
)


def _check_name(region: Any, row: int) -> None:
    if not isinstance(region, str) or type(region) is not str:
        raise TypeError(
            f'row {row}: region must be str, got {type(region).__name__}')
    if not 1 <= len(region) <= MAX_NAME:
        raise ValueError(f'row {row}: region must be 1-8 chars')


def _check_signal(signal: Any, row: int) -> None:
    if type(signal) is not int:
        raise TypeError(
            f'row {row}: signal must be int, got {type(signal).__name__}')
    if not MIN_SIGNAL <= signal <= MAX_SIGNAL:
        raise ValueError(
            f'row {row}: signal must be {MIN_SIGNAL}-{MAX_SIGNAL}, got {signal}')


def chart(rows: Any) -> dict:
    """Return the interior summary for the supplied signal records."""
    if type(rows) not in (list, tuple):
        raise TypeError(f'rows must be list or tuple, got {type(rows).__name__}')
    if len(rows) > MAX_ROWS:
        raise ValueError(f'rows must contain at most {MAX_ROWS} entries')
    values: dict = {}
    for index, row in enumerate(rows, 1):
        if type(row) not in (list, tuple):
            raise TypeError(
                f'row {index}: expected (region, signal) tuple, got {type(row).__name__}')
        if len(row) != 2:
            raise ValueError(
                f'row {index}: expected 2 fields, got {len(row)}')
        region, signal = row
        _check_name(region, index)
        _check_signal(signal, index)
        values.setdefault(region, []).append(signal)
    interior = {}
    for region, vals in values.items():
        lo = min(vals)
        hi = max(vals)
        count = 0
        for v in vals:
            if lo < v < hi:
                count += 1
        interior[region] = count
    hollow = sorted(region for region, count in interior.items()
                    if count >= HOLLOW)
    return {'total': len(rows), 'interior': interior, 'hollow': hollow}
