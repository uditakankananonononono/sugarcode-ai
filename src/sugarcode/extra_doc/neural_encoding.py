"""Row 1005, Neural Encoding: writing between a site's endpoints.

A site is written between the pulse that opened it and the pulse
that closed it, not around them.  write() takes each site's
first and last pulses in record order and counts the site's
pulses that land strictly between those two values, then reports
the sites with nothing inside.

Input rows: (site 1-8, pulse int 0-10).  Endpoints themselves
never count.
Output: {'total', 'inner': {site: pulses strictly between its
first and last values}, 'sealed': sorted sites with none inside}.
Reported: pulses 2, 3, 4, 5 hold 2 inside; 5, 1, 8, 2 hold 0
and read sealed; 3, 3 hold 0 and read sealed; a lone pulse
holds 0; 1, 5, 3, 5 hold 1; 2, 2, 7, 2 hold 0; 1, 2, 3, 4
hold 2; 5, 1, 3, 2 hold 1; 2, 8, 3 hold 0 and read sealed.
"""

from typing import Any

MAX_ROWS = 100
MAX_NAME = 8
MIN_PULSE = 0
MAX_PULSE = 10

SCOPE = 'PARTIAL: pulse bookkeeping only; no stimulation hardware modeled'
NOT_CLAIMED = (
    'does not model pulse timing',
    'does not weight pulses by position beyond the endpoints',
    'does not measure distance outside the endpoint span',
    'does not compare sites against each other',
)


def _check_name(site: Any, row: int) -> None:
    if not isinstance(site, str) or type(site) is not str:
        raise TypeError(
            f'row {row}: site must be str, got {type(site).__name__}')
    if not 1 <= len(site) <= MAX_NAME:
        raise ValueError(f'row {row}: site must be 1-8 chars')


def _check_pulse(pulse: Any, row: int) -> None:
    if type(pulse) is not int:
        raise TypeError(
            f'row {row}: pulse must be int, got {type(pulse).__name__}')
    if not MIN_PULSE <= pulse <= MAX_PULSE:
        raise ValueError(
            f'row {row}: pulse must be {MIN_PULSE}-{MAX_PULSE}, got {pulse}')


def write(rows: Any) -> dict:
    """Return the endpoint-interior summary for the supplied pulse records."""
    if type(rows) not in (list, tuple):
        raise TypeError(f'rows must be list or tuple, got {type(rows).__name__}')
    if len(rows) > MAX_ROWS:
        raise ValueError(f'rows must contain at most {MAX_ROWS} entries')
    values: dict = {}
    for index, row in enumerate(rows, 1):
        if type(row) not in (list, tuple):
            raise TypeError(
                f'row {index}: expected (site, pulse) tuple, got {type(row).__name__}')
        if len(row) != 2:
            raise ValueError(
                f'row {index}: expected 2 fields, got {len(row)}')
        site, pulse = row
        _check_name(site, index)
        _check_pulse(pulse, index)
        values.setdefault(site, []).append(pulse)
    inner = {}
    for site, vals in values.items():
        lo = min(vals[0], vals[-1])
        hi = max(vals[0], vals[-1])
        count = 0
        for v in vals:
            if lo < v < hi:
                count += 1
        inner[site] = count
    sealed = sorted(site for site, count in inner.items() if count == 0)
    return {'total': len(rows), 'inner': inner, 'sealed': sealed}
