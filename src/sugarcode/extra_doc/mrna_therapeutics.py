"""Row 987, mRNA Therapeutics: spacing each sequence's expressions.

A sequence matters when its expressions sit together, not when one
spike carries it.  translate() sums the pairwise absolute
differences inside each sequence's own expression list and reports
the sequences whose spread stays within the tolerance.

Input rows: (sequence 1-8, expression int 0-10).  Tight is a spread
of at most 4.
Output: {'total', 'spreads': {sequence: sum of pairwise absolute
differences}, 'tight': sorted sequences with spread at most 4}.
Reported: expressions 1, 2, 4 spread to 1 + 3 + 2 = 6; 3, 3 spread
to 0 and stay tight; 1, 2, 3 spread to 4 and stay tight; 0, 5
spread to 5; a lone expression spreads to 0; record order does not
change a spread.
"""

from typing import Any

MAX_ROWS = 100
MAX_NAME = 8
MIN_EXPRESSION = 0
MAX_EXPRESSION = 10
TIGHT = 4

SCOPE = 'PARTIAL: expression bookkeeping only; no translation modeled'
NOT_CLAIMED = (
    'does not model codon optimization',
    'does not weight expressions by record order',
    'does not compare sequences against each other',
    'does not cap how many expressions one sequence may hold',
)


def _check_name(sequence: Any, row: int) -> None:
    if not isinstance(sequence, str) or type(sequence) is not str:
        raise TypeError(
            f'row {row}: sequence must be str, got {type(sequence).__name__}')
    if not 1 <= len(sequence) <= MAX_NAME:
        raise ValueError(f'row {row}: sequence must be 1-8 chars')


def _check_expression(expression: Any, row: int) -> None:
    if type(expression) is not int:
        raise TypeError(
            f'row {row}: expression must be int, got {type(expression).__name__}')
    if not MIN_EXPRESSION <= expression <= MAX_EXPRESSION:
        raise ValueError(
            f'row {row}: expression must be {MIN_EXPRESSION}-{MAX_EXPRESSION}, got {expression}')


def translate(rows: Any) -> dict:
    """Return the spread summary for the supplied expression records."""
    if type(rows) not in (list, tuple):
        raise TypeError(f'rows must be list or tuple, got {type(rows).__name__}')
    if len(rows) > MAX_ROWS:
        raise ValueError(f'rows must contain at most {MAX_ROWS} entries')
    values: dict = {}
    for index, row in enumerate(rows, 1):
        if type(row) not in (list, tuple):
            raise TypeError(
                f'row {index}: expected (sequence, expression) tuple, got {type(row).__name__}')
        if len(row) != 2:
            raise ValueError(
                f'row {index}: expected 2 fields, got {len(row)}')
        sequence, expression = row
        _check_name(sequence, index)
        _check_expression(expression, index)
        values.setdefault(sequence, []).append(expression)
    spreads = {}
    for sequence, vals in values.items():
        spread = 0
        for i, a in enumerate(vals):
            for b in vals[i + 1:]:
                spread += abs(a - b)
        spreads[sequence] = spread
    tight = sorted(sequence for sequence, spread in spreads.items()
                   if spread <= TIGHT)
    return {'total': len(rows), 'spreads': spreads, 'tight': tight}
