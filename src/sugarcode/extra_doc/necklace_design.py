"""Row 328, Jewelry Design: exact length, symmetry and graduation checks for a bead necklace.

A necklace is a list of bead diameters in millimetres, in order along the string.
- check_necklace(beads, clasp_mm, target_mm, tolerance_mm) returns the strung length
  (sum of diameters plus clasp), the gap to the target (length - target), within_tolerance
  (|gap| <= tolerance), symmetric (the sequence reads the same both ways) and graduated
  (sizes never decrease up to the middle and never increase after it).
- graduated_symmetric(beads) arranges the same beads, as a multiset, into the one graduated
  symmetric order if one exists: each size is split in halves, the halves run smallest to largest,
  an odd bead out sits in the middle, the halves are mirrored. It exists exactly when at most
  one size occurs an odd number of times, that is only allowed for an odd bead count, and the odd
  bead out is not smaller than any other bead (it sits at the peak). It returns {'possible': False, 'arrangement': None, 'odd_sizes': [...]} otherwise.
Caps: 1 to 24 beads of 1 to 30 mm, clasp 0 to 100 mm, target 1 to 2000 mm, tolerance 0 to 200 mm;
all values nonbool int. Order of checks: beads (type, count, then each value), then clasp, target and
tolerance, and only then any computation.

NOT_CLAIMED: arithmetic on sizes only. It does not judge beauty, wearability, comfort, strength of
the string or clasp, material, weight, price, or fashion; no rendering. No clinical or wet-lab claim.
"""
from collections import Counter

MAX_BEADS = 24


def _int(v, what):
    if type(v) is not int:
        raise TypeError(what + ' must be a nonbool int')


def _beads(beads):
    if type(beads) not in (list, tuple):
        raise TypeError('beads must be a list or tuple')
    if not 1 <= len(beads) <= MAX_BEADS:
        raise ValueError('bead count must be between 1 and 24')
    for b in beads:
        _int(b, 'bead size')
        if not 1 <= b <= 30:
            raise ValueError('bead size must be between 1 and 30 mm')


def check_necklace(beads, clasp_mm, target_mm, tolerance_mm):
    _beads(beads)
    _int(clasp_mm, 'clasp_mm')
    _int(target_mm, 'target_mm')
    _int(tolerance_mm, 'tolerance_mm')
    if not 0 <= clasp_mm <= 100:
        raise ValueError('clasp_mm must be between 0 and 100')
    if not 1 <= target_mm <= 2000:
        raise ValueError('target_mm must be between 1 and 2000')
    if not 0 <= tolerance_mm <= 200:
        raise ValueError('tolerance_mm must be between 0 and 200')
    b = list(beads)
    n = len(b)
    length = sum(b) + clasp_mm
    gap = length - target_mm
    # up to the middle bead (index (n-1)//2) then down
    peak = (n - 1) // 2
    graduated = (all(b[i] <= b[i + 1] for i in range(peak))
                 and all(b[i] >= b[i + 1] for i in range(n - n // 2 - 1, n - 1)))
    return {'length_mm': length, 'gap_mm': gap, 'within_tolerance': abs(gap) <= tolerance_mm,
            'symmetric': b == b[::-1], 'graduated': graduated, 'bead_count': n}


def graduated_symmetric(beads):
    _beads(beads)
    c = Counter(beads)
    odd = sorted(k for k, v in c.items() if v % 2)
    n = len(beads)
    if len(odd) != n % 2 or (odd and odd[0] < max(beads)):
        return {'possible': False, 'arrangement': None, 'odd_sizes': odd}
    half = []
    for k in sorted(c):
        half += [k] * (c[k] // 2)
    mid = odd[:1]
    return {'possible': True, 'arrangement': half + mid + half[::-1], 'odd_sizes': odd}
