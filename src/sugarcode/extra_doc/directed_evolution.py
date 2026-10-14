"""Row 973, Directed Evolution: netting each lineage's gain.

Evolution is judged by where a lineage ends against where it began,
not by the detours in between.  evolve() nets each lineage's gain as
its latest fitness minus its first and reports the lineages whose
net gain clears the rise bar.

Input rows: (lineage 1-8, fitness int 0-10).  Rise bar is 3.
Output: {'total', 'gains': {lineage: last fitness minus first},
'risen': sorted lineages gaining at least 3}.  Reported: fitness 2
then 5 gains 3 and rises; 5 then 2 loses 3 and stays down; a lone
record gains nothing; a gain of exactly 3 still counts; only the
first and last records set the gain, so 2, 9, 5 nets 3.
"""

from typing import Any

MAX_ROWS = 100
MAX_NAME = 8
MIN_FITNESS = 0
MAX_FITNESS = 10
RISE = 3

SCOPE = 'PARTIAL: fitness bookkeeping only; no selection dynamics modeled'
NOT_CLAIMED = (
    'does not model mutation rates',
    'does not weight fitness by generation',
    'does not read the middle records',
    'does not compare lineages against each other',
)


def _check_name(lineage: Any, row: int) -> None:
    if not isinstance(lineage, str) or type(lineage) is not str:
        raise TypeError(
            f'row {row}: lineage must be str, got {type(lineage).__name__}')
    if not 1 <= len(lineage) <= MAX_NAME:
        raise ValueError(f'row {row}: lineage must be 1-8 chars')


def _check_fitness(fitness: Any, row: int) -> None:
    if type(fitness) is not int:
        raise TypeError(
            f'row {row}: fitness must be int, got {type(fitness).__name__}')
    if not MIN_FITNESS <= fitness <= MAX_FITNESS:
        raise ValueError(
            f'row {row}: fitness must be {MIN_FITNESS}-{MAX_FITNESS}, got {fitness}')


def evolve(rows: Any) -> dict:
    """Return the net-gain summary for the supplied fitness records."""
    if type(rows) not in (list, tuple):
        raise TypeError(f'rows must be list or tuple, got {type(rows).__name__}')
    if len(rows) > MAX_ROWS:
        raise ValueError(f'rows must contain at most {MAX_ROWS} entries')
    firsts: dict = {}
    lasts: dict = {}
    for index, row in enumerate(rows, 1):
        if type(row) not in (list, tuple):
            raise TypeError(
                f'row {index}: expected (lineage, fitness) tuple, got {type(row).__name__}')
        if len(row) != 2:
            raise ValueError(
                f'row {index}: expected 2 fields, got {len(row)}')
        lineage, fitness = row
        _check_name(lineage, index)
        _check_fitness(fitness, index)
        if lineage not in firsts:
            firsts[lineage] = fitness
        lasts[lineage] = fitness
    gains = {lineage: lasts[lineage] - firsts[lineage] for lineage in firsts}
    risen = sorted(lineage for lineage, gain in gains.items()
                   if gain >= RISE)
    return {'total': len(rows), 'gains': gains, 'risen': risen}
