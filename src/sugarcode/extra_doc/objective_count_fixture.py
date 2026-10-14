"""Row 1420, Learning Objective Writing.

objective_count_fixture formats supplied label and abstract attempt count
x into a fixed objective string, requiring the ceiling of percent times x
in hundredths successes. Supplied success count y meets inclusive target.
Returns sorted objectives (label,text), met labels and percent. Zero attempts
requires zero successes. No pedagogical objective writing, Bloom taxonomy
validation, learning measurement or educational recommendation is supplied.
Inputs: rows is an exact list or tuple of 1 to 8 entries. Each entry is an
exact list or tuple (label, x, y). label is an exact printable ASCII str
of 1 to 12 characters, unique across rows. x and y are exact ints from
0 to 10; bool and all subclasses are refused.
percent defaults to 80, an exact int from 0 to 100.
Validation order: rows type, rows size, percent, then each row in input
order (shape, label, x, y), then duplicate labels.
NOT_CLAIMED: pedagogical objective writing, Bloom taxonomy validation, learning measurement, production readiness.
"""

SCOPE = 'PARTIAL: formats supplied objective attempt/success count targets, no pedagogical objective writing'
NOT_CLAIMED = ('pedagogical objective writing', 'Bloom taxonomy validation', 'learning measurement', 'production readiness')


def _label(x):
    return type(x) is str and x.isascii() and x.isprintable() and 1 <= len(x) <= 12


def objective_count_fixture(rows, percent=80):
    if type(rows) not in (list, tuple):
        raise TypeError('rows must be a list or tuple')
    if not 1 <= len(rows) <= 8:
        raise ValueError('rows must contain 1 to 8 entries')
    if type(percent) is not int or not 0 <= percent <= 100:
        raise ValueError('percent must be a nonbool integer between 0 and 100')
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
    values=sorted((n,f'{n}: demonstrate {x} attempts with at least {(percent*x+99)//100} successes',y>=(percent*x+99)//100) for n,x,y in clean)
    return {'objectives':[(n,text) for n,text,met in values],'met':[n for n,text,met in values if met],
            'percent':percent}
