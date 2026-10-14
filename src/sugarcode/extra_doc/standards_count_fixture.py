"""Row 1489, Standards-Based Grading.

standards_count_fixture compares supplied achieved y to target x:
advanced strictly above x plus advanced_gap, meeting at least x otherwise,
below when y is less. Returns sorted bands, meeting_or_above, below and
advanced lists. No actual standards-based grading policy, standard validity,
learner evaluation, mastery inference or educational recommendation.
Inputs: rows is an exact list or tuple of 1 to 8 entries. Each entry is an
exact list or tuple (label, x, y). label is an exact printable ASCII str
of 1 to 12 characters, unique across rows. x and y are exact ints from
0 to 10; bool and all subclasses are refused.
advanced_gap defaults to 2, an exact int from 0 to 10.
Validation order: rows type, rows size, advanced_gap, then each row in input
order (shape, label, x, y), then duplicate labels.
NOT_CLAIMED: grading policy, standard validity, learner evaluation, production readiness.
"""

SCOPE = 'PARTIAL: supplied target/achieved count standards bands, no grading policy'
NOT_CLAIMED = ('grading policy', 'standard validity', 'learner evaluation', 'production readiness')


def _label(x):
    return type(x) is str and x.isascii() and x.isprintable() and 1 <= len(x) <= 12


def standards_count_fixture(rows, advanced_gap=2):
    if type(rows) not in (list, tuple):
        raise TypeError('rows must be a list or tuple')
    if not 1 <= len(rows) <= 8:
        raise ValueError('rows must contain 1 to 8 entries')
    if type(advanced_gap) is not int or not 0 <= advanced_gap <= 10:
        raise ValueError('advanced_gap must be a nonbool integer between 0 and 10')
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
    values=sorted((n,'advanced' if y>x+advanced_gap else 'meeting' if y>=x else 'below') for n,x,y in clean)
    return {'bands':values,'meeting_or_above':[n for n,b in values if b!='below'],
            'below':[n for n,b in values if b=='below'],'advanced':[n for n,b in values if b=='advanced']}
