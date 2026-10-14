"""Row 997, Retinal Implants: balancing each pixel's charge.

A pixel reads even when its even charges outweigh its odd ones,
not when it merely stays lit.  see() adds each even charge to
the pixel's ledger and subtracts each odd one, then reports the
pixels whose ledger ends positive.

Input rows: (pixel 1-8, charge int 0-10).  Even is a positive
ledger; 0 counts as an even charge.
Output: {'total', 'ledger': {pixel: even charges minus odd
charges}, 'even': sorted pixels with a positive ledger}.
Reported: charges 1, 2, 3, 4 balance to 2 and read even; 5
balances to -5; 2, 2 balance to 4; 1, 3 balance to -4; 0
balances to 0 and does not read even; 0, 1 balance to -1;
3, 3, 2 balance to -4; 6, 1 balance to 5; a lone odd charge
never reads even.
"""

from typing import Any

MAX_ROWS = 100
MAX_NAME = 8
MIN_CHARGE = 0
MAX_CHARGE = 10

SCOPE = 'PARTIAL: charge bookkeeping only; no retinal tissue modeled'
NOT_CLAIMED = (
    'does not model phosphene mapping',
    'does not weight charges by record order',
    'does not treat 0 as odd; it adds nothing as an even charge',
    'does not compare pixels against each other',
)


def _check_name(pixel: Any, row: int) -> None:
    if not isinstance(pixel, str) or type(pixel) is not str:
        raise TypeError(
            f'row {row}: pixel must be str, got {type(pixel).__name__}')
    if not 1 <= len(pixel) <= MAX_NAME:
        raise ValueError(f'row {row}: pixel must be 1-8 chars')


def _check_charge(charge: Any, row: int) -> None:
    if type(charge) is not int:
        raise TypeError(
            f'row {row}: charge must be int, got {type(charge).__name__}')
    if not MIN_CHARGE <= charge <= MAX_CHARGE:
        raise ValueError(
            f'row {row}: charge must be {MIN_CHARGE}-{MAX_CHARGE}, got {charge}')


def see(rows: Any) -> dict:
    """Return the ledger summary for the supplied charge records."""
    if type(rows) not in (list, tuple):
        raise TypeError(f'rows must be list or tuple, got {type(rows).__name__}')
    if len(rows) > MAX_ROWS:
        raise ValueError(f'rows must contain at most {MAX_ROWS} entries')
    ledger: dict = {}
    for index, row in enumerate(rows, 1):
        if type(row) not in (list, tuple):
            raise TypeError(
                f'row {index}: expected (pixel, charge) tuple, got {type(row).__name__}')
        if len(row) != 2:
            raise ValueError(
                f'row {index}: expected 2 fields, got {len(row)}')
        pixel, charge = row
        _check_name(pixel, index)
        _check_charge(charge, index)
        ledger.setdefault(pixel, 0)
        if charge % 2 == 0:
            ledger[pixel] += charge
        else:
            ledger[pixel] -= charge
    even = sorted(pixel for pixel, balance in ledger.items()
                  if balance > 0)
    return {'total': len(rows), 'ledger': ledger, 'even': even}
