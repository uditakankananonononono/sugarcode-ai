"""Row 583 Error Correction: exact Hamming(7,4) encode and single-bit correction on caller bit lists.

encode(data): 4 data bits (each int 0 or 1, never bool) give a 7-bit codeword with parity bits at
positions 1, 2 and 4 (1-indexed) and data bits at positions 3, 5, 6 and 7, each parity bit making the
even parity of the positions whose index has that bit set. decode(word): a 7-bit word (ints 0 or 1)
gives the syndrome (the 1-indexed position of a single flipped bit, 0 for none), the corrected word
and the 4 data bits read from it. A word with two or more flipped bits is miscorrected by this code and
is not detected; that is a property of the code, stated here and not hidden. Nothing is transmitted
or measured here.
NOT_CLAIMED: that real channels flip single bits, that this code suits any real link, detection of
double errors, burst-error handling, throughput or overhead beyond the fixed 4-to-7 ratio, any other
code, approval-gate clearance, deployment.
"""
NOT_CLAIMED = ('real channels flip single bits', 'this code suits any real link', 'detection of double errors',
               'burst-error handling', 'throughput or overhead beyond the fixed 4-to-7 ratio',
               'any other code', 'approval-gate clearance', 'deployment')


def _bits(v, n, label):
    if type(v) not in (list, tuple):
        raise TypeError(label + ' must be a list or tuple')
    if len(v) != n:
        raise ValueError('%s must hold exactly %d bits' % (label, n))
    for b in v:
        if type(b) is not int:
            raise TypeError(label + ' bits must be nonbool int')
        if b not in (0, 1):
            raise ValueError(label + ' bits must be 0 or 1')


def encode(data):
    _bits(data, 4, 'data')
    w = {3: data[0], 5: data[1], 6: data[2], 7: data[3]}
    for p in (1, 2, 4):
        w[p] = sum(b for i, b in w.items() if i & p) % 2
    return {'codeword': tuple(w[i] for i in sorted(w)), 'code_validated': False, 'not_claimed': NOT_CLAIMED}


def decode(word):
    _bits(word, 7, 'word')
    w = dict(enumerate(word, 1))
    syn = 0
    for p in (1, 2, 4):
        if sum(b for i, b in w.items() if i & p) % 2:
            syn += p
    if syn:
        w[syn] ^= 1
    return {'syndrome': syn, 'corrected': tuple(w[i] for i in sorted(w)), 'data': (w[3], w[5], w[6], w[7]),
            'code_validated': False, 'not_claimed': NOT_CLAIMED}
