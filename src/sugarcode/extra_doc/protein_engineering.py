"""Row 972, Protein Engineering: picking each protein's modal delta.

A protein's character shows in the delta it keeps coming back to, so
the typical change matters more than the occasional one.  fold()
tallies each protein's deltas, picks the most frequent one - the
smallest delta on a tie - and reports the proteins whose modal delta
is at least neutral.

Input rows: (protein 1-8, delta int -5..5).
Output: {'total', 'modes': {protein: most frequent delta, smallest
on a tie}, 'stable': sorted proteins whose modal delta is at least
0}.  Reported: deltas 3, 2, 3, 2 tie and the smaller delta 2 reads
as the mode; deltas -1, -1, 2 give a mode of -1 and lose stable; a
lone delta is its own mode; a mode of exactly 0 still counts stable;
deltas 1, 2, 3 all appear once and the mode is 1.
"""

from typing import Any

MAX_ROWS = 100
MAX_NAME = 8
MIN_DELTA = -5
MAX_DELTA = 5

SCOPE = 'PARTIAL: delta tallying only; no folding physics modeled'
NOT_CLAIMED = (
    'does not model thermodynamic stability',
    'does not weight deltas by record order',
    'does not average the deltas',
    'does not compare proteins against each other',
)


def _check_name(protein: Any, row: int) -> None:
    if not isinstance(protein, str) or type(protein) is not str:
        raise TypeError(
            f'row {row}: protein must be str, got {type(protein).__name__}')
    if not 1 <= len(protein) <= MAX_NAME:
        raise ValueError(f'row {row}: protein must be 1-8 chars')


def _check_delta(delta: Any, row: int) -> None:
    if type(delta) is not int:
        raise TypeError(
            f'row {row}: delta must be int, got {type(delta).__name__}')
    if not MIN_DELTA <= delta <= MAX_DELTA:
        raise ValueError(
            f'row {row}: delta must be {MIN_DELTA}-{MAX_DELTA}, got {delta}')


def fold(rows: Any) -> dict:
    """Return the modal-delta summary for the supplied delta records."""
    if type(rows) not in (list, tuple):
        raise TypeError(f'rows must be list or tuple, got {type(rows).__name__}')
    if len(rows) > MAX_ROWS:
        raise ValueError(f'rows must contain at most {MAX_ROWS} entries')
    tallies: dict = {}
    for index, row in enumerate(rows, 1):
        if type(row) not in (list, tuple):
            raise TypeError(
                f'row {index}: expected (protein, delta) tuple, got {type(row).__name__}')
        if len(row) != 2:
            raise ValueError(
                f'row {index}: expected 2 fields, got {len(row)}')
        protein, delta = row
        _check_name(protein, index)
        _check_delta(delta, index)
        if protein not in tallies:
            tallies[protein] = {}
        tallies[protein][delta] = tallies[protein].get(delta, 0) + 1
    modes: dict = {}
    for protein, counts in tallies.items():
        best = max(counts.values())
        modes[protein] = min(delta for delta, count in counts.items()
                             if count == best)
    stable = sorted(protein for protein, mode in modes.items()
                    if mode >= 0)
    return {'total': len(rows), 'modes': modes, 'stable': stable}
