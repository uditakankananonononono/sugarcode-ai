"""Row 988, Nanomedicine: bonding each particle's coating.

A particle holds when neighbouring sizes grip, not when one big
coat shows up alone.  coat() multiplies each neighbouring pair of
sizes inside the particle's own size list and reports the particles
whose coupling reaches the bonding level.

Input rows: (particle 1-8, size int 0-10).  Bonded is a coupling of
8 or more.
Output: {'total', 'couplings': {particle: sum of neighbouring size
products}, 'bonded': sorted particles coupling to 8 or more}.
Reported: sizes 1, 2, 3 couple to 1*2 + 2*3 = 8 and bond; 2, 2
couple to 4; 1, 1, 6 couple to 7 and do not bond; 3, 3 couple to
9; 3, 0, 3 couple to 0; 1, 2, 3, 4 couple to 2 + 6 + 12 = 20; a
lone size couples to 0; sizes 1, 2, 4 couple to 10 while 2, 4, 1
couple to 12, so order matters.
"""

from typing import Any

MAX_ROWS = 100
MAX_NAME = 8
MIN_SIZE = 0
MAX_SIZE = 10
BOND = 8

SCOPE = 'PARTIAL: coating bookkeeping only; no drug loading modeled'
NOT_CLAIMED = (
    'does not model circulation half-life',
    'does not weight sizes beyond neighbouring pairs',
    'does not compare particles against each other',
    'does not cap how many coats one particle may hold',
)


def _check_name(particle: Any, row: int) -> None:
    if not isinstance(particle, str) or type(particle) is not str:
        raise TypeError(
            f'row {row}: particle must be str, got {type(particle).__name__}')
    if not 1 <= len(particle) <= MAX_NAME:
        raise ValueError(f'row {row}: particle must be 1-8 chars')


def _check_size(size: Any, row: int) -> None:
    if type(size) is not int:
        raise TypeError(
            f'row {row}: size must be int, got {type(size).__name__}')
    if not MIN_SIZE <= size <= MAX_SIZE:
        raise ValueError(
            f'row {row}: size must be {MIN_SIZE}-{MAX_SIZE}, got {size}')


def coat(rows: Any) -> dict:
    """Return the coupling summary for the supplied size records."""
    if type(rows) not in (list, tuple):
        raise TypeError(f'rows must be list or tuple, got {type(rows).__name__}')
    if len(rows) > MAX_ROWS:
        raise ValueError(f'rows must contain at most {MAX_ROWS} entries')
    values: dict = {}
    for index, row in enumerate(rows, 1):
        if type(row) not in (list, tuple):
            raise TypeError(
                f'row {index}: expected (particle, size) tuple, got {type(row).__name__}')
        if len(row) != 2:
            raise ValueError(
                f'row {index}: expected 2 fields, got {len(row)}')
        particle, size = row
        _check_name(particle, index)
        _check_size(size, index)
        values.setdefault(particle, []).append(size)
    couplings = {}
    for particle, vals in values.items():
        coupling = 0
        for i in range(len(vals) - 1):
            coupling += vals[i] * vals[i + 1]
        couplings[particle] = coupling
    bonded = sorted(particle for particle, coupling in couplings.items()
                    if coupling >= BOND)
    return {'total': len(rows), 'couplings': couplings, 'bonded': bonded}
