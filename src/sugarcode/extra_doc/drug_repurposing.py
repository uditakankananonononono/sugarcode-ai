"""Row 978, Drug Repurposing: timing each drug's plateau.

A drug that keeps landing on the same score has found its level, and
that steady stretch is what a new use builds on.  rescue() times
each drug's longest run of equal consecutive scores and reports the
drugs whose plateau reaches the anchor length.

Input rows: (drug 1-8, score int 0-10).  Anchor length is 2.
Output: {'total', 'plateaus': {drug: longest equal consecutive run},
'anchored': sorted drugs plateauing at 2 or more}.  Reported:
scores 3, 3 plateau at 2 and anchor; 3, 3, 3 plateau at 3; 3, 4, 4
plateau at 2; a lone record plateaus at 1; a broken run keeps its
best, so 4, 4, 3, 3, 3 plateaus at 3.
"""

from typing import Any

MAX_ROWS = 100
MAX_NAME = 8
MIN_SCORE = 0
MAX_SCORE = 10
ANCHOR = 2

SCOPE = 'PARTIAL: score bookkeeping only; no clinical evidence modeled'
NOT_CLAIMED = (
    'does not model side effects',
    'does not weight scores by record order',
    'does not merge runs separated by other drugs',
    'does not compare drugs against each other',
)


def _check_name(drug: Any, row: int) -> None:
    if not isinstance(drug, str) or type(drug) is not str:
        raise TypeError(
            f'row {row}: drug must be str, got {type(drug).__name__}')
    if not 1 <= len(drug) <= MAX_NAME:
        raise ValueError(f'row {row}: drug must be 1-8 chars')


def _check_score(score: Any, row: int) -> None:
    if type(score) is not int:
        raise TypeError(
            f'row {row}: score must be int, got {type(score).__name__}')
    if not MIN_SCORE <= score <= MAX_SCORE:
        raise ValueError(
            f'row {row}: score must be {MIN_SCORE}-{MAX_SCORE}, got {score}')


def rescue(rows: Any) -> dict:
    """Return the plateau summary for the supplied score records."""
    if type(rows) not in (list, tuple):
        raise TypeError(f'rows must be list or tuple, got {type(rows).__name__}')
    if len(rows) > MAX_ROWS:
        raise ValueError(f'rows must contain at most {MAX_ROWS} entries')
    last: dict = {}
    runs: dict = {}
    plateaus: dict = {}
    for index, row in enumerate(rows, 1):
        if type(row) not in (list, tuple):
            raise TypeError(
                f'row {index}: expected (drug, score) tuple, got {type(row).__name__}')
        if len(row) != 2:
            raise ValueError(
                f'row {index}: expected 2 fields, got {len(row)}')
        drug, score = row
        _check_name(drug, index)
        _check_score(score, index)
        if drug not in last:
            runs[drug] = 1
            plateaus[drug] = 1
        elif score == last[drug]:
            runs[drug] += 1
            plateaus[drug] = max(plateaus[drug], runs[drug])
        else:
            runs[drug] = 1
        last[drug] = score
    anchored = sorted(drug for drug, plateau in plateaus.items()
                      if plateau >= ANCHOR)
    return {'total': len(rows), 'plateaus': plateaus, 'anchored': anchored}
