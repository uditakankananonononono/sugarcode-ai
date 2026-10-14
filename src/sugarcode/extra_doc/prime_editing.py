"""Row 968, Prime Editing: minding the longest extension.

A prime editor writes its edit through an extension built from a
template and a primer binding site, and the reverse transcriptase
fails when the combined extension runs too long.  rewrite() tracks
each editor's longest extension and reports the editors that never
exceed the viability limit.

Input rows: (editor 1-8, template int 0-10, primer int 0-10).  The
extension is template + primer; the viability limit is 15.  Output:
{'total', 'longest': {editor: longest extension}, 'viable': sorted
editors whose longest extension is at most 15}.  Reported:
extensions are computed per record, so template 9 with primer 7 is
not viable (16) even if every other record is short; template 10
with primer 5 is exactly 15 and stays viable; the longest is kept,
not the latest.
"""

from typing import Any

MAX_ROWS = 100
MAX_NAME = 8
MIN_PART = 0
MAX_PART = 10
LIMIT = 15

SCOPE = 'PARTIAL: extension bookkeeping only; no editing outcome modeled'
NOT_CLAIMED = (
    'does not model reverse transcriptase kinetics',
    'does not sum extensions across records',
    'does not limit the template and primer separately',
    'does not model insertion or deletion length',
)


def _check_name(editor: Any, row: int) -> None:
    if not isinstance(editor, str) or type(editor) is not str:
        raise TypeError(
            f'row {row}: editor must be str, got {type(editor).__name__}')
    if not 1 <= len(editor) <= MAX_NAME:
        raise ValueError(f'row {row}: editor must be 1-8 chars')


def _check_part(value: Any, row: int, field: str) -> None:
    if type(value) is not int:
        raise TypeError(
            f'row {row}: {field} must be int, got {type(value).__name__}')
    if not MIN_PART <= value <= MAX_PART:
        raise ValueError(
            f'row {row}: {field} must be {MIN_PART}-{MAX_PART}, got {value}')


def rewrite(rows: Any) -> dict:
    """Return the extension summary for the supplied edit records."""
    if type(rows) not in (list, tuple):
        raise TypeError(f'rows must be list or tuple, got {type(rows).__name__}')
    if len(rows) > MAX_ROWS:
        raise ValueError(f'rows must contain at most {MAX_ROWS} entries')
    longest: dict = {}
    for index, row in enumerate(rows, 1):
        if type(row) not in (list, tuple):
            raise TypeError(
                f'row {index}: expected (editor, template, primer) tuple, got {type(row).__name__}')
        if len(row) != 3:
            raise ValueError(
                f'row {index}: expected 3 fields, got {len(row)}')
        editor, template, primer = row
        _check_name(editor, index)
        _check_part(template, index, 'template')
        _check_part(primer, index, 'primer')
        extension = template + primer
        longest[editor] = max(longest.get(editor, MIN_PART), extension)
    viable = sorted(editor for editor, best in longest.items()
                    if best <= LIMIT)
    return {'total': len(rows), 'longest': longest, 'viable': viable}
