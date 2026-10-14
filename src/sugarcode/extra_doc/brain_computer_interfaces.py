"""Row 994, Brain-Computer Interfaces: untangling each channel.

A channel reads smooth when its signals never arrive out of
order, not when they merely end high.  link() counts each
channel's tangled pairs - earlier signals that exceed later
ones - and reports the channels with no tangles.

Input rows: (channel 1-8, signal int 0-10).  Smooth is 0
tangled pairs.
Output: {'total', 'tangles': {channel: out-of-order signal
pairs}, 'smooth': sorted channels with no tangles}.
Reported: signals 1, 2, 3 tangle 0 and read smooth; 1, 1
tangle 0 since equal signals do not tangle; 3, 2, 1 tangle 3;
2, 1, 2 tangle 1; 3, 1, 2 tangle 2; 2, 2, 1 tangle 2; 1, 2, 1
tangle 1; 10, 0 tangle 1; a lone signal tangles 0.
"""

from typing import Any

MAX_ROWS = 100
MAX_NAME = 8
MIN_SIGNAL = 0
MAX_SIGNAL = 10

SCOPE = 'PARTIAL: signal bookkeeping only; no neural decoding modeled'
NOT_CLAIMED = (
    'does not model electrode placement',
    'does not count only consecutive drops; every pair counts',
    'does not weight tangles by how far signals drop',
    'does not compare channels against each other',
)


def _check_name(channel: Any, row: int) -> None:
    if not isinstance(channel, str) or type(channel) is not str:
        raise TypeError(
            f'row {row}: channel must be str, got {type(channel).__name__}')
    if not 1 <= len(channel) <= MAX_NAME:
        raise ValueError(f'row {row}: channel must be 1-8 chars')


def _check_signal(signal: Any, row: int) -> None:
    if type(signal) is not int:
        raise TypeError(
            f'row {row}: signal must be int, got {type(signal).__name__}')
    if not MIN_SIGNAL <= signal <= MAX_SIGNAL:
        raise ValueError(
            f'row {row}: signal must be {MIN_SIGNAL}-{MAX_SIGNAL}, got {signal}')


def link(rows: Any) -> dict:
    """Return the tangle summary for the supplied signal records."""
    if type(rows) not in (list, tuple):
        raise TypeError(f'rows must be list or tuple, got {type(rows).__name__}')
    if len(rows) > MAX_ROWS:
        raise ValueError(f'rows must contain at most {MAX_ROWS} entries')
    values: dict = {}
    for index, row in enumerate(rows, 1):
        if type(row) not in (list, tuple):
            raise TypeError(
                f'row {index}: expected (channel, signal) tuple, got {type(row).__name__}')
        if len(row) != 2:
            raise ValueError(
                f'row {index}: expected 2 fields, got {len(row)}')
        channel, signal = row
        _check_name(channel, index)
        _check_signal(signal, index)
        values.setdefault(channel, []).append(signal)
    tangles = {}
    for channel, vals in values.items():
        count = 0
        for i, a in enumerate(vals):
            for b in vals[i + 1:]:
                if a > b:
                    count += 1
        tangles[channel] = count
    smooth = sorted(channel for channel, count in tangles.items()
                    if count == 0)
    return {'total': len(rows), 'tangles': tangles, 'smooth': smooth}
