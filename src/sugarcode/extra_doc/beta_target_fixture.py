"""Row 1345, Beta Management.

beta_target_fixture contrasts abstract current x and candidate y deviations
from target. Returns sorted deviation triples, closer labels whose candidate
absolute distance is smaller, exact candidate-target labels and same_distance.
No actual beta, market risk, hedge, target suitability or action/advice is assessed.
Inputs: rows is an exact list or tuple of 1 to 8 entries. Each entry is an
exact list or tuple (label, x, y). label is an exact printable ASCII str
of 1 to 12 characters, unique across rows. x and y are exact ints from
0 to 10; bool and all subclasses are refused.
target defaults to 5, an exact int from 0 to 10.
Validation order: rows type, rows size, target, then each row in input
order (shape, label, x, y), then duplicate labels.
NOT_CLAIMED: actual beta estimation, risk management, hedge execution, investment advice, production readiness.
"""

SCOPE = 'PARTIAL: inventories supplied abstract beta-count target deviations, no beta management'
NOT_CLAIMED = ('actual beta estimation', 'risk management', 'hedge execution', 'investment advice', 'production readiness')


def _label(x):
    return type(x) is str and x.isascii() and x.isprintable() and 1 <= len(x) <= 12


def beta_target_fixture(rows, target=5):
    if type(rows) not in (list, tuple):
        raise TypeError('rows must be a list or tuple')
    if not 1 <= len(rows) <= 8:
        raise ValueError('rows must contain 1 to 8 entries')
    if type(target) is not int or not 0 <= target <= 10:
        raise ValueError('target must be a nonbool integer between 0 and 10')
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
    deviations=[(n,x-target,y-target) for n,x,y in sorted(clean,key=lambda r:r[0])]
    return {'deviations':deviations,'closer':sorted(n for n,x,y in clean if abs(y-target)<abs(x-target)),
            'exact':sorted(n for n,x,y in clean if y==target),'same_distance':sorted(n for n,x,y in clean if abs(x-target)==abs(y-target))}
