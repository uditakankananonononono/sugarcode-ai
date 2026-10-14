"""Row 980, Pharmacogenomics: cancelling each gene's signals.

A gene whose effects pair off reads as quiet, while anything left
over is a live signal.  panel() folds each gene's effects together
with bitwise XOR - matched pairs cancel - and reports the genes
whose signal cancels to zero.

Input rows: (gene 1-8, effect int 0-10).
Output: {'total', 'signals': {gene: XOR of its effects},
'clear': sorted genes whose signal is 0}.  Reported: effects 3, 3
cancel to 0 and clear; 1, 2, 3 cancel to 0 too; 3, 5 leave 6; a
lone effect signals itself; cancellation needs matching pairs, so
4, 4, 4 leaves 4.
"""

from typing import Any

MAX_ROWS = 100
MAX_NAME = 8
MIN_EFFECT = 0
MAX_EFFECT = 10

SCOPE = 'PARTIAL: effect bookkeeping only; no gene-drug mechanism modeled'
NOT_CLAIMED = (
    'does not model metabolic pathways',
    'does not weight effects by record order',
    'does not compare genes against each other',
    'does not cap the signal during accumulation',
)


def _check_name(gene: Any, row: int) -> None:
    if not isinstance(gene, str) or type(gene) is not str:
        raise TypeError(
            f'row {row}: gene must be str, got {type(gene).__name__}')
    if not 1 <= len(gene) <= MAX_NAME:
        raise ValueError(f'row {row}: gene must be 1-8 chars')


def _check_effect(effect: Any, row: int) -> None:
    if type(effect) is not int:
        raise TypeError(
            f'row {row}: effect must be int, got {type(effect).__name__}')
    if not MIN_EFFECT <= effect <= MAX_EFFECT:
        raise ValueError(
            f'row {row}: effect must be {MIN_EFFECT}-{MAX_EFFECT}, got {effect}')


def panel(rows: Any) -> dict:
    """Return the signal summary for the supplied effect records."""
    if type(rows) not in (list, tuple):
        raise TypeError(f'rows must be list or tuple, got {type(rows).__name__}')
    if len(rows) > MAX_ROWS:
        raise ValueError(f'rows must contain at most {MAX_ROWS} entries')
    signals: dict = {}
    for index, row in enumerate(rows, 1):
        if type(row) not in (list, tuple):
            raise TypeError(
                f'row {index}: expected (gene, effect) tuple, got {type(row).__name__}')
        if len(row) != 2:
            raise ValueError(
                f'row {index}: expected 2 fields, got {len(row)}')
        gene, effect = row
        _check_name(gene, index)
        _check_effect(effect, index)
        if gene not in signals:
            signals[gene] = 0
        signals[gene] ^= effect
    clear = sorted(gene for gene, signal in signals.items()
                   if signal == 0)
    return {'total': len(rows), 'signals': signals, 'clear': clear}
