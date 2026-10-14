"""Row 953, Metamaterials: tuning cells to a target ratio.

An engineered property appears when the unit cell's geometry hits a
target ratio in lowest terms.  tune() aggregates the supplied pitch and
width per cell, reduces each cell's ratio with the Euclidean algorithm,
and reports the cells tuned to 1:2.

Input rows: (cell 1-8, pitch int 1-10, width int 1-10).  Output:
{'total', 'cells', 'ratios': {cell: [reduced pitch, reduced width]},
'tuned': sorted cells whose reduced ratio is exactly [1, 2]}.
Reported: rows (a,2,4) and (a,1,2) aggregate to 3:6 and reduce to [1,
2]; reduction happens after aggregation, so tuning is a property of the
cell, not of any single record; equal sums reduce to [1, 1].
"""

from typing import Any

MAX_ROWS = 100
MAX_NAME = 8
MIN_DIM = 1
MAX_DIM = 10
TARGET = (1, 2)

SCOPE = 'PARTIAL: geometric ratio tuning only; no EM simulation'
NOT_CLAIMED = (
    'does not simulate electromagnetic response',
    'does not model frequency dependence',
    'does not optimize the geometry',
    'does not handle more than two structural dimensions',
)


def _check_name(cell: Any, row: int) -> None:
    if not isinstance(cell, str) or type(cell) is not str:
        raise TypeError(
            f'row {row}: cell must be str, got {type(cell).__name__}')
    if not 1 <= len(cell) <= MAX_NAME:
        raise ValueError(f'row {row}: cell must be 1-8 chars')


def _check_dim(value: Any, row: int, field: str) -> None:
    if type(value) is not int:
        raise TypeError(
            f'row {row}: {field} must be int, got {type(value).__name__}')
    if not MIN_DIM <= value <= MAX_DIM:
        raise ValueError(
            f'row {row}: {field} must be {MIN_DIM}-{MAX_DIM}, got {value}')


def _gcd(a: int, b: int) -> int:
    while b:
        a, b = b, a % b
    return a


def tune(rows: Any) -> dict:
    """Return the ratio summary for the supplied cell records."""
    if type(rows) not in (list, tuple):
        raise TypeError(f'rows must be list or tuple, got {type(rows).__name__}')
    if len(rows) > MAX_ROWS:
        raise ValueError(f'rows must contain at most {MAX_ROWS} entries')
    pitches: dict = {}
    widths: dict = {}
    for index, row in enumerate(rows, 1):
        if type(row) not in (list, tuple):
            raise TypeError(
                f'row {index}: expected (cell, pitch, width) tuple, got {type(row).__name__}')
        if len(row) != 3:
            raise ValueError(
                f'row {index}: expected 3 fields, got {len(row)}')
        cell, pitch, width = row
        _check_name(cell, index)
        _check_dim(pitch, index, 'pitch')
        _check_dim(width, index, 'width')
        pitches[cell] = pitches.get(cell, 0) + pitch
        widths[cell] = widths.get(cell, 0) + width
    ratios: dict = {}
    tuned = []
    for cell, pitch in pitches.items():
        width = widths[cell]
        factor = _gcd(pitch, width)
        reduced = [pitch // factor, width // factor]
        ratios[cell] = reduced
        if reduced == [TARGET[0], TARGET[1]]:
            tuned.append(cell)
    return {'total': len(rows), 'cells': len(pitches), 'ratios': ratios,
            'tuned': sorted(tuned)}
