"""Row 1419, Curriculum Design.

curriculum_sequence_fixture orders supplied abstract units by level x
ascending, ties label ascending. Duration y is a count, with transition count
between units, including zero-duration units. Returns sequence
(label,level,start,end), total duration including transitions, instruction
sum and unique sorted levels. No pedagogical curriculum design, learning
outcome validation, prerequisite inference or accreditation is supplied.
Inputs: rows is an exact list or tuple of 1 to 8 entries. Each entry is an
exact list or tuple (label, x, y). label is an exact printable ASCII str
of 1 to 12 characters, unique across rows. x and y are exact ints from
0 to 10; bool and all subclasses are refused.
transition defaults to 1, an exact int from 0 to 5.
Validation order: rows type, rows size, transition, then each row in input
order (shape, label, x, y), then duplicate labels.
NOT_CLAIMED: pedagogical curriculum design, learning outcome validation, prerequisite inference, production readiness.
"""

SCOPE = 'PARTIAL: orders supplied unit-level/duration counts into an abstract sequence, no pedagogical curriculum design'
NOT_CLAIMED = ('pedagogical curriculum design', 'learning outcome validation', 'prerequisite inference', 'production readiness')


def _label(x):
    return type(x) is str and x.isascii() and x.isprintable() and 1 <= len(x) <= 12


def curriculum_sequence_fixture(rows, transition=1):
    if type(rows) not in (list, tuple):
        raise TypeError('rows must be a list or tuple')
    if not 1 <= len(rows) <= 8:
        raise ValueError('rows must contain 1 to 8 entries')
    if type(transition) is not int or not 0 <= transition <= 5:
        raise ValueError('transition must be a nonbool integer between 0 and 5')
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
    ordered=sorted(clean,key=lambda r:(r[1],r[0])); clock=0; sequence=[]
    for i,(n,level,duration) in enumerate(ordered):
        if i: clock+=transition
        start=clock; clock+=duration; sequence.append((n,level,start,clock))
    return {'sequence':sequence,'duration':clock,'instruction':sum(y for n,x,y in clean),
            'levels':sorted({x for n,x,y in clean})}
