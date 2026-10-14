"""Row 977, Drug Discovery: spanning each compound's results.

A compound whose potency lands in a tight window is easier to trust
than one scattered across the scale.  screen() measures each
compound's span - its highest potency minus its lowest - and reports
the compounds whose span stays inside the focus band.

Input rows: (compound 1-8, potency int 0-10).  Focus band is 3.
Output: {'total', 'spans': {compound: highest minus lowest potency},
'focused': sorted compounds spanning at most 3}.  Reported:
potencies 2, 7, 4 span 5 and lose focus; 2, 5, 4 span 3 and stay
focused; a lone record spans 0; a span of exactly 3 still counts
focused; the order never matters, so 7, 2, 4 spans 5 too.
"""

from typing import Any

MAX_ROWS = 100
MAX_NAME = 8
MIN_POTENCY = 0
MAX_POTENCY = 10
FOCUS = 3

SCOPE = 'PARTIAL: potency bookkeeping only; no pharmacology modeled'
NOT_CLAIMED = (
    'does not model dose response curves',
    'does not weight potency by record order',
    'does not compare compounds against each other',
    'does not cap the potency during accumulation',
)


def _check_name(compound: Any, row: int) -> None:
    if not isinstance(compound, str) or type(compound) is not str:
        raise TypeError(
            f'row {row}: compound must be str, got {type(compound).__name__}')
    if not 1 <= len(compound) <= MAX_NAME:
        raise ValueError(f'row {row}: compound must be 1-8 chars')


def _check_potency(potency: Any, row: int) -> None:
    if type(potency) is not int:
        raise TypeError(
            f'row {row}: potency must be int, got {type(potency).__name__}')
    if not MIN_POTENCY <= potency <= MAX_POTENCY:
        raise ValueError(
            f'row {row}: potency must be {MIN_POTENCY}-{MAX_POTENCY}, got {potency}')


def screen(rows: Any) -> dict:
    """Return the span summary for the supplied potency records."""
    if type(rows) not in (list, tuple):
        raise TypeError(f'rows must be list or tuple, got {type(rows).__name__}')
    if len(rows) > MAX_ROWS:
        raise ValueError(f'rows must contain at most {MAX_ROWS} entries')
    lows: dict = {}
    highs: dict = {}
    for index, row in enumerate(rows, 1):
        if type(row) not in (list, tuple):
            raise TypeError(
                f'row {index}: expected (compound, potency) tuple, got {type(row).__name__}')
        if len(row) != 2:
            raise ValueError(
                f'row {index}: expected 2 fields, got {len(row)}')
        compound, potency = row
        _check_name(compound, index)
        _check_potency(potency, index)
        if compound not in lows:
            lows[compound] = potency
            highs[compound] = potency
        else:
            lows[compound] = min(lows[compound], potency)
            highs[compound] = max(highs[compound], potency)
    spans = {compound: highs[compound] - lows[compound] for compound in lows}
    focused = sorted(compound for compound, span in spans.items()
                     if span <= FOCUS)
    return {'total': len(rows), 'spans': spans, 'focused': focused}
