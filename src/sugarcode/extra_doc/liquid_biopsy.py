"""Row 991, Liquid Biopsy: reading each marker's rise.

A marker matters when readings climb past its own baseline, not
when one high reading arrives first.  detect() takes each marker's
first reading as its baseline, counts the later readings above it,
and reports the markers with repeated rises.

Input rows: (marker 1-8, level int 0-10).  Risen is 2 readings
above baseline.
Output: {'total', 'risers': {marker: readings above its first},
'risen': sorted markers with 2 rises}.  Reported: readings 3, 5,
2, 7 rise twice and mark risen; 3, 3 rise 0 since equal is not
above; 3, 3, 5 rise 1; 5, 3 rise 0; 1, 2 rise 1; 3, 4, 4 rise 2;
10, 0 rise 0; 3, 1, 2 rise 0 because a later dip
does not lower the baseline; a lone reading rises 0; the
baseline itself never counts.
"""

from typing import Any

MAX_ROWS = 100
MAX_NAME = 8
MIN_LEVEL = 0
MAX_LEVEL = 10
RISEN = 2

SCOPE = 'PARTIAL: marker bookkeeping only; no assay chemistry modeled'
NOT_CLAIMED = (
    'does not model marker half-life',
    'does not count the baseline reading itself',
    'does not weight rises by how far they climb',
    'does not compare markers against each other',
)


def _check_name(marker: Any, row: int) -> None:
    if not isinstance(marker, str) or type(marker) is not str:
        raise TypeError(
            f'row {row}: marker must be str, got {type(marker).__name__}')
    if not 1 <= len(marker) <= MAX_NAME:
        raise ValueError(f'row {row}: marker must be 1-8 chars')


def _check_level(level: Any, row: int) -> None:
    if type(level) is not int:
        raise TypeError(
            f'row {row}: level must be int, got {type(level).__name__}')
    if not MIN_LEVEL <= level <= MAX_LEVEL:
        raise ValueError(
            f'row {row}: level must be {MIN_LEVEL}-{MAX_LEVEL}, got {level}')


def detect(rows: Any) -> dict:
    """Return the rise summary for the supplied marker records."""
    if type(rows) not in (list, tuple):
        raise TypeError(f'rows must be list or tuple, got {type(rows).__name__}')
    if len(rows) > MAX_ROWS:
        raise ValueError(f'rows must contain at most {MAX_ROWS} entries')
    values: dict = {}
    for index, row in enumerate(rows, 1):
        if type(row) not in (list, tuple):
            raise TypeError(
                f'row {index}: expected (marker, level) tuple, got {type(row).__name__}')
        if len(row) != 2:
            raise ValueError(
                f'row {index}: expected 2 fields, got {len(row)}')
        marker, level = row
        _check_name(marker, index)
        _check_level(level, index)
        values.setdefault(marker, []).append(level)
    risers = {}
    for marker, vals in values.items():
        base = vals[0]
        count = 0
        for v in vals[1:]:
            if v > base:
                count += 1
        risers[marker] = count
    risen = sorted(marker for marker, count in risers.items()
                   if count >= RISEN)
    return {'total': len(rows), 'risers': risers, 'risen': risen}
