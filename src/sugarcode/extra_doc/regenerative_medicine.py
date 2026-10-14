"""Row 963, Regenerative Medicine: matching grafts by marker.

A regenerative graft takes only between patients who share a tissue
marker, so patients are grouped by their marker and only groups of
two or more can exchange grafts.  match() groups the supplied
records by marker and reports the match groups and the patients
left without a partner.

Input rows: (patient 1-8, marker int 0-10).  Output: {'total',
'groups': {marker: sorted patients} for markers with at least two
patients, 'lonely': sorted patients whose marker group has just
one}.  Reported: a patient is listed once per marker however often
recorded with it; a patient recorded with two markers joins both
groups; a marker with a single patient forms no group.
"""

from typing import Any

MAX_ROWS = 100
MAX_NAME = 8
MIN_MARKER = 0
MAX_MARKER = 10

SCOPE = 'PARTIAL: marker grouping only; no immunology modeled'
NOT_CLAIMED = (
    'does not model rejection risk within a group',
    'does not rank matches by compatibility',
    'does not track graft supply',
    'does not resolve a patient recorded with two markers',
)


def _check_name(patient: Any, row: int) -> None:
    if not isinstance(patient, str) or type(patient) is not str:
        raise TypeError(
            f'row {row}: patient must be str, got {type(patient).__name__}')
    if not 1 <= len(patient) <= MAX_NAME:
        raise ValueError(f'row {row}: patient must be 1-8 chars')


def _check_marker(marker: Any, row: int) -> None:
    if type(marker) is not int:
        raise TypeError(
            f'row {row}: marker must be int, got {type(marker).__name__}')
    if not MIN_MARKER <= marker <= MAX_MARKER:
        raise ValueError(
            f'row {row}: marker must be {MIN_MARKER}-{MAX_MARKER}, got {marker}')


def match(rows: Any) -> dict:
    """Return the match summary for the supplied marker records."""
    if type(rows) not in (list, tuple):
        raise TypeError(f'rows must be list or tuple, got {type(rows).__name__}')
    if len(rows) > MAX_ROWS:
        raise ValueError(f'rows must contain at most {MAX_ROWS} entries')
    by_marker: dict = {}
    for index, row in enumerate(rows, 1):
        if type(row) not in (list, tuple):
            raise TypeError(
                f'row {index}: expected (patient, marker) tuple, got {type(row).__name__}')
        if len(row) != 2:
            raise ValueError(
                f'row {index}: expected 2 fields, got {len(row)}')
        patient, marker = row
        _check_name(patient, index)
        _check_marker(marker, index)
        by_marker.setdefault(marker, set()).add(patient)
    groups = {marker: sorted(patients)
              for marker, patients in by_marker.items() if len(patients) >= 2}
    lonely = sorted(patient for patient in
                    {p for patients in by_marker.values() for p in patients}
                    if all(patient not in groups.get(marker, [])
                           for marker in by_marker))
    return {'total': len(rows), 'groups': groups, 'lonely': lonely}
