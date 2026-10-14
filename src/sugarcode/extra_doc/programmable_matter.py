"""Row 952, Programmable Matter: finding cells under stress.

A sheet of programmable matter holds a level per cell, and a cell is
under stress when its average level deviates from the sheet-wide average
by more than two.  morph() averages each cell's records, compares them
against the global average with exact integer arithmetic, and lists the
stressed cells.

Input rows: (cell 1-8, level int 0-10).  Output: {'total', 'cells',
'mean': global level average rounded down, 'stress': sorted cells whose
own average deviates from the global average by more than 2}.  Reported:
the comparison is exact - a cell deviating by exactly 2 is not stressed;
per-cell averaging matters, so records (a,2),(a,8),(b,5) leave every
cell at the sheet average and nothing is stressed.
"""

from typing import Any

MAX_ROWS = 100
MAX_NAME = 8
MIN_LEVEL = 0
MAX_LEVEL = 10
TOLERANCE = 2

SCOPE = 'PARTIAL: stress detection only; no actuation or feedback modeled'
NOT_CLAIMED = (
    'does not model cell actuation or locomotion',
    'does not propagate stress between neighbors',
    'does not reshape the sheet',
    'does not weight cells by area',
)


def _check_name(cell: Any, row: int) -> None:
    if not isinstance(cell, str) or type(cell) is not str:
        raise TypeError(
            f'row {row}: cell must be str, got {type(cell).__name__}')
    if not 1 <= len(cell) <= MAX_NAME:
        raise ValueError(f'row {row}: cell must be 1-8 chars')


def _check_level(level: Any, row: int) -> None:
    if type(level) is not int:
        raise TypeError(
            f'row {row}: level must be int, got {type(level).__name__}')
    if not MIN_LEVEL <= level <= MAX_LEVEL:
        raise ValueError(
            f'row {row}: level must be {MIN_LEVEL}-{MAX_LEVEL}, got {level}')


def morph(rows: Any) -> dict:
    """Return the stress summary for the supplied level records."""
    if type(rows) not in (list, tuple):
        raise TypeError(f'rows must be list or tuple, got {type(rows).__name__}')
    if len(rows) > MAX_ROWS:
        raise ValueError(f'rows must contain at most {MAX_ROWS} entries')
    sums: dict = {}
    counts: dict = {}
    total_level = 0
    for index, row in enumerate(rows, 1):
        if type(row) not in (list, tuple):
            raise TypeError(
                f'row {index}: expected (cell, level) tuple, got {type(row).__name__}')
        if len(row) != 2:
            raise ValueError(
                f'row {index}: expected 2 fields, got {len(row)}')
        cell, level = row
        _check_name(cell, index)
        _check_level(level, index)
        sums[cell] = sums.get(cell, 0) + level
        counts[cell] = counts.get(cell, 0) + 1
        total_level += level
    n = len(rows)
    mean = total_level // n if n else 0
    stress = sorted(
        cell for cell, cell_sum in sums.items()
        if abs(cell_sum * n - total_level * counts[cell])
        > TOLERANCE * n * counts[cell])
    return {'total': n, 'cells': len(sums), 'mean': mean, 'stress': stress}
