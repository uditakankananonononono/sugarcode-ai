"""Row 967, Base Editing: weighting each change by its place.

A base editor's later changes lean on the earlier ones, so a change
late in a series counts more than the same change made first.
weight() scores each editor's changes by their 1-based place in the
editor's own record order and reports the editors whose weighted
score stays inside the precision limit.

Input rows: (editor 1-8, change int 0-10).  Precision limit is 20.
Output: {'total', 'scores': {editor: change times place, summed},
'precise': sorted editors scoring at most 20}.  Reported: changes 5
then 3 score 5*1 + 3*2 = 11; changes 3 then 5 score 13, the order
matters; a lone change scores itself; changes 6 then 7 score
exactly 20 and stay precise.
"""

from typing import Any

MAX_ROWS = 100
MAX_NAME = 8
MIN_CHANGE = 0
MAX_CHANGE = 10
LIMIT = 20

SCOPE = 'PARTIAL: weighted scoring only; no DNA chemistry modeled'
NOT_CLAIMED = (
    'does not model conversion efficiency',
    'does not weight by genomic position',
    'does not cap the score during accumulation',
    'does not compare editors against each other',
)


def _check_name(editor: Any, row: int) -> None:
    if not isinstance(editor, str) or type(editor) is not str:
        raise TypeError(
            f'row {row}: editor must be str, got {type(editor).__name__}')
    if not 1 <= len(editor) <= MAX_NAME:
        raise ValueError(f'row {row}: editor must be 1-8 chars')


def _check_change(change: Any, row: int) -> None:
    if type(change) is not int:
        raise TypeError(
            f'row {row}: change must be int, got {type(change).__name__}')
    if not MIN_CHANGE <= change <= MAX_CHANGE:
        raise ValueError(
            f'row {row}: change must be {MIN_CHANGE}-{MAX_CHANGE}, got {change}')


def weight(rows: Any) -> dict:
    """Return the weighted summary for the supplied change records."""
    if type(rows) not in (list, tuple):
        raise TypeError(f'rows must be list or tuple, got {type(rows).__name__}')
    if len(rows) > MAX_ROWS:
        raise ValueError(f'rows must contain at most {MAX_ROWS} entries')
    scores: dict = {}
    places: dict = {}
    for index, row in enumerate(rows, 1):
        if type(row) not in (list, tuple):
            raise TypeError(
                f'row {index}: expected (editor, change) tuple, got {type(row).__name__}')
        if len(row) != 2:
            raise ValueError(
                f'row {index}: expected 2 fields, got {len(row)}')
        editor, change = row
        _check_name(editor, index)
        _check_change(change, index)
        places[editor] = places.get(editor, 0) + 1
        scores[editor] = scores.get(editor, 0) + change * places[editor]
    precise = sorted(editor for editor, score in scores.items()
                     if score <= LIMIT)
    return {'total': len(rows), 'scores': scores, 'precise': precise}
