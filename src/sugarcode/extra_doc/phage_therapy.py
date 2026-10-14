"""Row 983, Phage Therapy: counting each phage's crests.

A phage whose titer spikes and settles, then spikes again, covers
more ground than one on a steady climb.  hunt() counts each phage's
crests - records strictly higher than both neighbors in the phage's
own record sequence - and reports the phages with enough crests to
read as rugged.

Input rows: (phage 1-8, titer int 0-10).  Rugged means 2 crests.
Output: {'total', 'crests': {phage: count of strict local maxima},
'rugged': sorted phages with at least 2 crests}.  Reported: titers
1, 3, 1 give one crest at the middle record; 1, 3, 1, 3, 1 give two
and read rugged; 3, 3, 1 give none because a crest must be strict;
1, 3, 3 give none because the next record must drop below the
crest; 1, 2, 3 give none because the rise never turns; a lone
record gives none.
"""

from typing import Any

MAX_ROWS = 100
MAX_NAME = 8
MIN_TITER = 0
MAX_TITER = 10
RUGGED = 2

SCOPE = 'PARTIAL: titer bookkeeping only; no infection dynamics modeled'
NOT_CLAIMED = (
    'does not model bacterial resistance',
    'does not weight titers by record order',
    'does not count edge records as crests',
    'does not compare phages against each other',
)


def _check_name(phage: Any, row: int) -> None:
    if not isinstance(phage, str) or type(phage) is not str:
        raise TypeError(
            f'row {row}: phage must be str, got {type(phage).__name__}')
    if not 1 <= len(phage) <= MAX_NAME:
        raise ValueError(f'row {row}: phage must be 1-8 chars')


def _check_titer(titer: Any, row: int) -> None:
    if type(titer) is not int:
        raise TypeError(
            f'row {row}: titer must be int, got {type(titer).__name__}')
    if not MIN_TITER <= titer <= MAX_TITER:
        raise ValueError(
            f'row {row}: titer must be {MIN_TITER}-{MAX_TITER}, got {titer}')


def hunt(rows: Any) -> dict:
    """Return the crest summary for the supplied titer records."""
    if type(rows) not in (list, tuple):
        raise TypeError(f'rows must be list or tuple, got {type(rows).__name__}')
    if len(rows) > MAX_ROWS:
        raise ValueError(f'rows must contain at most {MAX_ROWS} entries')
    history: dict = {}
    crests: dict = {}
    for index, row in enumerate(rows, 1):
        if type(row) not in (list, tuple):
            raise TypeError(
                f'row {index}: expected (phage, titer) tuple, got {type(row).__name__}')
        if len(row) != 2:
            raise ValueError(
                f'row {index}: expected 2 fields, got {len(row)}')
        phage, titer = row
        _check_name(phage, index)
        _check_titer(titer, index)
        if phage not in history:
            history[phage] = []
            crests[phage] = 0
        seen = history[phage]
        if len(seen) >= 2 and seen[-1] > seen[-2] and seen[-1] > titer:
            crests[phage] += 1
        seen.append(titer)
    rugged = sorted(phage for phage, count in crests.items()
                    if count >= RUGGED)
    return {'total': len(rows), 'crests': crests, 'rugged': rugged}
