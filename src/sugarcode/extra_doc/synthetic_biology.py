"""Row 970, Synthetic Biology: counting the distinct parts in each build.

A synthetic organism is assembled from genetic parts, and a build
that reaches for the same part twice reads as redundant.  assemble()
counts the distinct parts each organism uses and reports the
organisms whose builds never repeat a part.

Input rows: (organism 1-8, part 1-8).
Output: {'total', 'parts': {organism: distinct part count},
'clean': sorted organisms with no repeated part}.  Reported: parts
a, b, a give 2 distinct parts and the repeat costs clean; parts a,
b, c give 3 distinct parts and stay clean; one organism's repeat
never stains another organism's build, and the same part in two
different organisms stains neither.
"""

from typing import Any

MAX_ROWS = 100
MAX_NAME = 8

SCOPE = 'PARTIAL: part tallying only; no sequence biology modeled'
NOT_CLAIMED = (
    'does not model part compatibility',
    'does not order the parts within a build',
    'does not score build quality beyond repeats',
    'does not compare organisms against each other',
)


def _check_organism(organism: Any, row: int) -> None:
    if not isinstance(organism, str) or type(organism) is not str:
        raise TypeError(
            f'row {row}: organism must be str, got {type(organism).__name__}')
    if not 1 <= len(organism) <= MAX_NAME:
        raise ValueError(f'row {row}: organism must be 1-8 chars')


def _check_part(part: Any, row: int) -> None:
    if not isinstance(part, str) or type(part) is not str:
        raise TypeError(
            f'row {row}: part must be str, got {type(part).__name__}')
    if not 1 <= len(part) <= MAX_NAME:
        raise ValueError(f'row {row}: part must be 1-8 chars')


def assemble(rows: Any) -> dict:
    """Return the distinct-part summary for the supplied build records."""
    if type(rows) not in (list, tuple):
        raise TypeError(f'rows must be list or tuple, got {type(rows).__name__}')
    if len(rows) > MAX_ROWS:
        raise ValueError(f'rows must contain at most {MAX_ROWS} entries')
    seen: dict = {}
    dirty: set = set()
    for index, row in enumerate(rows, 1):
        if type(row) not in (list, tuple):
            raise TypeError(
                f'row {index}: expected (organism, part) tuple, got {type(row).__name__}')
        if len(row) != 2:
            raise ValueError(
                f'row {index}: expected 2 fields, got {len(row)}')
        organism, part = row
        _check_organism(organism, index)
        _check_part(part, index)
        if organism not in seen:
            seen[organism] = set()
        if part in seen[organism]:
            dirty.add(organism)
        seen[organism].add(part)
    parts = {organism: len(seen[organism]) for organism in seen}
    clean = sorted(organism for organism in seen if organism not in dirty)
    return {'total': len(rows), 'parts': parts, 'clean': clean}
