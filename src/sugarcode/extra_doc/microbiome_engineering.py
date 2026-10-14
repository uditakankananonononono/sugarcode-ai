"""Row 981, Microbiome Engineering: timing each strain's summit.

A strain that reaches its peak abundance early reads as established,
while one still climbing at the end is unsettled.  seed() finds the
1-based record position of each strain's highest abundance - the
first one, when the peak repeats - and reports the strains whose
summit comes inside the early window.

Input rows: (strain 1-8, abundance int 0-10).  Early window is
position 2 or sooner.
Output: {'total', 'summits': {strain: position of its first highest
record}, 'early': sorted strains summiting at position 2 or
sooner}.  Reported: abundances 3, 5, 5 summit at record 2, the
first time the peak appears; 5, 3 summit at 1; 1, 2, 3 summit at 3
and miss the early window; a lone record summits at 1; a summit at
record 2 still counts early.
"""

from typing import Any

MAX_ROWS = 100
MAX_NAME = 8
MIN_ABUNDANCE = 0
MAX_ABUNDANCE = 10
EARLY = 2

SCOPE = 'PARTIAL: abundance bookkeeping only; no ecology modeled'
NOT_CLAIMED = (
    'does not model species interactions',
    'does not weight abundance by record order',
    'does not compare strains against each other',
    'does not read records after the summit',
)


def _check_name(strain: Any, row: int) -> None:
    if not isinstance(strain, str) or type(strain) is not str:
        raise TypeError(
            f'row {row}: strain must be str, got {type(strain).__name__}')
    if not 1 <= len(strain) <= MAX_NAME:
        raise ValueError(f'row {row}: strain must be 1-8 chars')


def _check_abundance(abundance: Any, row: int) -> None:
    if type(abundance) is not int:
        raise TypeError(
            f'row {row}: abundance must be int, got {type(abundance).__name__}')
    if not MIN_ABUNDANCE <= abundance <= MAX_ABUNDANCE:
        raise ValueError(
            f'row {row}: abundance must be {MIN_ABUNDANCE}-{MAX_ABUNDANCE}, got {abundance}')


def seed(rows: Any) -> dict:
    """Return the summit summary for the supplied abundance records."""
    if type(rows) not in (list, tuple):
        raise TypeError(f'rows must be list or tuple, got {type(rows).__name__}')
    if len(rows) > MAX_ROWS:
        raise ValueError(f'rows must contain at most {MAX_ROWS} entries')
    counts: dict = {}
    bests: dict = {}
    summits: dict = {}
    for index, row in enumerate(rows, 1):
        if type(row) not in (list, tuple):
            raise TypeError(
                f'row {index}: expected (strain, abundance) tuple, got {type(row).__name__}')
        if len(row) != 2:
            raise ValueError(
                f'row {index}: expected 2 fields, got {len(row)}')
        strain, abundance = row
        _check_name(strain, index)
        _check_abundance(abundance, index)
        counts[strain] = counts.get(strain, 0) + 1
        if strain not in bests or abundance > bests[strain]:
            bests[strain] = abundance
            summits[strain] = counts[strain]
    early = sorted(strain for strain, position in summits.items()
                   if position <= EARLY)
    return {'total': len(rows), 'summits': summits, 'early': early}
