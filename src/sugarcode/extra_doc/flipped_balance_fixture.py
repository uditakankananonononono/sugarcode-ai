"""Row 1450, Flipped Classroom.

flipped_balance_fixture compares supplied preparation count x with
preparation_per_class times in-class activity count y. Returns sorted
preparation_margins, ready nonnegative labels, missing total deficits and
class_count total. Readiness is count bookkeeping only, not actual learner
preparedness, flipped-classroom pedagogy, content generation or advice.
Inputs: rows is an exact list or tuple of 1 to 8 entries. Each entry is an
exact list or tuple (label, x, y). label is an exact printable ASCII str
of 1 to 12 characters, unique across rows. x and y are exact ints from
0 to 10; bool and all subclasses are refused.
preparation_per_class defaults to 2, an exact int from 1 to 5.
Validation order: rows type, rows size, preparation_per_class, then each row in input
order (shape, label, x, y), then duplicate labels.
NOT_CLAIMED: flipped classroom pedagogy, content generation, learner preparedness, production readiness.
"""

SCOPE = 'PARTIAL: supplied preparation/in-class count balance, no flipped-classroom pedagogy'
NOT_CLAIMED = ('flipped classroom pedagogy', 'content generation', 'learner preparedness', 'production readiness')


def _label(x):
    return type(x) is str and x.isascii() and x.isprintable() and 1 <= len(x) <= 12


def flipped_balance_fixture(rows, preparation_per_class=2):
    if type(rows) not in (list, tuple):
        raise TypeError('rows must be a list or tuple')
    if not 1 <= len(rows) <= 8:
        raise ValueError('rows must contain 1 to 8 entries')
    if type(preparation_per_class) is not int or not 1 <= preparation_per_class <= 5:
        raise ValueError('preparation_per_class must be a nonbool integer between 1 and 5')
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
    values=sorted((n,x-preparation_per_class*y) for n,x,y in clean)
    return {'preparation_margins':values,'ready':[n for n,v in values if v>=0],
            'missing':sum(max(-v,0) for n,v in values),'class_count':sum(y for n,x,y in clean)}
