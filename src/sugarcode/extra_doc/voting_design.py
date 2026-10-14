"""Row 745, Voting Design: aggregating preferences with Borda points.

Aggregates preferences by scoring. Each ballot lists 1 to 6 distinct
candidates, each a name of 1 to 8 characters, in preference order; a
candidate earns (ballot length - 1 - position) points per ballot.
Reported: (candidate, points) pairs sorted by points descending with
names breaking ties, the winner (the first pair's candidate, None when
there are no ballots), and the ballot count. Caps (checked before any
work): 0 to 50 ballots.
NOT_CLAIMED: real elections, strategy, fairness proofs, other voting
rules, voter registration, cryptography, production readiness.
"""
SCOPE = 'PARTIAL: Borda tally over supplied ballots, no real election'
NOT_CLAIMED = ('real elections', 'strategy', 'fairness proofs', 'other voting rules',
               'voter registration', 'cryptography', 'production readiness')

MAX_BALLOTS = 50
MAX_CANDIDATES = 6
MAX_NAME = 8


def tally(ballots):
    if type(ballots) not in (list, tuple):
        raise TypeError('ballots must be a list or tuple')
    if len(ballots) > MAX_BALLOTS:
        raise ValueError('ballots must contain at most 50 rows')
    rows = []
    for ballot in ballots:
        if type(ballot) not in (list, tuple) or not 1 <= len(ballot) <= MAX_CANDIDATES:
            raise ValueError('each ballot must list 1 to 6 candidates')
        for candidate in ballot:
            if type(candidate) is not str or not 1 <= len(candidate) <= MAX_NAME:
                raise ValueError('candidates must be names of 1 to 8 characters')
        if len(set(ballot)) != len(ballot):
            raise ValueError('a ballot may not repeat a candidate')
        rows.append(list(ballot))
    points = {}
    for ballot in rows:
        for position, candidate in enumerate(ballot):
            points[candidate] = points.get(candidate, 0) + len(ballot) - 1 - position
    ranked = sorted(points.items(), key=lambda kv: (-kv[1], kv[0]))
    return {'points': ranked, 'winner': ranked[0][0] if ranked else None,
            'ballots': len(rows)}
