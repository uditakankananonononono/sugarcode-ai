"""Row 984, Immunotherapy: beating each cell's average.

A cell is primed when enough of its markers rise above its own
typical level, so the average sets the bar.  engage() averages each
cell's markers - the fractional part dropped - counts how many
records beat that bar strictly, and reports the cells with enough
beats to read as primed.

Input rows: (cell 1-8, marker int 0-10).  Primed means 2 beats.
Output: {'total', 'elevated': {cell: records strictly above its own
floor average}, 'primed': sorted cells with at least 2 beats}.
Reported: markers 2, 4, 6 average 4 and one record beats it;
4, 4, 4 average 4 and none beats it because beating must be strict;
1, 4, 4 average 3 and two beat it, priming the cell; 1, 2 average
1, the fractional part dropped, and one beats it; a lone marker
averages itself and never beats.
"""

from typing import Any

MAX_ROWS = 100
MAX_NAME = 8
MIN_MARKER = 0
MAX_MARKER = 10
PRIMED = 2

SCOPE = 'PARTIAL: marker bookkeeping only; no immune response modeled'
NOT_CLAIMED = (
    'does not model T-cell activation',
    'does not weight markers by record order',
    'does not round the average to nearest',
    'does not compare cells against each other',
)


def _check_name(cell: Any, row: int) -> None:
    if not isinstance(cell, str) or type(cell) is not str:
        raise TypeError(
            f'row {row}: cell must be str, got {type(cell).__name__}')
    if not 1 <= len(cell) <= MAX_NAME:
        raise ValueError(f'row {row}: cell must be 1-8 chars')


def _check_marker(marker: Any, row: int) -> None:
    if type(marker) is not int:
        raise TypeError(
            f'row {row}: marker must be int, got {type(marker).__name__}')
    if not MIN_MARKER <= marker <= MAX_MARKER:
        raise ValueError(
            f'row {row}: marker must be {MIN_MARKER}-{MAX_MARKER}, got {marker}')


def engage(rows: Any) -> dict:
    """Return the elevated summary for the supplied marker records."""
    if type(rows) not in (list, tuple):
        raise TypeError(f'rows must be list or tuple, got {type(rows).__name__}')
    if len(rows) > MAX_ROWS:
        raise ValueError(f'rows must contain at most {MAX_ROWS} entries')
    values: dict = {}
    for index, row in enumerate(rows, 1):
        if type(row) not in (list, tuple):
            raise TypeError(
                f'row {index}: expected (cell, marker) tuple, got {type(row).__name__}')
        if len(row) != 2:
            raise ValueError(
                f'row {index}: expected 2 fields, got {len(row)}')
        cell, marker = row
        _check_name(cell, index)
        _check_marker(marker, index)
        if cell not in values:
            values[cell] = []
        values[cell].append(marker)
    elevated: dict = {}
    for cell, markers in values.items():
        average = sum(markers) // len(markers)
        elevated[cell] = sum(1 for marker in markers if marker > average)
    primed = sorted(cell for cell, beats in elevated.items()
                    if beats >= PRIMED)
    return {'total': len(rows), 'elevated': elevated, 'primed': primed}
