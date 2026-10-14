"""Row 582 Compression Algorithm: exact run-length encoding round trip for a caller-supplied string.

The caller supplies a str of 1 to 500 characters (any characters, no digit restriction). It is encoded
as a list of (character, run length) pairs for maximal runs, decoded back and checked equal. Reported:
the runs, the run count, the original length, an encoded size model of 2 units per run (one for the
character and one for the count, a modelling choice), the ratio of encoded to original size (Fraction)
and whether the round trip matched. Caps and the size model are implementation choices, not spec
values; no real format or byte layout is used.
NOT_CLAIMED: that the size model is any real file or wire size, that RLE suits any real data,
compression of real files, speed, memory, that the ratio generalises to other inputs, approval-gate
clearance, deployment.
"""
from fractions import Fraction

NOT_CLAIMED = ('size model is any real file or wire size', 'RLE suits any real data',
               'compression of real files', 'speed or memory', 'ratio generalises to other inputs',
               'approval-gate clearance', 'deployment')


def rle(text):
    if type(text) is not str:
        raise TypeError('text must be str')
    if not 1 <= len(text) <= 500:
        raise ValueError('text length must be between 1 and 500')
    runs = []
    for ch in text:
        if runs and runs[-1][0] == ch:
            runs[-1] = (ch, runs[-1][1] + 1)
        else:
            runs.append((ch, 1))
    back = ''.join(c * n for c, n in runs)
    return {'runs': runs, 'run_count': len(runs), 'original_length': len(text),
            'encoded_units': 2 * len(runs), 'ratio': Fraction(2 * len(runs), len(text)),
            'round_trip_ok': back == text, 'compression_validated': False, 'not_claimed': NOT_CLAIMED}
