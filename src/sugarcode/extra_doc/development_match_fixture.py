"""Row 1395, Development Finance.

development_match_fixture caps matching support at supplied project
count x and match times supplied grant count y. Returns sorted funding
(label,matched,gap), fully_matched zero-gap labels including zero project,
total_matched and total_gap. No actual grant award, development-finance
appraisal, project impact prediction or financial advice is supplied.
Inputs: rows is an exact list or tuple of 1 to 8 entries. Each entry is an
exact list or tuple (label, x, y). label is an exact printable ASCII str
of 1 to 12 characters, unique across rows. x and y are exact ints from
0 to 10; bool and all subclasses are refused.
match defaults to 2, an exact int from 1 to 5.
Validation order: rows type, rows size, match, then each row in input
order (shape, label, x, y), then duplicate labels.
NOT_CLAIMED: development finance appraisal, grant award, project impact prediction, financial advice, production readiness.
"""

SCOPE = 'PARTIAL: supplied project/grant count matching, no development-finance appraisal'
NOT_CLAIMED = ('development finance appraisal', 'grant award', 'project impact prediction', 'financial advice', 'production readiness')


def _label(x):
    return type(x) is str and x.isascii() and x.isprintable() and 1 <= len(x) <= 12


def development_match_fixture(rows, match=2):
    if type(rows) not in (list, tuple):
        raise TypeError('rows must be a list or tuple')
    if not 1 <= len(rows) <= 8:
        raise ValueError('rows must contain 1 to 8 entries')
    if type(match) is not int or not 1 <= match <= 5:
        raise ValueError('match must be a nonbool integer between 1 and 5')
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
    values=sorted((n,min(x,match*y),max(x-match*y,0)) for n,x,y in clean)
    return {'funding':values,'fully_matched':[n for n,f,g in values if g==0],
            'total_matched':sum(f for n,f,g in values),'total_gap':sum(g for n,f,g in values)}
