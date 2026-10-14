"""Row 1000, Chemogenetics: chaining each receptor's doses.

A receptor chains when one dose is the sum of the two before
it, not when doses merely climb.  bind() counts each receptor's
consecutive triples where the third dose equals the first two
added together and reports the receptors with repeated chains.

Input rows: (receptor 1-8, dose int 0-10).  Chained is 2
sum-triples.
Output: {'total', 'bonds': {receptor: consecutive sum-triples},
'chained': sorted receptors with 2 sum-triples}.  Reported:
doses 1, 1, 2, 3, 5 chain 3 times; 1, 2, 3 chain once; 1, 2,
3, 5 chain twice and read chained; 2, 3, 5 chain once; 1, 2, 4
chain 0; 0, 0, 0 chain once; 3, 0, 3 chain once; 5, 5, 10
chain once; a lone dose chains 0.
"""

from typing import Any

MAX_ROWS = 100
MAX_NAME = 8
MIN_DOSE = 0
MAX_DOSE = 10
CHAINED = 2

SCOPE = 'PARTIAL: dose bookkeeping only; no DREADD signaling modeled'
NOT_CLAIMED = (
    'does not model ligand affinity',
    'does not count non-consecutive dose triples',
    'does not cap the sum at the dose range',
    'does not compare receptors against each other',
)


def _check_name(receptor: Any, row: int) -> None:
    if not isinstance(receptor, str) or type(receptor) is not str:
        raise TypeError(
            f'row {row}: receptor must be str, got {type(receptor).__name__}')
    if not 1 <= len(receptor) <= MAX_NAME:
        raise ValueError(f'row {row}: receptor must be 1-8 chars')


def _check_dose(dose: Any, row: int) -> None:
    if type(dose) is not int:
        raise TypeError(
            f'row {row}: dose must be int, got {type(dose).__name__}')
    if not MIN_DOSE <= dose <= MAX_DOSE:
        raise ValueError(
            f'row {row}: dose must be {MIN_DOSE}-{MAX_DOSE}, got {dose}')


def bind(rows: Any) -> dict:
    """Return the bond summary for the supplied dose records."""
    if type(rows) not in (list, tuple):
        raise TypeError(f'rows must be list or tuple, got {type(rows).__name__}')
    if len(rows) > MAX_ROWS:
        raise ValueError(f'rows must contain at most {MAX_ROWS} entries')
    values: dict = {}
    for index, row in enumerate(rows, 1):
        if type(row) not in (list, tuple):
            raise TypeError(
                f'row {index}: expected (receptor, dose) tuple, got {type(row).__name__}')
        if len(row) != 2:
            raise ValueError(
                f'row {index}: expected 2 fields, got {len(row)}')
        receptor, dose = row
        _check_name(receptor, index)
        _check_dose(dose, index)
        values.setdefault(receptor, []).append(dose)
    bonds = {}
    for receptor, vals in values.items():
        count = 0
        for i in range(len(vals) - 2):
            if vals[i] + vals[i + 1] == vals[i + 2]:
                count += 1
        bonds[receptor] = count
    chained = sorted(receptor for receptor, count in bonds.items()
                     if count >= CHAINED)
    return {'total': len(rows), 'bonds': bonds, 'chained': chained}
