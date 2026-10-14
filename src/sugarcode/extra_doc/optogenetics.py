"""Row 999, Optogenetics: listening for each channel's echo.

A channel echoes when a flash level comes back, not when levels
keep changing.  flash() counts the flash levels that appear at
least twice inside the channel's own record and reports the
channels where several levels repeat.

Input rows: (channel 1-8, flash int 0-10).  Echoing is 2
repeated levels.
Output: {'total', 'echoes': {channel: repeated flash levels},
'echoing': sorted channels with 2 repeated levels}.  Reported:
flashes 1, 2, 2, 3, 3, 3 echo 2 levels and read echoing; 5, 5
echo 1; 1, 2, 3 echo 0; 4, 4, 4, 4 echo 1; 1, 1, 2, 2, 3 echo
2; 3, 3, 3 echo 1; 0, 0 echo 1; a lone flash echoes 0.
"""

from typing import Any

MAX_ROWS = 100
MAX_NAME = 8
MIN_FLASH = 0
MAX_FLASH = 10
ECHOING = 2

SCOPE = 'PARTIAL: flash bookkeeping only; no channelrhodopsin modeled'
NOT_CLAIMED = (
    'does not model light wavelengths',
    'does not count how many times a level repeats, only that it does',
    'does not weight echoes by record order',
    'does not compare channels against each other',
)


def _check_name(channel: Any, row: int) -> None:
    if not isinstance(channel, str) or type(channel) is not str:
        raise TypeError(
            f'row {row}: channel must be str, got {type(channel).__name__}')
    if not 1 <= len(channel) <= MAX_NAME:
        raise ValueError(f'row {row}: channel must be 1-8 chars')


def _check_flash(flash: Any, row: int) -> None:
    if type(flash) is not int:
        raise TypeError(
            f'row {row}: flash must be int, got {type(flash).__name__}')
    if not MIN_FLASH <= flash <= MAX_FLASH:
        raise ValueError(
            f'row {row}: flash must be {MIN_FLASH}-{MAX_FLASH}, got {flash}')


def flash(rows: Any) -> dict:
    """Return the echo summary for the supplied flash records."""
    if type(rows) not in (list, tuple):
        raise TypeError(f'rows must be list or tuple, got {type(rows).__name__}')
    if len(rows) > MAX_ROWS:
        raise ValueError(f'rows must contain at most {MAX_ROWS} entries')
    values: dict = {}
    for index, row in enumerate(rows, 1):
        if type(row) not in (list, tuple):
            raise TypeError(
                f'row {index}: expected (channel, flash) tuple, got {type(row).__name__}')
        if len(row) != 2:
            raise ValueError(
                f'row {index}: expected 2 fields, got {len(row)}')
        channel, flash = row
        _check_name(channel, index)
        _check_flash(flash, index)
        values.setdefault(channel, []).append(flash)
    echoes = {}
    for channel, vals in values.items():
        freq = {}
        for v in vals:
            freq[v] = freq.get(v, 0) + 1
        count = 0
        for f in freq.values():
            if f >= 2:
                count += 1
        echoes[channel] = count
    echoing = sorted(channel for channel, count in echoes.items()
                     if count >= ECHOING)
    return {'total': len(rows), 'echoes': echoes, 'echoing': echoing}
