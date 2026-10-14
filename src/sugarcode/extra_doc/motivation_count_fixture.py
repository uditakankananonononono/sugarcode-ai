"""Row 1503, Motivational Tutoring.

motivation_count_fixture chooses recognize when supplied completion y
meets minimum, otherwise encourage at positive attempt x, else no_record.
Returns sorted triggers and recognize/encourage/no_record lists. Completion
takes priority independently of attempts by fixture convention. No real
motivational tutoring, motivation inference, psychological diagnosis,
message sending or educational recommendation is supplied.
Inputs: rows is an exact list or tuple of 1 to 8 entries. Each entry is an
exact list or tuple (label, x, y). label is an exact printable ASCII str
of 1 to 12 characters, unique across rows. x and y are exact ints from
0 to 10; bool and all subclasses are refused.
minimum defaults to 3, an exact int from 0 to 10.
Validation order: rows type, rows size, minimum, then each row in input
order (shape, label, x, y), then duplicate labels.
NOT_CLAIMED: motivational tutoring, motivation inference, psychological diagnosis, production readiness.
"""

SCOPE = 'PARTIAL: supplied attempt/completion count encouragement triggers, no motivational tutoring'
NOT_CLAIMED = ('motivational tutoring', 'motivation inference', 'psychological diagnosis', 'production readiness')


def _label(x):
    return type(x) is str and x.isascii() and x.isprintable() and 1 <= len(x) <= 12


def motivation_count_fixture(rows, minimum=3):
    if type(rows) not in (list, tuple):
        raise TypeError('rows must be a list or tuple')
    if not 1 <= len(rows) <= 8:
        raise ValueError('rows must contain 1 to 8 entries')
    if type(minimum) is not int or not 0 <= minimum <= 10:
        raise ValueError('minimum must be a nonbool integer between 0 and 10')
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
    values=sorted((n,'recognize' if y>=minimum else 'encourage' if x>0 else 'no_record') for n,x,y in clean)
    return {'triggers':values,'recognize':[n for n,t in values if t=='recognize'],
            'encourage':[n for n,t in values if t=='encourage'],'no_record':[n for n,t in values if t=='no_record']}
