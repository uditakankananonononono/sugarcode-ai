"""Row 961, Organ Printing: checking every required layer is printed.

A replacement organ comes out only when each of its four required
layers has been printed at least once; anything short of the full
set leaves a gap in the organ.  complete() collects the printed
layers per organ and reports which organs have the full set and
which layers the rest still miss.

Input rows: (organ 1-8, layer int 1-4).  Output: {'total',
'complete': sorted organs with all four layers, 'missing': {organ:
sorted missing layers} for the incomplete organs}.  Reported:
layers 1, 2, 4 leave the organ missing [3]; printing the same layer
twice does not help; an organ named in no record appears nowhere in
the output; a complete organ has no entry in missing.
"""

from typing import Any

MAX_ROWS = 100
MAX_NAME = 8
MIN_LAYER = 1
MAX_LAYER = 4
REQUIRED = frozenset({1, 2, 3, 4})

SCOPE = 'PARTIAL: layer-set bookkeeping only; no organ biology modeled'
NOT_CLAIMED = (
    'does not model cell placement within a layer',
    'does not simulate vascularization',
    'does not order the layers into a print sequence',
    'does not track partially printed layers',
)


def _check_name(organ: Any, row: int) -> None:
    if not isinstance(organ, str) or type(organ) is not str:
        raise TypeError(
            f'row {row}: organ must be str, got {type(organ).__name__}')
    if not 1 <= len(organ) <= MAX_NAME:
        raise ValueError(f'row {row}: organ must be 1-8 chars')


def _check_layer(layer: Any, row: int) -> None:
    if type(layer) is not int:
        raise TypeError(
            f'row {row}: layer must be int, got {type(layer).__name__}')
    if not MIN_LAYER <= layer <= MAX_LAYER:
        raise ValueError(
            f'row {row}: layer must be {MIN_LAYER}-{MAX_LAYER}, got {layer}')


def complete(rows: Any) -> dict:
    """Return the layer summary for the supplied print records."""
    if type(rows) not in (list, tuple):
        raise TypeError(f'rows must be list or tuple, got {type(rows).__name__}')
    if len(rows) > MAX_ROWS:
        raise ValueError(f'rows must contain at most {MAX_ROWS} entries')
    printed: dict = {}
    for index, row in enumerate(rows, 1):
        if type(row) not in (list, tuple):
            raise TypeError(
                f'row {index}: expected (organ, layer) tuple, got {type(row).__name__}')
        if len(row) != 2:
            raise ValueError(
                f'row {index}: expected 2 fields, got {len(row)}')
        organ, layer = row
        _check_name(organ, index)
        _check_layer(layer, index)
        printed.setdefault(organ, set()).add(layer)
    done = sorted(organ for organ in printed if printed[organ] >= REQUIRED)
    missing = {organ: sorted(REQUIRED - printed[organ])
               for organ in printed if not printed[organ] >= REQUIRED}
    return {'total': len(rows), 'complete': done, 'missing': missing}
