"""Row 1001, Neurofeedback: settling each wave's shortfall.

A wave is calm when every amplitude sits at its own peak, not
when the peak flashes once.  train() squares each amplitude's
shortfall from the wave's own peak and sums the squares, then
reports the waves with no shortfall at all.

Input rows: (wave 1-8, amplitude int 0-10).  Calm is a
shortfall of 0.
Output: {'total', 'lags': {wave: summed squared shortfall
from its peak}, 'calm': sorted waves with no shortfall}.
Reported: amplitudes 1, 3 lag 4; 3, 3 lag 0 and read calm;
0, 2, 2 lag 4; 2, 3 lag 1; 0, 3 lag 9; 1, 2, 3 lag 5;
3, 1 lag 4; a lone amplitude lags 0.
"""

from typing import Any

MAX_ROWS = 100
MAX_NAME = 8
MIN_AMPLITUDE = 0
MAX_AMPLITUDE = 10

SCOPE = 'PARTIAL: amplitude bookkeeping only; no EEG hardware modeled'
NOT_CLAIMED = (
    'does not model frequency bands',
    'does not weight shortfalls by record order',
    'does not measure depth below the peak, only squared distance',
    'does not compare waves against each other',
)


def _check_name(wave: Any, row: int) -> None:
    if not isinstance(wave, str) or type(wave) is not str:
        raise TypeError(
            f'row {row}: wave must be str, got {type(wave).__name__}')
    if not 1 <= len(wave) <= MAX_NAME:
        raise ValueError(f'row {row}: wave must be 1-8 chars')


def _check_amplitude(amplitude: Any, row: int) -> None:
    if type(amplitude) is not int:
        raise TypeError(
            f'row {row}: amplitude must be int, got {type(amplitude).__name__}')
    if not MIN_AMPLITUDE <= amplitude <= MAX_AMPLITUDE:
        raise ValueError(
            f'row {row}: amplitude must be {MIN_AMPLITUDE}-{MAX_AMPLITUDE}, got {amplitude}')


def train(rows: Any) -> dict:
    """Return the shortfall summary for the supplied amplitude records."""
    if type(rows) not in (list, tuple):
        raise TypeError(f'rows must be list or tuple, got {type(rows).__name__}')
    if len(rows) > MAX_ROWS:
        raise ValueError(f'rows must contain at most {MAX_ROWS} entries')
    values: dict = {}
    for index, row in enumerate(rows, 1):
        if type(row) not in (list, tuple):
            raise TypeError(
                f'row {index}: expected (wave, amplitude) tuple, got {type(row).__name__}')
        if len(row) != 2:
            raise ValueError(
                f'row {index}: expected 2 fields, got {len(row)}')
        wave, amplitude = row
        _check_name(wave, index)
        _check_amplitude(amplitude, index)
        values.setdefault(wave, []).append(amplitude)
    lags = {}
    for wave, vals in values.items():
        peak = max(vals)
        lag = 0
        for v in vals:
            lag += (peak - v) * (peak - v)
        lags[wave] = lag
    calm = sorted(wave for wave, lag in lags.items() if lag == 0)
    return {'total': len(rows), 'lags': lags, 'calm': calm}
