"""Row 766, Altruism: keeping a ledger of supplied helping acts.

Helps without reward by recording. Each row pairs a giver with a
receiver, both strings of 1 to 8 characters, and the two must
differ. Reported: the act count, how many distinct givers appear,
and the most generous giver (the one with the most acts, ties broken
alphabetically, None when there are no acts). Caps (checked before
any work): 0 to 100 rows.
NOT_CLAIMED: real generosity, charity, motivation, ethics,
philosophy, donations, production readiness.
"""
SCOPE = 'PARTIAL: act ledger over supplied rows, no real altruism'
NOT_CLAIMED = ('real generosity', 'charity', 'motivation', 'ethics',
               'philosophy', 'donations', 'production readiness')

MAX_ROWS = 100
MAX_NAME = 8


def ledger(acts):
    if type(acts) not in (list, tuple):
        raise TypeError('acts must be a list or tuple')
    if len(acts) > MAX_ROWS:
        raise ValueError('acts must contain at most 100 rows')
    rows = []
    for row in acts:
        if type(row) not in (list, tuple) or len(row) != 2:
            raise ValueError('each act must be a (giver, receiver) row')
        giver, receiver = row
        if type(giver) is not str or not 1 <= len(giver) <= MAX_NAME:
            raise ValueError('giver must be a string of 1 to 8 characters')
        if type(receiver) is not str or not 1 <= len(receiver) <= MAX_NAME:
            raise ValueError('receiver must be a string of 1 to 8 characters')
        if giver == receiver:
            raise ValueError('giver and receiver must differ')
        rows.append((giver, receiver))
    counts = {}
    for giver, receiver in rows:
        counts[giver] = counts.get(giver, 0) + 1
    most = None
    if counts:
        most = min(counts, key=lambda giver: (-counts[giver], giver))
    return {'acts': len(rows), 'givers': len(counts), 'most_generous': most}
