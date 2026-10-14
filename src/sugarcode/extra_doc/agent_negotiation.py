"""Row 1942, Title: Agent Negotiation

count_counters(rows): rows are (offer, party, bid)
triples; offer and party strings of 1 to 16
characters; bid a nonbool integer between 1 and 9.
Caps (checked before any work): 1 to 60 rows.
Reported: the total row count, for each party its
counters (bids landing strictly between the party's
own previous bid and the previous row's bid, counted
once the party has bid before), the total counters,
and the leading negotiator (the most counters, first
supplied on ties, or None when no party counters).

SCOPE: PARTIAL: counter counting over supplied bids
NOT_CLAIMED: strategy modeling, preference elicitation,
game theory, protocol design, production readiness.
"""

SCOPE = 'PARTIAL: counter counting over supplied bids'
NOT_CLAIMED = ('strategy modeling', 'preference elicitation',
               'game theory', 'protocol design',
               'production readiness')


def count_counters(rows):
    if type(rows) not in (list, tuple):
        raise TypeError('rows must be a list or tuple')
    if not 1 <= len(rows) <= 60:
        raise ValueError('rows must contain between 1 and 60 entries')
    for i, row in enumerate(rows, 1):
        if type(row) not in (list, tuple):
            raise TypeError(f'row {i}: expected an (offer, party, bid) triple')
        if len(row) != 3:
            raise ValueError(f'row {i}: expected 3 fields, got {len(row)}')
        offer, party, bid = row
        if type(offer) is not str or not 1 <= len(offer) <= 16:
            raise ValueError(f'row {i}: offer must be a string of 1 to 16 characters')
        if type(party) is not str or not 1 <= len(party) <= 16:
            raise ValueError(f'row {i}: party must be a string of 1 to 16 characters')
        if type(bid) is not int or not 1 <= bid <= 9:
            raise ValueError(f'row {i}: bid must be a nonbool integer between 1 and 9')
    own = {}
    order = {}
    counters = {}
    turns = 0
    previous = None
    for offer, party, bid in rows:
        if party not in order:
            order[party] = True
        if previous is not None and party in own:
            low = min(previous, own[party])
            high = max(previous, own[party])
            if low < bid < high:
                if party not in counters:
                    counters[party] = 0
                counters[party] += 1
                turns += 1
        own[party] = bid
        previous = bid
    leader = None
    for party in order:
        if party not in counters:
            continue
        if leader is None or counters[party] > counters[leader]:
            leader = party
    return {'total': len(rows),
            'counters': counters,
            'turns': turns,
            'leader': leader}
