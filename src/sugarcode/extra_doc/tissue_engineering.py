"""Row 962, Tissue Engineering: merging the grown strands.

Tissue grows as strands along a scaffold, and overlapping strands
merge into one continuous coverage; strands that only touch end to
end stay separate.  merge() folds the supplied strand records per
scaffold, merges strictly overlapping strands, and reports the
covered length and the scaffolds grown confluent edge to edge.

Input rows: (scaffold 1-8, start int 0-10, end int 0-10) with start
strictly below end.  Output: {'total', 'covered': {scaffold: merged
coverage length}, 'confluent': sorted scaffolds whose strands merge
into a single 0-to-10 coverage}.  Reported: strands (0, 5) and (5,
10) touch but do not overlap, so they cover 10 without being
confluent; strands (0, 6) and (4, 10) overlap and merge into one
0-to-10 coverage, which is confluent; strands (2, 4) and (6, 8)
cover 4 and leave gaps.
"""

from typing import Any

MAX_ROWS = 100
MAX_NAME = 8
MIN_POS = 0
MAX_POS = 10

SCOPE = 'PARTIAL: coverage bookkeeping only; no scaffold chemistry modeled'
NOT_CLAIMED = (
    'does not model cell growth over time',
    'does not simulate scaffold degradation',
    'does not merge strands that only touch',
    'does not track coverage outside 0 to 10',
)


def _check_name(scaffold: Any, row: int) -> None:
    if not isinstance(scaffold, str) or type(scaffold) is not str:
        raise TypeError(
            f'row {row}: scaffold must be str, got {type(scaffold).__name__}')
    if not 1 <= len(scaffold) <= MAX_NAME:
        raise ValueError(f'row {row}: scaffold must be 1-8 chars')


def _check_pos(value: Any, row: int, field: str) -> None:
    if type(value) is not int:
        raise TypeError(
            f'row {row}: {field} must be int, got {type(value).__name__}')
    if not MIN_POS <= value <= MAX_POS:
        raise ValueError(
            f'row {row}: {field} must be {MIN_POS}-{MAX_POS}, got {value}')


def merge(rows: Any) -> dict:
    """Return the coverage summary for the supplied strand records."""
    if type(rows) not in (list, tuple):
        raise TypeError(f'rows must be list or tuple, got {type(rows).__name__}')
    if len(rows) > MAX_ROWS:
        raise ValueError(f'rows must contain at most {MAX_ROWS} entries')
    strands: dict = {}
    for index, row in enumerate(rows, 1):
        if type(row) not in (list, tuple):
            raise TypeError(
                f'row {index}: expected (scaffold, start, end) tuple, got {type(row).__name__}')
        if len(row) != 3:
            raise ValueError(
                f'row {index}: expected 3 fields, got {len(row)}')
        scaffold, start, end = row
        _check_name(scaffold, index)
        _check_pos(start, index, 'start')
        _check_pos(end, index, 'end')
        if start >= end:
            raise ValueError(
                f'row {index}: start must be below end, got {start} and {end}')
        strands.setdefault(scaffold, []).append((start, end))
    covered: dict = {}
    confluent = []
    for scaffold in strands:
        spans = []
        for start, end in sorted(strands[scaffold]):
            if spans and start < spans[-1][1]:
                spans[-1][1] = max(spans[-1][1], end)
            else:
                spans.append([start, end])
        covered[scaffold] = sum(end - start for start, end in spans)
        if len(spans) == 1 and spans[0] == [MIN_POS, MAX_POS]:
            confluent.append(scaffold)
    confluent.sort()
    return {'total': len(rows), 'covered': covered, 'confluent': confluent}
