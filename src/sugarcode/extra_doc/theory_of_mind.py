"""Row 762, Theory of Mind: pooling supplied beliefs by holder.

Models others' beliefs by collecting. Each row pairs a holder name of
1 to 8 characters with a claim of 1 to 20 characters. Reported: the
distinct (holder, claim) beliefs in first-seen order, how many
holders appear, the claims held by at least two distinct holders
sorted alphabetically, and the total row count. Caps (checked before
any work): 0 to 50 rows.
NOT_CLAIMED: real minds, false-belief tasks, cognitive science,
developmental psychology, inference, deception, production readiness.
"""
SCOPE = "PARTIAL: belief pooling over supplied rows, no real theory of mind"
NOT_CLAIMED = ('real minds', 'false-belief tasks', 'cognitive science',
               'developmental psychology', 'inference', 'deception',
               'production readiness')

MAX_ROWS = 50
MAX_HOLDER = 8
MAX_CLAIM = 20


def infer(beliefs):
    if type(beliefs) not in (list, tuple):
        raise TypeError('beliefs must be a list or tuple')
    if len(beliefs) > MAX_ROWS:
        raise ValueError('beliefs must contain at most 50 rows')
    rows = []
    for row in beliefs:
        if type(row) not in (list, tuple) or len(row) != 2:
            raise ValueError('each belief must be a (holder, claim) row')
        holder, claim = row
        if type(holder) is not str or not 1 <= len(holder) <= MAX_HOLDER:
            raise ValueError('holder must be a string of 1 to 8 characters')
        if type(claim) is not str or not 1 <= len(claim) <= MAX_CLAIM:
            raise ValueError('claim must be a string of 1 to 20 characters')
        rows.append((holder, claim))
    seen = set()
    unique = []
    holders = set()
    by_claim = {}
    for holder, claim in rows:
        if (holder, claim) not in seen:
            seen.add((holder, claim))
            unique.append((holder, claim))
        holders.add(holder)
        by_claim.setdefault(claim, set()).add(holder)
    shared = sorted(claim for claim, whos in by_claim.items() if len(whos) >= 2)
    return {'beliefs': unique, 'holders': len(holders),
            'shared': shared, 'total': len(rows)}
