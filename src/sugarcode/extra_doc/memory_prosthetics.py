"""Row 1006, Memory Prosthetics: weighing a trace's halves.

A trace holds steady when its two halves carry the same weight,
not when its cues merely repeat.  recall() splits each trace's
cues in record order into a front half and a back half, leaving
any middle cue aside, and reports the absolute drift between
the half sums.

Input rows: (trace 1-8, cue int 0-10).  With an odd count the
middle cue joins neither half.
Output: {'total', 'drift': {trace: absolute difference of its
half sums}, 'even': sorted traces with no drift}.
Reported: cues 1, 2, 3, 4 drift 4; 2, 2, 2, 2 drift 0 and
read even; 1, 5, 1 drift 0; 2, 3, 4 drift 2; a lone cue
drifts 0; 0, 10, 0, 10 drift 0; 1, 1, 1, 1, 9 drift 8;
6, 4, 2 drift 4; 0, 0, 1 drift 1.
"""

from typing import Any

MAX_ROWS = 100
MAX_NAME = 8
MIN_CUE = 0
MAX_CUE = 10

SCOPE = 'PARTIAL: cue bookkeeping only; no prosthetic device modeled'
NOT_CLAIMED = (
    'does not model consolidation over time',
    'does not weight the middle cue when the count is odd',
    'does not measure which half is heavier, only the gap',
    'does not compare traces against each other',
)


def _check_name(trace: Any, row: int) -> None:
    if not isinstance(trace, str) or type(trace) is not str:
        raise TypeError(
            f'row {row}: trace must be str, got {type(trace).__name__}')
    if not 1 <= len(trace) <= MAX_NAME:
        raise ValueError(f'row {row}: trace must be 1-8 chars')


def _check_cue(cue: Any, row: int) -> None:
    if type(cue) is not int:
        raise TypeError(
            f'row {row}: cue must be int, got {type(cue).__name__}')
    if not MIN_CUE <= cue <= MAX_CUE:
        raise ValueError(
            f'row {row}: cue must be {MIN_CUE}-{MAX_CUE}, got {cue}')


def recall(rows: Any) -> dict:
    """Return the half-drift summary for the supplied cue records."""
    if type(rows) not in (list, tuple):
        raise TypeError(f'rows must be list or tuple, got {type(rows).__name__}')
    if len(rows) > MAX_ROWS:
        raise ValueError(f'rows must contain at most {MAX_ROWS} entries')
    values: dict = {}
    for index, row in enumerate(rows, 1):
        if type(row) not in (list, tuple):
            raise TypeError(
                f'row {index}: expected (trace, cue) tuple, got {type(row).__name__}')
        if len(row) != 2:
            raise ValueError(
                f'row {index}: expected 2 fields, got {len(row)}')
        trace, cue = row
        _check_name(trace, index)
        _check_cue(cue, index)
        values.setdefault(trace, []).append(cue)
    drift = {}
    for trace, vals in values.items():
        half = len(vals) // 2
        front = sum(vals[:half])
        back = sum(vals[len(vals) - half:])
        drift[trace] = abs(front - back)
    even = sorted(trace for trace, gap in drift.items() if gap == 0)
    return {'total': len(rows), 'drift': drift, 'even': even}
