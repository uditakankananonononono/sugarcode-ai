"""Row 998, Deep Brain Stimulation: timing each region's climbs.

A region is rising when its pulses keep topping themselves, not
when one pulse spikes alone.  stimulate() times each region's
longest run of strictly increasing pulses and reports the
regions whose climb lasts.

Input rows: (region 1-8, pulse int 0-10).  Rising is a climb
of 3.
Output: {'total', 'climbs': {region: longest strictly
increasing run}, 'rising': sorted regions climbing to 3}.
Reported: pulses 1, 2, 3, 2, 3 climb to 3; 5, 5, 5 climb to 1
since equal pulses do not climb; 1, 2, 1, 2, 3 climb to 3;
3, 2, 1 climb to 1; 1, 3, 2 climb to 2; 1, 1, 2 climb to 2;
1, 2, 2 climb to 2; 2, 2 climb to 1; a lone pulse climbs to 1.
"""

from typing import Any

MAX_ROWS = 100
MAX_NAME = 8
MIN_PULSE = 0
MAX_PULSE = 10
RISING = 3

SCOPE = 'PARTIAL: pulse bookkeeping only; no neural circuitry modeled'
NOT_CLAIMED = (
    'does not model electrode impedance',
    'does not count equal pulses as climbing',
    'does not merge climbs across a flat or falling pulse',
    'does not compare regions against each other',
)


def _check_name(region: Any, row: int) -> None:
    if not isinstance(region, str) or type(region) is not str:
        raise TypeError(
            f'row {row}: region must be str, got {type(region).__name__}')
    if not 1 <= len(region) <= MAX_NAME:
        raise ValueError(f'row {row}: region must be 1-8 chars')


def _check_pulse(pulse: Any, row: int) -> None:
    if type(pulse) is not int:
        raise TypeError(
            f'row {row}: pulse must be int, got {type(pulse).__name__}')
    if not MIN_PULSE <= pulse <= MAX_PULSE:
        raise ValueError(
            f'row {row}: pulse must be {MIN_PULSE}-{MAX_PULSE}, got {pulse}')


def stimulate(rows: Any) -> dict:
    """Return the climb summary for the supplied pulse records."""
    if type(rows) not in (list, tuple):
        raise TypeError(f'rows must be list or tuple, got {type(rows).__name__}')
    if len(rows) > MAX_ROWS:
        raise ValueError(f'rows must contain at most {MAX_ROWS} entries')
    values: dict = {}
    for index, row in enumerate(rows, 1):
        if type(row) not in (list, tuple):
            raise TypeError(
                f'row {index}: expected (region, pulse) tuple, got {type(row).__name__}')
        if len(row) != 2:
            raise ValueError(
                f'row {index}: expected 2 fields, got {len(row)}')
        region, pulse = row
        _check_name(region, index)
        _check_pulse(pulse, index)
        values.setdefault(region, []).append(pulse)
    climbs = {}
    for region, vals in values.items():
        best = 1
        run = 1
        for i in range(1, len(vals)):
            if vals[i] > vals[i - 1]:
                run += 1
                best = max(best, run)
            else:
                run = 1
        climbs[region] = best
    rising = sorted(region for region, best in climbs.items()
                    if best >= RISING)
    return {'total': len(rows), 'climbs': climbs, 'rising': rising}
