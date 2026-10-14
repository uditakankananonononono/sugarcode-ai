"""Row 830, Peer Assessment - Evaluates others: tally of supplied peer ratings.

peer_assessment takes ratings, a list or tuple of 0 to max_ratings (rater,
ratee, score) triples, and max_ratings, a nonbool int from 1 to 20 (default
8). Rater and ratee are strings of 1 to 12 characters. score is a nonbool int
from 1 to 5. A person may not rate themself, and each (rater, ratee) pair may
appear once.
Returns ratees (one (name, count, total, mean_tenths) tuple per rated person,
sorted by name, where mean_tenths is total * 10 divided by count rounded down)
and raters (the number of distinct raters).
Checks, in this order: max_ratings, ratings type, ratings size, each triple
(shape, rater, ratee, score, self-rating), repeated pair.
NOT_CLAIMED: fairness of the raters, real performance, rater honesty,
bias correction, production readiness.
"""
SCOPE = 'PARTIAL: per-person tally of supplied peer rating triples, no person is evaluated'
NOT_CLAIMED = ('fairness of the raters', 'real performance', 'rater honesty',
               'bias correction', 'production readiness')


def peer_assessment(ratings, max_ratings=8):
    if type(max_ratings) is not int or not 1 <= max_ratings <= 20:
        raise ValueError('max_ratings must be a nonbool integer between 1 and 20')
    if type(ratings) not in (list, tuple):
        raise TypeError('ratings must be a list or tuple')
    if len(ratings) > max_ratings:
        raise ValueError('ratings must contain at most max_ratings entries')
    seen = set()
    tally = {}
    raters = set()
    for r in ratings:
        if type(r) not in (list, tuple) or len(r) != 3:
            raise ValueError('each rating must be a (rater, ratee, score) triple')
        rater, ratee, score = r
        if type(rater) is not str or not 1 <= len(rater) <= 12:
            raise ValueError('each rater must be a string of 1 to 12 characters')
        if type(ratee) is not str or not 1 <= len(ratee) <= 12:
            raise ValueError('each ratee must be a string of 1 to 12 characters')
        if type(score) is not int or not 1 <= score <= 5:
            raise ValueError('score must be a nonbool integer between 1 and 5')
        if rater == ratee:
            raise ValueError('a person may not rate themself')
        if (rater, ratee) in seen:
            raise ValueError('each rater may rate a person once')
        seen.add((rater, ratee))
        raters.add(rater)
        c, t = tally.get(ratee, (0, 0))
        tally[ratee] = (c + 1, t + score)
    out = [(n, c, t, t * 10 // c) for n, (c, t) in sorted(tally.items())]
    return {'ratees': out, 'raters': len(raters)}
