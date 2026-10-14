"""Row 954, Negative Index Materials: running the phase backwards.

In a negative-index slab the phase velocity reverses, so a wave's phase
walks backwards around the cycle as it propagates.  refract() folds the
supplied advances per wave, subtracting them from the launch phase and
wrapping around the 12-step cycle, and reports the waves that end in the
reversed half of the cycle.

Input rows: (wave 1-8, advance int 0-10).  Launch phase is 10; final
phase is (10 - total advance) modulo 12.  Output: {'total', 'phases':
{wave: final phase}, 'reversed': sorted waves at phase 6 or above}.
Reported: advance 4 lands exactly on 6 and counts as reversed; advance 5
lands on 5 and does not; a total advance of 16 (10 + 6 across records)
wraps backwards to 6; the comparison
is strict at the lower edge only by the 6-or-above rule.
"""

from typing import Any

MAX_ROWS = 100
MAX_NAME = 8
MIN_ADVANCE = 0
MAX_ADVANCE = 10
LAUNCH_PHASE = 10
PERIOD = 12
REVERSED_FROM = 6

SCOPE = 'PARTIAL: phase bookkeeping only; no field simulation'
NOT_CLAIMED = (
    'does not solve Maxwell equations',
    'does not model dispersion or loss',
    'does not compute ray trajectories',
    'does not model interfaces between slabs',
)


def _check_name(wave: Any, row: int) -> None:
    if not isinstance(wave, str) or type(wave) is not str:
        raise TypeError(
            f'row {row}: wave must be str, got {type(wave).__name__}')
    if not 1 <= len(wave) <= MAX_NAME:
        raise ValueError(f'row {row}: wave must be 1-8 chars')


def _check_advance(advance: Any, row: int) -> None:
    if type(advance) is not int:
        raise TypeError(
            f'row {row}: advance must be int, got {type(advance).__name__}')
    if not MIN_ADVANCE <= advance <= MAX_ADVANCE:
        raise ValueError(
            f'row {row}: advance must be {MIN_ADVANCE}-{MAX_ADVANCE}, got {advance}')


def refract(rows: Any) -> dict:
    """Return the phase summary for the supplied advance records."""
    if type(rows) not in (list, tuple):
        raise TypeError(f'rows must be list or tuple, got {type(rows).__name__}')
    if len(rows) > MAX_ROWS:
        raise ValueError(f'rows must contain at most {MAX_ROWS} entries')
    advances: dict = {}
    for index, row in enumerate(rows, 1):
        if type(row) not in (list, tuple):
            raise TypeError(
                f'row {index}: expected (wave, advance) tuple, got {type(row).__name__}')
        if len(row) != 2:
            raise ValueError(
                f'row {index}: expected 2 fields, got {len(row)}')
        wave, advance = row
        _check_name(wave, index)
        _check_advance(advance, index)
        advances[wave] = advances.get(wave, 0) + advance
    phases = {
        wave: (LAUNCH_PHASE - total) % PERIOD
        for wave, total in advances.items()
    }
    reversed_waves = sorted(
        wave for wave, phase in phases.items() if phase >= REVERSED_FROM)
    return {'total': len(rows), 'phases': phases, 'reversed': reversed_waves}
