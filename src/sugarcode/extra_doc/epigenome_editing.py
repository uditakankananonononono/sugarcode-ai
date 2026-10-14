"""Row 969, Epigenome Editing: tracking each gene's fall from its peak.

An epigenome edit nudges a gene's expression level up or down, and a
gene that stays near its own high-water mark reads as stable.
marks() accumulates each gene's marks into a level, tracks the gene's
peak level and its largest fall below that peak, and reports the
genes whose largest fall stays inside the stability tolerance.

Input rows: (gene 1-8, mark int -9..9).  Stability tolerance is 4.
Output: {'total', 'peaks': {gene: highest level reached},
'steady': sorted genes whose largest fall from their own peak is at
most 4}.  Reported: marks 3, -2, -2 give levels 3, 1, -1, a peak of
3 and a fall of 4, still steady; marks 5 then -5 give a fall of 5
and lose steady; a lone mark of 0 peaks at 0 with no fall; a gene
that only falls from zero still peaks at 0.
"""

from typing import Any

MAX_ROWS = 100
MAX_NAME = 8
MIN_MARK = -9
MAX_MARK = 9
TOLERANCE = 4

SCOPE = 'PARTIAL: level bookkeeping only; no chromatin state modeled'
NOT_CLAIMED = (
    'does not model methylation chemistry',
    'does not decay levels between records',
    'does not compare genes against each other',
    'does not bound the level itself',
)


def _check_name(gene: Any, row: int) -> None:
    if not isinstance(gene, str) or type(gene) is not str:
        raise TypeError(
            f'row {row}: gene must be str, got {type(gene).__name__}')
    if not 1 <= len(gene) <= MAX_NAME:
        raise ValueError(f'row {row}: gene must be 1-8 chars')


def _check_mark(mark: Any, row: int) -> None:
    if type(mark) is not int:
        raise TypeError(
            f'row {row}: mark must be int, got {type(mark).__name__}')
    if not MIN_MARK <= mark <= MAX_MARK:
        raise ValueError(
            f'row {row}: mark must be {MIN_MARK}-{MAX_MARK}, got {mark}')


def marks(rows: Any) -> dict:
    """Return the stability summary for the supplied mark records."""
    if type(rows) not in (list, tuple):
        raise TypeError(f'rows must be list or tuple, got {type(rows).__name__}')
    if len(rows) > MAX_ROWS:
        raise ValueError(f'rows must contain at most {MAX_ROWS} entries')
    levels: dict = {}
    peaks: dict = {}
    dips: dict = {}
    for index, row in enumerate(rows, 1):
        if type(row) not in (list, tuple):
            raise TypeError(
                f'row {index}: expected (gene, mark) tuple, got {type(row).__name__}')
        if len(row) != 2:
            raise ValueError(
                f'row {index}: expected 2 fields, got {len(row)}')
        gene, mark = row
        _check_name(gene, index)
        _check_mark(mark, index)
        levels[gene] = levels.get(gene, 0) + mark
        peaks[gene] = max(peaks.get(gene, 0), levels[gene])
        dips[gene] = max(dips.get(gene, 0), peaks[gene] - levels[gene])
    steady = sorted(gene for gene, fall in dips.items()
                    if fall <= TOLERANCE)
    return {'total': len(rows), 'peaks': peaks, 'steady': steady}
