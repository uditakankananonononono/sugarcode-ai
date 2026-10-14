"""Row 990, Theranostics: confirming each probe's pairs.

A probe locks when back-to-back readings complement each other,
not when one strong reading flashes.  scan() counts each probe's
consecutive pairs of signals that sum to a full reading and
reports the probes with enough confirmations.

Input rows: (probe 1-8, signal int 0-10).  A pair confirms when
neighbouring signals sum to 10; locked is 2 confirmations.
Output: {'total', 'confirmed': {probe: confirmed consecutive
pairs}, 'locked': sorted probes with 2 confirmations}.
Reported: signals 4, 6, 4 confirm 2 pairs and lock; 5, 5 confirm
1; 5, 5, 5 confirm 2 and lock; 10, 0 confirm 1; 1, 2, 3 confirm
0; 4, 1, 6 confirm 0 because only neighbours count; 10, 10
confirm 0 since 20 overshoots; 6, 6 confirm 0 as well; a lone
signal confirms 0.
"""

from typing import Any

MAX_ROWS = 100
MAX_NAME = 8
MIN_SIGNAL = 0
MAX_SIGNAL = 10
PAIR = 10
LOCK = 2

SCOPE = 'PARTIAL: signal bookkeeping only; no imaging modeled'
NOT_CLAIMED = (
    'does not model probe decay',
    'does not count non-consecutive signal pairs',
    'does not weight confirmations by signal size',
    'does not compare probes against each other',
)


def _check_name(probe: Any, row: int) -> None:
    if not isinstance(probe, str) or type(probe) is not str:
        raise TypeError(
            f'row {row}: probe must be str, got {type(probe).__name__}')
    if not 1 <= len(probe) <= MAX_NAME:
        raise ValueError(f'row {row}: probe must be 1-8 chars')


def _check_signal(signal: Any, row: int) -> None:
    if type(signal) is not int:
        raise TypeError(
            f'row {row}: signal must be int, got {type(signal).__name__}')
    if not MIN_SIGNAL <= signal <= MAX_SIGNAL:
        raise ValueError(
            f'row {row}: signal must be {MIN_SIGNAL}-{MAX_SIGNAL}, got {signal}')


def scan(rows: Any) -> dict:
    """Return the confirmation summary for the supplied signal records."""
    if type(rows) not in (list, tuple):
        raise TypeError(f'rows must be list or tuple, got {type(rows).__name__}')
    if len(rows) > MAX_ROWS:
        raise ValueError(f'rows must contain at most {MAX_ROWS} entries')
    values: dict = {}
    for index, row in enumerate(rows, 1):
        if type(row) not in (list, tuple):
            raise TypeError(
                f'row {index}: expected (probe, signal) tuple, got {type(row).__name__}')
        if len(row) != 2:
            raise ValueError(
                f'row {index}: expected 2 fields, got {len(row)}')
        probe, signal = row
        _check_name(probe, index)
        _check_signal(signal, index)
        values.setdefault(probe, []).append(signal)
    confirmed = {}
    for probe, vals in values.items():
        count = 0
        for i in range(len(vals) - 1):
            if vals[i] + vals[i + 1] == PAIR:
                count += 1
        confirmed[probe] = count
    locked = sorted(probe for probe, count in confirmed.items()
                    if count >= LOCK)
    return {'total': len(rows), 'confirmed': confirmed, 'locked': locked}
