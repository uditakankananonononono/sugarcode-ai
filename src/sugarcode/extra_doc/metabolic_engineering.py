"""Row 971, Metabolic Engineering: reading each pathway's bottleneck.

A tuned pathway keeps every flux strong, so its weakest record says
more about it than its best one.  tune() takes each pathway's lowest
flux as its bottleneck and reports the pathways whose bottleneck
still clears the strength floor.

Input rows: (pathway 1-8, flux int 0-10).  Strength floor is 5.
Output: {'total', 'bottlenecks': {pathway: lowest flux},
'strong': sorted pathways whose bottleneck is at least 5}.
Reported: fluxes 6, 8, 7 give a bottleneck of 6 and stay strong;
fluxes 6 then 4 give a bottleneck of 4 and drop strong; a lone flux
is its own bottleneck; a bottleneck of exactly 5 still counts
strong; one weak record drags the whole pathway down.
"""

from typing import Any

MAX_ROWS = 100
MAX_NAME = 8
MIN_FLUX = 0
MAX_FLUX = 10
FLOOR = 5

SCOPE = 'PARTIAL: flux bookkeeping only; no reaction kinetics modeled'
NOT_CLAIMED = (
    'does not model enzyme saturation',
    'does not weight fluxes by record order',
    'does not compare pathways against each other',
    'does not cap the flux during accumulation',
)


def _check_name(pathway: Any, row: int) -> None:
    if not isinstance(pathway, str) or type(pathway) is not str:
        raise TypeError(
            f'row {row}: pathway must be str, got {type(pathway).__name__}')
    if not 1 <= len(pathway) <= MAX_NAME:
        raise ValueError(f'row {row}: pathway must be 1-8 chars')


def _check_flux(flux: Any, row: int) -> None:
    if type(flux) is not int:
        raise TypeError(
            f'row {row}: flux must be int, got {type(flux).__name__}')
    if not MIN_FLUX <= flux <= MAX_FLUX:
        raise ValueError(
            f'row {row}: flux must be {MIN_FLUX}-{MAX_FLUX}, got {flux}')


def tune(rows: Any) -> dict:
    """Return the bottleneck summary for the supplied flux records."""
    if type(rows) not in (list, tuple):
        raise TypeError(f'rows must be list or tuple, got {type(rows).__name__}')
    if len(rows) > MAX_ROWS:
        raise ValueError(f'rows must contain at most {MAX_ROWS} entries')
    bottlenecks: dict = {}
    for index, row in enumerate(rows, 1):
        if type(row) not in (list, tuple):
            raise TypeError(
                f'row {index}: expected (pathway, flux) tuple, got {type(row).__name__}')
        if len(row) != 2:
            raise ValueError(
                f'row {index}: expected 2 fields, got {len(row)}')
        pathway, flux = row
        _check_name(pathway, index)
        _check_flux(flux, index)
        if pathway not in bottlenecks:
            bottlenecks[pathway] = flux
        else:
            bottlenecks[pathway] = min(bottlenecks[pathway], flux)
    strong = sorted(pathway for pathway, low in bottlenecks.items()
                    if low >= FLOOR)
    return {'total': len(rows), 'bottlenecks': bottlenecks, 'strong': strong}
