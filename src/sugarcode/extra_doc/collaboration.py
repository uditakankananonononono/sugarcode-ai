"""Row 769, Collaboration: crediting supplied pieces to contributors.

Creates jointly by crediting. Each row pairs a piece name with a
contributor name, both strings of 1 to 8 characters. Reported: the
(piece, sorted contributors) pairs sorted by piece, how many pieces
have exactly one contributor, how many have at least two, and the
row total. Caps (checked before any work): 0 to 100 rows.
NOT_CLAIMED: real co-creation, authorship disputes, version control,
creative work, attribution policy, editing, production readiness.
"""
SCOPE = 'PARTIAL: piece crediting over supplied rows, no real collaboration'
NOT_CLAIMED = ('real co-creation', 'authorship disputes', 'version control',
               'creative work', 'attribution policy', 'editing',
               'production readiness')

MAX_ROWS = 100
MAX_NAME = 8


def credit(rows_in):
    if type(rows_in) not in (list, tuple):
        raise TypeError('credits must be a list or tuple')
    if len(rows_in) > MAX_ROWS:
        raise ValueError('credits must contain at most 100 rows')
    rows = []
    for row in rows_in:
        if type(row) not in (list, tuple) or len(row) != 2:
            raise ValueError('each credit must be a (piece, contributor) row')
        piece, contributor = row
        if type(piece) is not str or not 1 <= len(piece) <= MAX_NAME:
            raise ValueError('piece must be a string of 1 to 8 characters')
        if type(contributor) is not str or not 1 <= len(contributor) <= MAX_NAME:
            raise ValueError('contributor must be a string of 1 to 8 characters')
        rows.append((piece, contributor))
    by_piece = {}
    for piece, contributor in rows:
        by_piece.setdefault(piece, set()).add(contributor)
    pieces = sorted((piece, sorted(who)) for piece, who in by_piece.items())
    solo = sum(1 for piece, who in pieces if len(who) == 1)
    joint = sum(1 for piece, who in pieces if len(who) >= 2)
    return {'pieces': pieces, 'solo': solo, 'joint': joint, 'total': len(rows)}
