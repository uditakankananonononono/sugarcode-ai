"""Row 996, Cochlear Implants: splitting each electrode's stream.

An electrode is steady when its pulses never change pitch, not
when they stay loud.  hear() counts the maximal runs of equal
pulses inside the electrode's own stream and reports the
electrodes that hold a single run.

Input rows: (electrode 1-8, pulse int 0-10).  Steady is a
single run.
Output: {'total', 'segments': {electrode: run count}, 'steady':
sorted electrodes holding one run}.  Reported: pulses 5, 5, 2,
2, 2, 5 split into 3 runs; 1, 2, 3 split into 3; 5, 5 hold 1
run and read steady; 1, 1, 2, 1 split into 3; 2, 2 hold 1;
1, 2, 1, 2 split into 4; 0, 0, 10 split into 2; a lone pulse
holds 1 run.
"""

from typing import Any

MAX_ROWS = 100
MAX_NAME = 8
MIN_PULSE = 0
MAX_PULSE = 10

SCOPE = 'PARTIAL: pulse bookkeeping only; no auditory nerve modeled'
NOT_CLAIMED = (
    'does not model pitch mapping',
    'does not measure run lengths, only how many runs there are',
    'does not merge equal runs separated by other pulses',
    'does not compare electrodes against each other',
)


def _check_name(electrode: Any, row: int) -> None:
    if not isinstance(electrode, str) or type(electrode) is not str:
        raise TypeError(
            f'row {row}: electrode must be str, got {type(electrode).__name__}')
    if not 1 <= len(electrode) <= MAX_NAME:
        raise ValueError(f'row {row}: electrode must be 1-8 chars')


def _check_pulse(pulse: Any, row: int) -> None:
    if type(pulse) is not int:
        raise TypeError(
            f'row {row}: pulse must be int, got {type(pulse).__name__}')
    if not MIN_PULSE <= pulse <= MAX_PULSE:
        raise ValueError(
            f'row {row}: pulse must be {MIN_PULSE}-{MAX_PULSE}, got {pulse}')


def hear(rows: Any) -> dict:
    """Return the segment summary for the supplied pulse records."""
    if type(rows) not in (list, tuple):
        raise TypeError(f'rows must be list or tuple, got {type(rows).__name__}')
    if len(rows) > MAX_ROWS:
        raise ValueError(f'rows must contain at most {MAX_ROWS} entries')
    values: dict = {}
    for index, row in enumerate(rows, 1):
        if type(row) not in (list, tuple):
            raise TypeError(
                f'row {index}: expected (electrode, pulse) tuple, got {type(row).__name__}')
        if len(row) != 2:
            raise ValueError(
                f'row {index}: expected 2 fields, got {len(row)}')
        electrode, pulse = row
        _check_name(electrode, index)
        _check_pulse(pulse, index)
        values.setdefault(electrode, []).append(pulse)
    segments = {}
    for electrode, vals in values.items():
        segs = 1
        for i in range(1, len(vals)):
            if vals[i] != vals[i - 1]:
                segs += 1
        segments[electrode] = segs
    steady = sorted(electrode for electrode, segs in segments.items()
                    if segs == 1)
    return {'total': len(rows), 'segments': segments, 'steady': steady}
