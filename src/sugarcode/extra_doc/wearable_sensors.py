"""Row 992, Wearable Sensors: counting each sensor's peaks.

A sensor is peaky when it keeps returning to its own top, not when
one spike stands alone.  track() finds each sensor's peak reading,
counts how many readings sit at that peak, and reports the sensors
that peak again and again.

Input rows: (sensor 1-8, reading int 0-10).  Peaky is 3 readings
at the peak.
Output: {'total', 'peaks': {sensor: readings at its peak},
'peaky': sorted sensors with 3 peak readings}.  Reported:
readings 3, 5, 5, 2 peak twice; 5, 5, 5 peak 3 times and mark
peaky; 1, 2 peak once; 4, 5, 5 peak twice; 0, 0, 0 peak 3 times
at a zero peak; 5, 1, 5 peak twice; 2, 2 peak twice; a lone
reading peaks once.
"""

from typing import Any

MAX_ROWS = 100
MAX_NAME = 8
MIN_READING = 0
MAX_READING = 10
PEAKY = 3

SCOPE = 'PARTIAL: reading bookkeeping only; no sampling hardware modeled'
NOT_CLAIMED = (
    'does not model sampling rate or drift',
    'does not weight peak readings by record order',
    'does not count readings near the peak, only at it',
    'does not compare sensors against each other',
)


def _check_name(sensor: Any, row: int) -> None:
    if not isinstance(sensor, str) or type(sensor) is not str:
        raise TypeError(
            f'row {row}: sensor must be str, got {type(sensor).__name__}')
    if not 1 <= len(sensor) <= MAX_NAME:
        raise ValueError(f'row {row}: sensor must be 1-8 chars')


def _check_reading(reading: Any, row: int) -> None:
    if type(reading) is not int:
        raise TypeError(
            f'row {row}: reading must be int, got {type(reading).__name__}')
    if not MIN_READING <= reading <= MAX_READING:
        raise ValueError(
            f'row {row}: reading must be {MIN_READING}-{MAX_READING}, got {reading}')


def track(rows: Any) -> dict:
    """Return the peak summary for the supplied sensor records."""
    if type(rows) not in (list, tuple):
        raise TypeError(f'rows must be list or tuple, got {type(rows).__name__}')
    if len(rows) > MAX_ROWS:
        raise ValueError(f'rows must contain at most {MAX_ROWS} entries')
    values: dict = {}
    for index, row in enumerate(rows, 1):
        if type(row) not in (list, tuple):
            raise TypeError(
                f'row {index}: expected (sensor, reading) tuple, got {type(row).__name__}')
        if len(row) != 2:
            raise ValueError(
                f'row {index}: expected 2 fields, got {len(row)}')
        sensor, reading = row
        _check_name(sensor, index)
        _check_reading(reading, index)
        values.setdefault(sensor, []).append(reading)
    peaks = {}
    for sensor, vals in values.items():
        mx = max(vals)
        count = 0
        for v in vals:
            if v == mx:
                count += 1
        peaks[sensor] = count
    peaky = sorted(sensor for sensor, count in peaks.items()
                   if count >= PEAKY)
    return {'total': len(rows), 'peaks': peaks, 'peaky': peaky}
