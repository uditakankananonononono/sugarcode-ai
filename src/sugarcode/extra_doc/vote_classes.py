"""Row 1106, Voting Classifiers - Majority vote.

vote_classes maps each pair x,y to two class indices by modulo classes,
counts all ballots, and chooses smallest-index class among maximum counts.
Returns ballots as (label,class_x,class_y) sorted by label, votes as count
list in class-index order including zero-vote classes, winner as integer
class index, tied as all maximum-count class indices ascending. This is
supplied-vote aggregation only, not classifier learning.
Inputs: rows is an exact list or tuple of 1 to 8 entries. Each entry is an
exact list or tuple (label, x, y). label is an exact printable ASCII str
of 1 to 12 characters, unique across rows. x and y are exact ints from
0 to 10; bool and all subclasses are refused.
classes defaults to 3, an exact int from 2 to 5.
Validation order: rows type, rows size, classes, then each row in input
order (shape, label, x, y), then duplicate labels.
NOT_CLAIMED: classifier training, generalization, independent votes, class validity, production readiness.
"""

SCOPE = 'PARTIAL: aggregates supplied multiclass vote counts encoded by two class labels, no classifiers are trained'
NOT_CLAIMED = ('classifier training', 'generalization', 'independent votes', 'class validity', 'production readiness')


def _label(x):
    return type(x) is str and x.isascii() and x.isprintable() and 1 <= len(x) <= 12


def vote_classes(rows, classes=3):
    if type(rows) not in (list, tuple):
        raise TypeError('rows must be a list or tuple')
    if not 1 <= len(rows) <= 8:
        raise ValueError('rows must contain 1 to 8 entries')
    if type(classes) is not int or not 2 <= classes <= 5:
        raise ValueError('classes must be a nonbool integer between 2 and 5')
    clean = []
    for row in rows:
        if type(row) not in (list, tuple) or len(row) != 3:
            raise ValueError('each row must be a (label, x, y) triple')
        label, x, y = row
        if not _label(label):
            raise ValueError('label must be a printable ASCII string of 1 to 12 characters')
        if type(x) is not int or not 0 <= x <= 10:
            raise ValueError('x must be a nonbool integer between 0 and 10')
        if type(y) is not int or not 0 <= y <= 10:
            raise ValueError('y must be a nonbool integer between 0 and 10')
        clean.append((label, x, y))
    if len({r[0] for r in clean}) != len(clean):
        raise ValueError('labels must be distinct')
    votes = [0] * classes
    ballots = []
    for n, x, y in sorted(clean, key=lambda r: r[0]):
        a, b = x % classes, y % classes
        votes[a] += 1
        votes[b] += 1
        ballots.append((n, a, b))
    maximum = max(votes)
    tied = [i for i, count in enumerate(votes) if count == maximum]
    return {'ballots': ballots, 'votes': votes, 'winner': tied[0], 'tied': tied}
