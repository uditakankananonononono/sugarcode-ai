"""Row 1408, Herding.

herding_majority_fixture finds larger supplied first x or second y choice
count, or tie, and labels positive-total rows concentrated when majority
share meets percent. Returns sorted majorities, concentrated, ties and
observations total. Zero totals are ties, not concentrated. No herding
inference, social influence model, causal claim or advice is supplied.
Inputs: rows is an exact list or tuple of 1 to 8 entries. Each entry is an
exact list or tuple (label, x, y). label is an exact printable ASCII str
of 1 to 12 characters, unique across rows. x and y are exact ints from
0 to 10; bool and all subclasses are refused.
percent defaults to 60, an exact int from 50 to 100.
Validation order: rows type, rows size, percent, then each row in input
order (shape, label, x, y), then duplicate labels.
NOT_CLAIMED: herding inference, social influence model, behavioral prediction, financial advice, production readiness.
"""

SCOPE = 'PARTIAL: supplied paired choice-count majority shares, no herding inference'
NOT_CLAIMED = ('herding inference', 'social influence model', 'behavioral prediction', 'financial advice', 'production readiness')


def _label(x):
    return type(x) is str and x.isascii() and x.isprintable() and 1 <= len(x) <= 12


def herding_majority_fixture(rows, percent=60):
    if type(rows) not in (list, tuple):
        raise TypeError('rows must be a list or tuple')
    if not 1 <= len(rows) <= 8:
        raise ValueError('rows must contain 1 to 8 entries')
    if type(percent) is not int or not 50 <= percent <= 100:
        raise ValueError('percent must be a nonbool integer between 50 and 100')
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
    values=sorted((n,'first' if x>y else 'second' if y>x else 'tie') for n,x,y in clean)
    return {'majorities':values,'concentrated':sorted(n for n,x,y in clean if x+y>0 and 100*max(x,y)>=percent*(x+y)),
            'ties':[n for n,c in values if c=='tie'],'observations':sum(x+y for n,x,y in clean)}
