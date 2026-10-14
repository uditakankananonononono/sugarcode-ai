"""Row 993, Implantable Devices: checking each device's readings.

A device aligns when its readings land on their own positions,
not when big numbers pile up.  monitor() counts the readings
that equal their 1-based position inside the device's own
sequence and reports the devices with repeated matches.

Input rows: (device 1-8, reading int 0-10).  Aligned is 2
position matches.
Output: {'total', 'checks': {device: readings matching their
position}, 'aligned': sorted devices with 2 matches}.
Reported: readings 1, 2, 3 check 3 times and align; 2, 2, 2
check once; 1, 1, 3 check twice and align; 3, 2, 1 check once;
2, 1 check 0; 0, 2 check once since 0 never matches its
1-based position; 5, 5, 5, 5, 5 check once; a lone 1 checks
once.
"""

from typing import Any

MAX_ROWS = 100
MAX_NAME = 8
MIN_READING = 0
MAX_READING = 10
ALIGNED = 2

SCOPE = 'PARTIAL: reading bookkeeping only; no implant hardware modeled'
NOT_CLAIMED = (
    'does not model battery or telemetry',
    'does not weight readings by how far they miss',
    'does not compare positions across devices',
    'does not cap how many readings one device may hold',
)


def _check_name(device: Any, row: int) -> None:
    if not isinstance(device, str) or type(device) is not str:
        raise TypeError(
            f'row {row}: device must be str, got {type(device).__name__}')
    if not 1 <= len(device) <= MAX_NAME:
        raise ValueError(f'row {row}: device must be 1-8 chars')


def _check_reading(reading: Any, row: int) -> None:
    if type(reading) is not int:
        raise TypeError(
            f'row {row}: reading must be int, got {type(reading).__name__}')
    if not MIN_READING <= reading <= MAX_READING:
        raise ValueError(
            f'row {row}: reading must be {MIN_READING}-{MAX_READING}, got {reading}')


def monitor(rows: Any) -> dict:
    """Return the position-check summary for the supplied readings."""
    if type(rows) not in (list, tuple):
        raise TypeError(f'rows must be list or tuple, got {type(rows).__name__}')
    if len(rows) > MAX_ROWS:
        raise ValueError(f'rows must contain at most {MAX_ROWS} entries')
    values: dict = {}
    for index, row in enumerate(rows, 1):
        if type(row) not in (list, tuple):
            raise TypeError(
                f'row {index}: expected (device, reading) tuple, got {type(row).__name__}')
        if len(row) != 2:
            raise ValueError(
                f'row {index}: expected 2 fields, got {len(row)}')
        device, reading = row
        _check_name(device, index)
        _check_reading(reading, index)
        values.setdefault(device, []).append(reading)
    checks = {}
    for device, vals in values.items():
        count = 0
        for pos, v in enumerate(vals, 1):
            if v == pos:
                count += 1
        checks[device] = count
    aligned = sorted(device for device, count in checks.items()
                     if count >= ALIGNED)
    return {'total': len(rows), 'checks': checks, 'aligned': aligned}
