"""Row 1004, Neural Decoding: reading a channel's leaning.

A channel leans toward the parity that carries more of its
signals, not the parity that flashes loudest.  read() tallies
each channel's even and odd signals, reports which parity
leads, then lists the channels held in a tie.

Input rows: (channel 1-8, signal int 0-10).  Zero reads even.
Output: {'total', 'lean': {channel: 'even', 'odd', or 'tie'},
'steady': sorted channels held in a tie}.
Reported: signals 2, 4 lean even; 3, 5 lean odd; 2, 3 tie and
read steady; 2, 2, 3 lean even; 3, 3, 2 lean odd; 0, 1 tie;
0, 0, 1, 1, 2 lean even; a lone 7 leans odd; a lone 4 leans
even.
"""

from typing import Any

MAX_ROWS = 100
MAX_NAME = 8
MIN_SIGNAL = 0
MAX_SIGNAL = 10

SCOPE = 'PARTIAL: signal bookkeeping only; no decoding model fit'
NOT_CLAIMED = (
    'does not model firing rates',
    'does not weight signals by record order',
    'does not measure signal magnitude, only parity',
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


def read(rows: Any) -> dict:
    """Return the parity-lean summary for the supplied signal records."""
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
    lean = {}
    for channel, vals in values.items():
        evens = 0
        odds = 0
        for signal in vals:
            if signal % 2 == 0:
                evens += 1
            else:
                odds += 1
        if evens > odds:
            lean[channel] = 'even'
        elif odds > evens:
            lean[channel] = 'odd'
        else:
            lean[channel] = 'tie'
    steady = sorted(channel for channel, side in lean.items()
                    if side == 'tie')
    return {'total': len(rows), 'lean': lean, 'steady': steady}
