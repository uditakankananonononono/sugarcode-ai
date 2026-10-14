"""Row 964, Stem Cell Therapy: watching the three-day engraftment window.

After an infusion the new cells must take hold inside a three-day
window: a therapy engrafts when some run of three consecutive daily
counts sums to at least the engraftment level.  engraft() slides a
three-record window along each patient's daily counts and reports
the best window and the engrafted patients.

Input rows: (patient 1-8, cells int 0-10).  Engraftment level is 15
over a window of exactly 3 consecutive records.  Output: {'total',
'peak': {patient: best 3-record window sum}, 'engrafted': sorted
patients with a window at 15 or above}.  Reported: counts 4, 6, 5
sum to 15 and engraft; 4, 5, 5 sums to 14 and does not; a patient
with fewer than 3 records has no window and appears in neither
peak nor engrafted; the peak is the best window, not the total.
"""

from typing import Any

MAX_ROWS = 100
MAX_NAME = 8
MIN_CELLS = 0
MAX_CELLS = 10
WINDOW = 3
ENGRAFT_LEVEL = 15

SCOPE = 'PARTIAL: window bookkeeping only; no cell biology modeled'
NOT_CLAIMED = (
    'does not model differentiation',
    'does not weight the days within a window',
    'does not slide windows of any other size',
    'does not predict counts beyond the records',
)


def _check_name(patient: Any, row: int) -> None:
    if not isinstance(patient, str) or type(patient) is not str:
        raise TypeError(
            f'row {row}: patient must be str, got {type(patient).__name__}')
    if not 1 <= len(patient) <= MAX_NAME:
        raise ValueError(f'row {row}: patient must be 1-8 chars')


def _check_cells(cells: Any, row: int) -> None:
    if type(cells) is not int:
        raise TypeError(
            f'row {row}: cells must be int, got {type(cells).__name__}')
    if not MIN_CELLS <= cells <= MAX_CELLS:
        raise ValueError(
            f'row {row}: cells must be {MIN_CELLS}-{MAX_CELLS}, got {cells}')


def engraft(rows: Any) -> dict:
    """Return the engraftment summary for the supplied cell counts."""
    if type(rows) not in (list, tuple):
        raise TypeError(f'rows must be list or tuple, got {type(rows).__name__}')
    if len(rows) > MAX_ROWS:
        raise ValueError(f'rows must contain at most {MAX_ROWS} entries')
    counts: dict = {}
    for index, row in enumerate(rows, 1):
        if type(row) not in (list, tuple):
            raise TypeError(
                f'row {index}: expected (patient, cells) tuple, got {type(row).__name__}')
        if len(row) != 2:
            raise ValueError(
                f'row {index}: expected 2 fields, got {len(row)}')
        patient, cells = row
        _check_name(patient, index)
        _check_cells(cells, index)
        counts.setdefault(patient, []).append(cells)
    peak: dict = {}
    for patient, values in counts.items():
        if len(values) >= WINDOW:
            peak[patient] = max(
                sum(values[start:start + WINDOW])
                for start in range(len(values) - WINDOW + 1))
    engrafted = sorted(patient for patient, best in peak.items()
                       if best >= ENGRAFT_LEVEL)
    return {'total': len(rows), 'peak': peak, 'engrafted': engrafted}
